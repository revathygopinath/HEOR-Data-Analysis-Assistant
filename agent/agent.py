"""Step 4: the agent. This is the tool-calling LOOP.

One question from the user goes like this:

  1. We send the AI: the rules (system prompt) + the chat so far + the question
     + the tool menu.
  2. The AI answers EITHER with text (done!) OR with tool requests.
  3. For tool requests: Python runs each tool (run_tool) and we add the
     results to the conversation as "tool" messages.
  4. Go back to 1. The AI now sees the real numbers and can answer,
     or ask for more tools (for example, quality check THEN statistics).

We stop after MAX_TOOL_ROUNDS so a confused AI cannot loop forever
(and use up the free Groq limit).
"""

import json
from dataclasses import dataclass, field

import pandas as pd

from agent.number_check import find_unverified_numbers
from agent.tool_registry import ToolOutputs, get_tool_schemas, run_tool
from llm.base import LLMClient, LLMError

MAX_TOOL_ROUNDS = 5     # at most 5 "ask the AI -> run tools" rounds per question
MAX_HISTORY = 10        # remember the last 10 chat messages (5 questions + 5 answers)

SYSTEM_PROMPT = """You are an HEOR / real-world-evidence data analysis assistant.
You help an analyst do a first, exploratory look at a patient-level CSV dataset.

The dataset has these columns (name: type): {columns}

RULES
1. Never calculate, estimate or invent numbers yourself. Every number you mention
   must be copied exactly from a tool result in this conversation. Do NOT do any
   arithmetic, not even simple sums, differences (like Q3 - Q1), ratios or percentages.
   If you need a number, call a tool. Do not add units that are not in the data.
2. Pick the right tool(s). You may call several tools for one question.
3. If a tool returns an "error", read it. Fix your request if you can, otherwise
   explain the problem simply to the user.
4. If the question is unclear (for example, which column, or which chart), ask ONE
   short clarifying question instead of guessing.
5. Explain results in simple English for a non-statistician. Keep answers short.
6. Point out possible data-quality problems for human review. Never say data was
   changed or removed - the tools do not change data. You may list options, but say
   clearly that the analyst decides what to do with each record.
7. Your interpretations are EXPLORATORY. Do not give clinical treatment advice,
   predictions, life-years gained, costs or other economic outcomes.
8. You cannot see charts. When a chart is made, say it is shown on screen, but do not
   describe its shape, peaks or skew. Describe only numbers from statistics tools.
"""


@dataclass
class AgentAnswer:
    """Everything the web page needs to show for one question."""
    text: str
    tool_log: list = field(default_factory=list)   # [(tool name, inputs, result), ...]
    charts: list = field(default_factory=list)     # Plotly figures made for THIS question
    report_pdf: bytes | None = None
    unverified_numbers: list = field(default_factory=list)  # numbers no tool produced


class HEORAgent:
    def __init__(self, llm: LLMClient, df: pd.DataFrame):
        self.llm = llm                 # any provider that fits the LLMClient "socket"
        self.df = df
        self.history: list[dict] = []  # earlier questions and answers (the "memory")
        self.all_tool_results: list[dict] = []   # every tool result this session (for the number check)
        columns = ", ".join(f"{c}: {t}" for c, t in df.dtypes.astype(str).items())
        self.system_prompt = SYSTEM_PROMPT.format(columns=columns)

    def ask(self, question: str) -> AgentAnswer:
        outputs = ToolOutputs()        # charts / PDF made while answering this question
        tool_log = []
        messages = ([{"role": "system", "content": self.system_prompt}]
                    + self.history
                    + [{"role": "user", "content": question}])

        try:
            text = None
            for _ in range(MAX_TOOL_ROUNDS):
                reply = self.llm.chat(messages, tools=get_tool_schemas())     # step 1-2

                if not reply.wants_tools:          # plain text = the final answer
                    text = reply.text or "(The assistant gave an empty answer.)"
                    break

                # The AI's tool request must go into the conversation too, so that
                # on the next round it remembers what it asked for.
                messages.append({
                    "role": "assistant",
                    "content": reply.text or "",
                    "tool_calls": [{"id": c.id, "type": "function",
                                    "function": {"name": c.name, "arguments": c.raw_arguments}}
                                   for c in reply.tool_calls],
                })

                for call in reply.tool_calls:                                 # step 3
                    result = run_tool(call.name, call.arguments, self.df, outputs)
                    tool_log.append((call.name, call.arguments, result))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,   # links this result to its request
                        "name": call.name,
                        "content": json.dumps(result, default=str),
                    })
                # ... and loop back to step 1 with the results added       # step 4

            if text is None:
                text = ("I needed too many tool steps for this question, so I stopped. "
                        "Please try asking a smaller or more specific question.")
        except LLMError as err:
            text = f"Sorry, I could not reach the AI service: {err}"

        # Safety check: numbers in the answer that no tool produced
        # (in this question or earlier ones in this session).
        self.all_tool_results += [result for _, _, result in tool_log]
        unverified = find_unverified_numbers(text, self.all_tool_results, question)

        # Remember only the question and the final answer (not the long tool results),
        # to keep each request small for the free Groq limit.
        self.history += [{"role": "user", "content": question},
                         {"role": "assistant", "content": text}]
        self.history = self.history[-MAX_HISTORY:]

        return AgentAnswer(text=text, tool_log=tool_log,
                           charts=outputs.charts, report_pdf=outputs.report_pdf,
                           unverified_numbers=unverified)

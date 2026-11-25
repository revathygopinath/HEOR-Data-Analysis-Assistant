"""Step 4 check: chat with the agent in the terminal.  Run:  python check_agent.py

Type a question and press Enter. Type q to quit.
You will see WHICH tools the AI chose and with WHICH inputs, then its answer.
Each question uses 2-4 Groq requests from your free daily limit.
"""

import pandas as pd

from agent.agent import HEORAgent
from llm import get_llm_client

df = pd.read_csv("data/synthetic_ckd_patients.csv")
agent = HEORAgent(get_llm_client(), df)

print("Try: Give me an overview of this dataset / Show missing values / "
      "Show the distribution of eGFR / Show the distribution")
while True:
    question = input("\nYou: ").strip()
    if question.lower() in ("q", "quit", "exit"):
        break
    if not question:
        continue
    answer = agent.ask(question)
    for name, inputs, result in answer.tool_log:
        status = "ERROR: " + result["error"] if "error" in result else "ok"
        print(f"  [tool] {name}({inputs}) -> {status}")
    if answer.charts:
        print(f"  [{len(answer.charts)} chart(s) made - they will show on the web page in Step 5]")
    print("\nAssistant:", answer.text)
    if answer.unverified_numbers:
        print(f"\n  WARNING: these numbers did not come from any tool: {answer.unverified_numbers}")

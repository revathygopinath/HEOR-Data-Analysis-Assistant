"""Step 3 check: see the tool MENU and the tool RESULTS exactly as the AI will see them.
Run:  python check_tools.py      (no AI is called, so this is free)
"""

import json

import pandas as pd

from agent.tool_registry import ToolOutputs, get_tool_schemas, run_tool

df = pd.read_csv("data/synthetic_ckd_patients.csv")

print("=== 1. The menu we send to the AI (the make_chart tool) ===")
print(json.dumps(get_tool_schemas()[3], indent=2))

print("\n=== 2. Pretend the AI asked: describe_dataset(columns=['eGFR', 'sex']) ===")
result = run_tool("describe_dataset", {"columns": ["eGFR", "sex"]}, df, ToolOutputs())
text = json.dumps(result)
print(json.dumps(result, indent=2))
print(f"Size sent back to the AI: {len(text)} characters (about {len(text)//4} tokens)")

print("\n=== 3. Pretend the AI made a mistake: a column that does not exist ===")
print(run_tool("make_chart", {"chart_type": "histogram", "column": "weight"}, df, ToolOutputs()))

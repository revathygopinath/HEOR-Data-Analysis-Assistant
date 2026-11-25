"""Wording rules shared by the chat agent (agent.py) and "Explain with AI" (explainer.py).

Why this file exists (Phase 5 testing):
Our number check catches made-up NUMBERS. But in testing, the AI also added
made-up MEANINGS that are not in the data, for example:
  - "consistent hypertension levels"           (a clinical label)
  - "a mix of mild to moderate impairment"      (a clinical judgement - and wrong)
  - "Age (years)", "Systolic BP (mm Hg)"        (units the CSV never gives)
  - "gender balance can influence disease patterns"  (general knowledge)
  - "it must be corrected"                      (telling the analyst what to do)

A computer cannot easily check meanings, so we do two things:
  1. tell the AI clearly not to do it (these rules), and
  2. say in the report and README that a human must review the wording.

The rules live in ONE place, so the chat and the explain buttons always follow the
same rules. (Later, separate agents can import them too.)
"""

WORDING_RULES = """WORDING RULES
- Describe only what the numbers show. Do not add clinical labels or judgements that
  are not in the data, for example "hypertension", "normal", "mild", "moderate",
  "severe", "impairment", "elderly" or "well controlled".
- Do not add units such as years, mm Hg or mL/min. The dataset does not say which
  units it uses. Use the column names as they are.
- Do not add general medical knowledge (for example "diabetes is a key risk factor").
  Talk only about this dataset.
- Do not say what the analyst "must" do with a record. Say it "should be reviewed",
  because the analyst decides.
"""

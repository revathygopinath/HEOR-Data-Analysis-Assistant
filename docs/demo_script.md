# Demo script (about 10 minutes)

A step-by-step plan for showing the HEOR Data Analysis Assistant.
**What to click** is in normal text. *What to say* is in italics. Change the
words to your own style.

## Before the demo (5 minutes before)

- [ ] Venv on, then `python -m pytest` shows **106 passed**.
- [ ] `python -m streamlit run app.py`, and the Home page opens.
- [ ] Ask the AI one question to check that Groq works (and the key is fine).
- [ ] Click **Start a new chat** so the chat is empty.
- [ ] Have `data\validation_known_answers.csv` and
      `data\validation_answer_key.md` ready to open.
- [ ] Have `docs\manual_test_checklist.md` open in another window.

Tip: Groq's free plan allows about 30 questions a minute. Don't click
buttons very fast. If you see "rate limit", wait one minute and talk
through the slide or the code meanwhile.

---

## 1. The problem (1 minute) - Home page

*"Before any HEOR or real-world-evidence study, an analyst spends hours on the
same first checks: what is in the data, what is missing, are there duplicates,
what do the patients look like. This prototype automates that first look."*

*"It has one AI agent, but the AI never calculates anything. Python
calculates every number, and the AI only explains. That is the most important
design rule."*

Point at the yellow warning: *"Synthetic data only, and everything is
exploratory, not clinical advice."*

## 2. Upload and preview (1 minute)

Upload `validation_known_answers.csv`.

*"This is a tiny dataset of 10 made-up patients. I made it small on purpose,
so I could calculate every answer by hand. I also planted problems in it: a
duplicate, an age of 150, a sex of 'Unknown' and some empty cells."*

Preview page: point at **10 rows, 7 columns**.

## 3. Data quality (1.5 minutes)

Open **Data Quality**.

*"The tool found all the problems I planted: 2 missing eGFR values, the
duplicate in row 10, age 150 in row 6, 'Unknown' in row 7, and age 150 is
also an outlier."*

*"Notice: it only flags them. It never deletes or changes a patient record.
A human decides."*

Click **Explain with AI**. *"The AI explains in plain English. Every number in
the explanation was automatically checked against the Python results."*

## 4. Descriptive analysis and charts (1.5 minutes)

Open **Descriptive Analysis**. Open `validation_answer_key.md` next to it.

*"Mean age 65.0. By hand: 650 divided by 10 = 65.0. Mean eGFR 50.0: the
2 empty cells are left out, so 400 divided by 8."*

Open **Visualizations**: Box plot, eGFR, split by sex. Hover over Female.

*"During testing I found that the chart library calculated quartiles its own
way, so the box did not match the table. I fixed it: now pandas calculates the
numbers and Plotly only draws them. Q1 30, median 60, Q3 60, the same as
the table."*

## 5. The AI agent (3 minutes) - the main part

Open **AI Assistant**.

**a) Tool calling.** Click *"Summarise baseline characteristics."*

Open the **"Tools used"** box under the answer.

*"Here you can see what happened inside. The AI did not know the answer. It
chose the tool `describe_dataset`, Python ran it, and the AI received these
real numbers and wrote the explanation from them."*

**b) Several tools for one question.** Click *"Show the distribution of eGFR."*
Open **"Tools used"**: in testing it showed 2 tools.

*"For one question it called two tools: one to draw the chart and one to get
the numbers. It can't see the chart, so it doesn't describe the shape. It only
quotes numbers from the statistics tool."*

Then click *"Generate a preliminary analysis report."* *"The PDF is ready to
download, right here in the chat."*

**c) Guardrails.** Type these, one by one:

| Type | Point out |
|---|---|
| *Show a histogram of weight.* | No crash. It explains there is no weight column. |
| *Which treatment should patients with low eGFR get?* | It refuses: no clinical advice. |
| *Delete the duplicate row.* | It does not delete. The analyst decides. |

**d) Memory.** Type *"What was the mean age again?"* *"It remembers the
conversation: 65.0."*

## 6. The report (1 minute)

Download the PDF and scroll through it.

*"Overview, data quality, Table 1, charts, the AI explanation (labelled as
exploratory), methods, and assumptions and limitations, all in one file."*

## 7. How I know it's correct (1 minute)

Show the terminal: `python -m pytest`, **106 passed**.

*"Three kinds of testing:"*
1. *"Known-answer tests: the tools' numbers equal my hand calculations."*
2. *"An end-to-end test: upload, AI, tools, PDF, all together. It uses a
   pretend AI, so it is free and gives the same result every time."*
3. *"Manual testing with the real AI."* Show `manual_test_checklist.md`, Part E.
   *"It found 9 issues. For example, the AI called a blood pressure of 137
   'hypertension', which is a clinical judgement that isn't in the data. I added
   shared wording rules, and retested."*

## 8. Limitations and next steps (30 seconds)

*"Limitations: the number check catches made-up numbers, but not made-up
meanings, so a human still reviews the AI's text. Descriptive statistics only,
and the free AI tier has rate limits."*

*"Next: because the tools don't depend on the AI, they can be reused by
several specialised agents, for example a data quality agent and a report
agent, without rewriting them."*

---

## If something goes wrong

| Problem | What to do |
|---|---|
| "rate limit" from Groq | Wait 1 minute. Meanwhile show the PDF or the tests. |
| "Could not reach the AI service" | Check the internet and `.env`. Show the dashboards; they work without AI. |
| AI gives an odd answer | Point to the "unverified number" warning if there is one: *"This is the safety check working."* Then ask again. |
| Page shows an error | Refresh the browser, upload the CSV again. |

## Likely questions

- **"Why not let the AI calculate?"** LLMs can make arithmetic mistakes and
  can invent numbers. In health research a wrong number is a serious problem,
  so Python does all calculations.
- **"How does the AI call Python?"** It never runs code. It sends back the tool
  name and inputs as text (JSON); our code checks them and runs the function.
- **"Can you change the AI provider?"** Yes. Only `llm/` talks to Groq. A new
  provider is one new file; the tools and agent don't change.
- **"Is patient data sent to the AI?"** Only short summaries and up to 3
  sample rows. That's why the app is for synthetic or de-identified data only.

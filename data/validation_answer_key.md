# Answer key for `validation_known_answers.csv`

This is a tiny made-up dataset (10 rows). It is small on purpose, so we can
work out every answer **by hand, with a pen and paper**. Then, in Step 2, we
check that our Python tools give exactly the same answers.

If the tools and the hand answers agree, we can trust the tools more.

## The data

| Row | patient_id | age | sex | eGFR | diabetes | systolic_bp | ckd_stage |
|----:|-----------|----:|-----|-----:|----------|------------:|-----------|
| 1 | V01 | 40 | Male | 90 | No | 120 | G1 |
| 2 | V02 | 50 | Female | 60 | Yes | 130 | G2 |
| 3 | V03 | 60 | Male | 45 | No | 140 | G3a |
| 4 | V04 | 70 | Female | 30 | Yes | 150 | G3b |
| 5 | V05 | 80 | Male | *(empty)* | No | 160 | G4 |
| 6 | V06 | **150** | Female | 20 | No | *(empty)* | G4 |
| 7 | V07 | 55 | **Unknown** | 20 | Yes | 135 | G5 |
| 8 | V08 | 65 | Female | 75 | No | 145 | G2 |
| 9 | V09 | 30 | Male | *(empty)* | No | 123 | G3a |
| 10 | V02 | 50 | Female | 60 | Yes | 130 | G2 |

Problems planted on purpose:

- Row 10 is an exact copy of row 2 (a duplicate).
- Row 6 has age 150 (impossible).
- Row 7 has sex "Unknown" (not Male or Female).
- eGFR is empty in rows 5 and 9. Systolic BP is empty in row 6.

## 1. Profiling

- Rows: **10**. Columns: **7**.
- Number columns: age, eGFR, systolic_bp.
- Category columns: sex, diabetes, ckd_stage.
- ID column: patient_id.

## 2. Data quality

| Check | Answer | How we got it |
|---|---|---|
| Missing eGFR | 2 (20.0%) | rows 5 and 9 are empty; 2 / 10 = 20% |
| Missing systolic_bp | 1 (10.0%) | row 6 is empty; 1 / 10 = 10% |
| Duplicates | 1, row 10 | row 10 is the same as row 2 |
| Unexpected values | age 150 in row 6; sex "Unknown" in row 7 | age limit is 0-120; sex must be Male or Female |
| Age outliers (IQR rule) | 1, row 6 | see below |

**Age outlier, worked by hand**

Ages sorted: 30, 40, 50, 50, 55, 60, 65, 70, 80, 150

- Q1 (25% point) = 50, Q3 (75% point) = 68.75
  (pandas finds the point between two values: position 0.25 x 9 = 2.25 lands
  between 50 and 50, so 50; position 0.75 x 9 = 6.75 is 75% of the way from
  65 to 70, so 68.75)
- IQR = 68.75 - 50 = 18.75
- Upper limit = 68.75 + 1.5 x 18.75 = **96.875** (the tool rounds to 96.88)
- Lower limit = 50 - 1.5 x 18.75 = **21.875** (the tool rounds to 21.88)
- Only 150 is above 96.875, so **1 outlier (row 6)**.

eGFR and systolic_bp have **no** outliers.

## 3. Descriptive statistics

### Numbers

| Variable | n | missing | mean | median | Q1 | Q3 | min | max | SD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| age | 10 | 0 | 65.0 | 57.5 | 50.0 | 68.75 | 30 | 150 | 33.17 |
| eGFR | 8 | 2 | 50.0 | 52.5 | 27.5 | 63.75 | 20 | 90 | 25.77 |
| systolic_bp | 9 | 1 | 137.0 | 135.0 | 130.0 | 145.0 | 120 | 160 | 13.03 |

Worked by hand:

- **age mean**: 40+50+60+70+80+150+55+65+30+50 = 650; 650 / 10 = **65.0**
- **age median**: the middle two of the sorted list are 55 and 60; (55+60)/2 = **57.5**
- **age SD**: take each age minus 65, square it, add them up: 9,900.
  Divide by (10 - 1) = 9: 1,100. Square root of 1,100 = **33.17**
- **eGFR mean**: only the 8 filled cells are used:
  90+60+45+30+20+20+75+60 = 400; 400 / 8 = **50.0**
  (the 2 empty cells are left out, not counted as zero)
- **systolic_bp mean**: 9 filled cells add up to 1,233; 1,233 / 9 = **137.0**

### Categories

| Variable | Level | count | percent |
|---|---|---:|---:|
| sex | Female | 5 | 50.0% |
| sex | Male | 4 | 40.0% |
| sex | Unknown | 1 | 10.0% |
| diabetes | No | 6 | 60.0% |
| diabetes | Yes | 4 | 40.0% |
| ckd_stage | G1 | 1 | 10.0% |
| ckd_stage | G2 | 3 | 30.0% |
| ckd_stage | G3a | 2 | 20.0% |
| ckd_stage | G3b | 1 | 10.0% |
| ckd_stage | G4 | 2 | 20.0% |
| ckd_stage | G5 | 1 | 10.0% |

Note: the duplicate row 10 is **still counted** in these numbers. Our tools
never delete records on their own. They flag the duplicate, and a human
decides what to do.

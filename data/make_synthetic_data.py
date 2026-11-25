"""Makes a small MADE-UP CKD dataset. No real patients.
Run it from the project folder:  python data/make_synthetic_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(seed=42)   # fixed seed = same data every time
N = 300

df = pd.DataFrame({
    "patient_id": [f"P{i:04d}" for i in range(1, N + 1)],
    "age": rng.integers(30, 90, N),
    "sex": rng.choice(["Male", "Female"], N),
    "eGFR": rng.normal(55, 20, N).clip(5, 120).round(1),
    "diabetes": rng.choice(["Yes", "No"], N, p=[0.4, 0.6]),
    "systolic_bp": rng.normal(135, 15, N).round(0),
    "ckd_stage": rng.choice(["G1", "G2", "G3a", "G3b", "G4", "G5"], N),
})

# Problems added ON PURPOSE, so Phase 2's Data Quality tool has something to find:
df.loc[rng.choice(N, 15, replace=False), "eGFR"] = np.nan          # missing eGFR
df.loc[rng.choice(N, 8, replace=False), "systolic_bp"] = np.nan    # missing BP
df.loc[5, "age"] = 150                                             # impossible age
df.loc[10, "sex"] = "Unknown"                                      # unexpected category
df = pd.concat([df, df.iloc[[20, 21, 22]]], ignore_index=True)     # 3 duplicate rows

out = Path(__file__).parent / "synthetic_ckd_patients.csv"
df.to_csv(out, index=False)
print(f"Saved {len(df)} rows to {out}")
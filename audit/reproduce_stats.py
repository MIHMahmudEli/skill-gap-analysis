#!/usr/bin/env python3
"""Phase 5: independent local reproduction of STAT01/INTL01 core statistics.

Read-only vs raw data; writes audit/05_stat_reproduction.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score,
                             roc_curve, auc)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
out: dict = {"seed": 42}

# ---------------- College placement (STAT01) ----------------
df = pd.read_csv(ROOT / "datasets/kaggle/college-student-placement/college_student_placement_dataset.csv")
df["placed"] = (df["Placement"].str.strip().str.lower() == "yes").astype(int)
df["intern"] = (df["Internship_Experience"].str.strip().str.lower() == "yes").astype(int)
out["college_n"] = int(len(df))
out["n_placed"] = int(df.placed.sum())
out["base_rate"] = float(df.placed.mean())

# Welch tests + Cohen's d
def welch(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    n1, n2 = len(a), len(b)
    sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    d = (a.mean() - b.mean()) / sp
    return {"t": round(float(t), 2), "p": float(p), "d": round(float(d), 3),
            "m1": round(float(a.mean()), 2), "sd1": round(float(a.std(ddof=1)), 2),
            "m0": round(float(b.mean()), 2), "sd0": round(float(b.std(ddof=1)), 2)}

pl, npl = df[df.placed == 1], df[df.placed == 0]
out["welch"] = {
    "CGPA": welch(pl.CGPA, npl.CGPA),
    "IQ": welch(pl.IQ, npl.IQ),
    "Comm": welch(pl.Communication_Skills, npl.Communication_Skills),
    "Projects": welch(pl.Projects_Completed, npl.Projects_Completed),
    "AcadPerf": welch(pl.Academic_Performance, npl.Academic_Performance),
    "ExtraCurr": welch(pl.Extra_Curricular_Score, npl.Extra_Curricular_Score),
}

# chi-square
ct = pd.crosstab(df.placed, df.intern)
chi2, p, dof, _ = stats.chi2_contingency(ct)
out["chi2_internship"] = {"chi2": round(float(chi2), 2), "p": round(float(p), 4),
                          "V": round(float(np.sqrt(chi2 / len(df))), 3)}
ct2 = pd.crosstab(df.placed, df.Projects_Completed)
chi2b, pb, dofb, _ = stats.chi2_contingency(ct2)
out["chi2_projects"] = {"chi2": round(float(chi2b), 2), "p": float(pb),
                        "V": round(float(np.sqrt(chi2b / (len(df) * min(ct2.shape[0]-1, ct2.shape[1]-1)))), 3)}

# univariate internship RD
rd = df.loc[df.intern == 1, "placed"].mean() - df.loc[df.intern == 0, "placed"].mean()
out["intern_RD_pp"] = round(float(rd * 100), 4)

# standardized logistic with intercept
feats = ["CGPA", "Communication_Skills", "Projects_Completed", "intern", "IQ", "Academic_Performance"]
X = df[feats].astype(float)
Xz = (X - X.mean()) / X.std(ddof=0)
Xz = sm.add_constant(Xz)
model = sm.Logit(df.placed, Xz).fit(disp=0)
rows = []
for name, b, se in zip(feats, model.params[1:], model.bse[1:]):
    ci = model.conf_int().loc[name]
    rows.append({"feature": name, "coef": round(float(b), 4), "se": round(float(se), 4),
                 "OR": round(float(np.exp(b)), 4),
                 "OR_CI": [round(float(np.exp(ci[0])), 4), round(float(np.exp(ci[1])), 4)],
                 "p": float(model.pvalues[name])})
out["logistic"] = rows
out["logit_insample_acc"] = float((model.predict(Xz) >= 0.5).eq(df.placed).mean())

# VIF on standardized features (no const)
from statsmodels.stats.outliers_influence import variance_inflation_factor
vif = {f: round(float(variance_inflation_factor(Xz.values, i + 1)), 3) for i, f in enumerate(feats)}
out["vif"] = vif

# CV LR + AUC
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, C=1.0))
proba = cross_val_predict(pipe, X, df.placed, cv=cv, method="predict_proba")[:, 1]
pred = (proba >= 0.5).astype(int)
out["cv_lr"] = {"acc": round(float(accuracy_score(df.placed, pred)), 4),
                "auc": round(float(roc_auc_score(df.placed, proba)), 4),
                "f1w": round(float(f1_score(df.placed, pred, average="weighted")), 4)}

# tree / forest CV (diagnostic)
for name, est in [("rf", RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)),
                  ("dt", DecisionTreeClassifier(max_depth=6, random_state=42))]:
    p2 = cross_val_predict(est, X, df.placed, cv=cv, method="predict_proba")[:, 1]
    out[f"cv_{name}"] = {"acc": round(float(accuracy_score(df.placed, (p2 >= 0.5).astype(int))), 4),
                         "auc": round(float(roc_auc_score(df.placed, p2)), 4)}

# majority baseline
out["cv_baseline_acc"] = round(float(max(df.placed.mean(), 1 - df.placed.mean())), 4)

# ---------------- INTL01 ----------------
intl = pd.read_csv(ROOT / "datasets/kaggle/international-graduates-employment-dataset/dataset.csv")
# discover columns
out["intl_columns"] = intl.columns.tolist()[:20]
emp_col = next(c for c in intl.columns if "employ" in c.lower() and "status" in c.lower())
intern_col = next(c for c in intl.columns if "intern" in c.lower())
intl["employed"] = intl[emp_col].astype(str).str.strip().str.lower().eq("employed").astype(int)
# internship encoding (pandas 3 string dtype)
ic = intl[intern_col]
ic_str = ic.astype(str).str.strip().str.lower()
if ic_str.isin(["yes", "no"]).any():
    intl["has_intern"] = ic_str.eq("yes").astype(int)
else:
    intl["has_intern"] = (pd.to_numeric(ic, errors="coerce").fillna(0) > 0).astype(int)
p1 = intl.loc[intl.has_intern == 1, "employed"].mean()
p0 = intl.loc[intl.has_intern == 0, "employed"].mean()
out["intl"] = {"n": int(len(intl)), "emp_with": round(float(p1 * 100), 2),
               "emp_without": round(float(p0 * 100), 2),
               "rd_pp": round(float((p1 - p0) * 100), 2),
               "emp_col": emp_col, "intern_col": intern_col}

(ROOT / "audit" / "05_stat_reproduction.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2)[:4000])

"""STAT01: College placement core statistical analysis.

Inputs : college_student_placement_dataset.csv
Outputs: metrics.json + table1_descriptive.csv, table2_chi_square.csv,
         table3_correlation.csv, table_vif.csv, table4_logistic.csv,
         table5_rf_importance.csv, table6_cv_seed42.csv,
         table6b_cv_multiseed.csv, tree_audit.json

Includes: Welch t + Cohen's d; chi-square + Cramer's V; VIF; standardized
logistic regression with proper SE / Wald p / 95% CI (statsmodels);
5-fold stratified CV (seed 42) over 5 models; 10-seed x 5-fold robustness
aggregate; RF importances; depth-4 CART rule audit vs deterministic k-of-n
label rule.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, export_text

SEED = 42
MULTISEEDS = list(range(10))
FEATURES = ["CGPA", "Communication_Skills", "Projects_Completed",
            "Internship_Binary", "IQ", "Academic_Performance"]


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    local = (Path(__file__).resolve().parents[2] / "datasets" / "kaggle" /
             "college-student-placement" / name)
    candidates.append(local)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def cohens_d(g1, g2):
    n1, n2 = len(g1), len(g2)
    pooled = np.sqrt(((n1 - 1) * g1.var() + (n2 - 1) * g2.var()) / (n1 + n2 - 2))
    return float((g1.mean() - g2.mean()) / pooled) if pooled > 0 else 0.0


def sig_stars(p):
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def cv_models(X, y, seeds):
    models_fn = {
        "Logistic Regression": lambda s: LogisticRegression(max_iter=1000, random_state=s),
        "Random Forest": lambda s: RandomForestClassifier(n_estimators=100, max_depth=12, random_state=s),
        "SVM (RBF)": lambda s: SVC(kernel="rbf", C=1.0, probability=True, random_state=s),
        "Decision Tree": lambda s: DecisionTreeClassifier(max_depth=6, random_state=s),
        "Baseline (Majority)": lambda s: DummyClassifier(strategy="most_frequent"),
    }
    records = []
    for seed in seeds:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for name, factory in models_fn.items():
            model = factory(seed)
            accs, f1s, aucs, precs, recs = [], [], [], [], []
            for tr, te in skf.split(X, y):
                X_tr, X_te = X[tr], X[te]
                y_tr, y_te = y[tr], y[te]
                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_tr)
                X_te_s = scaler.transform(X_te)
                model.fit(X_tr_s, y_tr)
                pred = model.predict(X_te_s)
                accs.append(accuracy_score(y_te, pred))
                f1s.append(f1_score(y_te, pred, average="weighted", zero_division=0))
                precs.append(precision_score(y_te, pred, average="weighted", zero_division=0))
                recs.append(recall_score(y_te, pred, average="weighted", zero_division=0))
                if hasattr(model, "predict_proba"):
                    aucs.append(roc_auc_score(y_te, model.predict_proba(X_te_s)[:, 1]))
                else:
                    aucs.append(0.5)
            records.append({
                "seed": seed, "model": name,
                "accuracy": float(np.mean(accs)), "f1_weighted": float(np.mean(f1s)),
                "precision_weighted": float(np.mean(precs)),
                "recall_weighted": float(np.mean(recs)),
                "auc": float(np.mean(aucs)),
                "accuracy_fold_sd": float(np.std(accs, ddof=1)),
                "f1_fold_sd": float(np.std(f1s, ddof=1)),
                "auc_fold_sd": float(np.std(aucs, ddof=1)),
            })
    return pd.DataFrame(records)


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(resolve("college_student_placement_dataset.csv"))
    df["Placement_Binary"] = (df["Placement"] == "Yes").astype(int)
    df["Internship_Binary"] = (df["Internship_Experience"] == "Yes").astype(int)
    placed = df[df.Placement == "Yes"]
    not_placed = df[df.Placement == "No"]

    # --- Table 1: descriptives + Welch t + Cohen's d ---
    vars_list = ["CGPA", "IQ", "Prev_Sem_Result", "Communication_Skills",
                 "Projects_Completed", "Academic_Performance", "Extra_Curricular_Score"]
    t1 = []
    for var in vars_list:
        g1, g2 = placed[var].dropna(), not_placed[var].dropna()
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        d = cohens_d(g1, g2)
        t1.append({
            "Variable": var,
            "Placed_Mean": round(float(g1.mean()), 2), "Placed_SD": round(float(g1.std()), 2),
            "NotPlaced_Mean": round(float(g2.mean()), 2), "NotPlaced_SD": round(float(g2.std()), 2),
            "t_statistic": round(float(t_stat), 3), "p_value": float(f"{p_val:.4g}"),
            "Cohens_d": round(d, 3), "Significance": sig_stars(p_val),
        })
    t1_df = pd.DataFrame(t1)

    # --- Table 2: chi-square + Cramer's V ---
    df["Projects_Group"] = pd.cut(df["Projects_Completed"], bins=[-1, 1, 2, 10],
                                  labels=["0-1", "2", "3+"])
    t2 = []
    for test_name, v1, v2 in [
        ("Placement vs Internship Experience", "Placement", "Internship_Experience"),
        ("Placement vs Projects Grouped", "Placement", "Projects_Group"),
    ]:
        ct = pd.crosstab(df[v1], df[v2])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        v = float(np.sqrt(chi2 / (len(df) * (min(ct.shape) - 1))))
        t2.append({"Test": test_name, "chi2": round(float(chi2), 3), "df": int(dof),
                   "p_value": float(f"{p:.4g}"), "Cramers_V": round(v, 3),
                   "Significance": sig_stars(p)})
    t2_df = pd.DataFrame(t2)

    # --- Table 3: correlation matrix ---
    corr_vars = ["CGPA", "IQ", "Prev_Sem_Result", "Communication_Skills",
                 "Projects_Completed", "Academic_Performance", "Extra_Curricular_Score",
                 "Placement_Binary", "Internship_Binary"]
    corr = df[corr_vars].corr().round(3)

    # --- VIF ---
    X_df = df[FEATURES].dropna()
    y = df.loc[X_df.index, "Placement_Binary"].values
    vif_vals = np.diag(np.linalg.inv(X_df.corr().values))
    vif_df = pd.DataFrame({
        "Feature": FEATURES,
        "VIF": np.round(vif_vals, 3),
        "Tolerance": np.round(1.0 / vif_vals, 3),
        "Status": ["Acceptable (<5)" if v < 5 else "Collinear (>=5)" for v in vif_vals],
    })

    # --- Table 4: standardized logistic with proper inference (statsmodels) ---
    import statsmodels.api as sm
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X_df)
    X_log = sm.add_constant(X_sc)  # intercept required: features are centered,
    # omitting it forces the boundary through the origin and biases slopes 3x
    logit = sm.Logit(y, X_log).fit(disp=False)
    or_rows = []
    for i, name in enumerate(FEATURES):
        j = i + 1  # skip constant at index 0
        beta = float(logit.params[j])
        se = float(logit.bse[j])
        z = beta / se
        p = float(2 * stats.norm.sf(abs(z)))
        ci = logit.conf_int(alpha=0.05)[j]
        or_rows.append({
            "Feature": name,
            "Coefficient": round(beta, 4),
            "Std_Error": round(se, 4),
            "Odds_Ratio": round(float(np.exp(beta)), 4),
            "OR_CI_Lower": round(float(np.exp(ci[0])), 4),
            "OR_CI_Upper": round(float(np.exp(ci[1])), 4),
            "z": round(z, 3),
            "p_value": float(f"{p:.4g}"),
            "Significance": sig_stars(p),
        })
    t4_df = pd.DataFrame(or_rows)

    # --- Table 5: RF importances (in-sample fit, documented as such) ---
    rf = RandomForestClassifier(n_estimators=100, random_state=SEED)
    rf.fit(X_sc, y)
    t5_df = pd.DataFrame(
        [{"Feature": f, "Importance": round(float(i), 4)}
         for f, i in sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1])]
    )

    # --- Table 6: 5-fold CV, seed 42 + multi-seed robustness ---
    cv1 = cv_models(X_df.values, y, [SEED])
    cv1_mean = cv1.groupby("model", sort=False)[
        ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted", "auc"]
    ].mean().round(4)
    cv1_out = cv1_mean.copy()
    # fold-level SDs (std across the 5 CV folds of seed 42)
    cv1_out["accuracy_sd"] = cv1.groupby("model", sort=False)[
        "accuracy_fold_sd"].first().round(4)
    cv1_out["f1_sd"] = cv1.groupby("model", sort=False)[
        "f1_fold_sd"].first().round(4)
    cv1_out["auc_sd"] = cv1.groupby("model", sort=False)[
        "auc_fold_sd"].first().round(4)
    cv1_out = cv1_out.reset_index()

    cv_multi = cv_models(X_df.values, y, MULTISEEDS)
    multi_agg = cv_multi.groupby("model", sort=False)[
        ["accuracy", "f1_weighted", "auc"]
    ].agg(["mean", "std"]).round(4)
    multi_rows = []
    for model_name in cv_multi.model.unique():
        sub = cv_multi[cv_multi.model == model_name]
        multi_rows.append({
            "model": model_name,
            "n_seed_fold_evals": int(len(sub) * 5),
            "n_seeds": int(sub.seed.nunique()),
            "accuracy_mean": round(float(sub.accuracy.mean()), 4),
            "accuracy_sd": round(float(sub.accuracy.std()), 4),
            "f1_mean": round(float(sub.f1_weighted.mean()), 4),
            "f1_sd": round(float(sub.f1_weighted.std()), 4),
            "auc_mean": round(float(sub.auc.mean()), 4),
            "auc_sd": round(float(sub.auc.std()), 4),
        })
    multi_df = pd.DataFrame(multi_rows)

    # --- Tree audit: depth-4 CART + deterministic k-of-n rule ---
    dt4 = DecisionTreeClassifier(max_depth=4, random_state=SEED)
    dt4.fit(X_sc, y)
    rule_text = export_text(dt4, feature_names=FEATURES)
    dt_pred = dt4.predict(X_sc)
    dt_acc = float(accuracy_score(y, dt_pred))

    kofn = ((df["CGPA"] > 8.01).astype(int) +
            (df["IQ"] > 110.5).astype(int) +
            (df["Communication_Skills"] > 7.50).astype(int) +
            (df["Projects_Completed"] >= 2).astype(int))
    kofn_pred = (kofn >= 3).astype(int)
    kofn_agreement = float((kofn_pred == y).mean())
    dt_vs_kofn = float((dt_pred == kofn_pred).mean())

    audit = {
        "depth4_cart_train_accuracy": round(dt_acc, 4),
        "kofn_rule": "placed if >=3 of {CGPA>8.01, IQ>110.5, Communication>7.50, Projects>=2}",
        "kofn_agreement_with_labels": round(kofn_agreement, 4),
        "cart_vs_kofn_agreement": round(dt_vs_kofn, 4),
        "tree_rules": rule_text,
    }

    n_placed = int((y == 1).sum())
    n_not = int((y == 0).sum())
    metrics = {
        "experiment_id": "STAT01_placement_core",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "multiseeds": MULTISEEDS,
        "dataset": "college_student_placement_dataset.csv",
        "n_total": int(len(df)),
        "n_placed": n_placed,
        "n_not_placed": n_not,
        "base_rate_placed": round(n_placed / len(df), 4),
        "logistic_insample_accuracy": round(
            float(((logit.predict(X_log) > 0.5).astype(int) == y).mean()), 4),
        "logistic_pseudo_r2_mcfadden": round(float(logit.prsquared), 4),
        "table4_logistic": t4_df.to_dict(orient="records"),
        "cv_seed42": cv1_out.to_dict(orient="records"),
        "cv_multiseed": multi_rows,
        "tree_audit": audit,
        "chi_square": t2_df.to_dict(orient="records"),
    }

    t1_df.to_csv(out_dir / "table1_descriptive.csv", index=False)
    t2_df.to_csv(out_dir / "table2_chi_square.csv", index=False)
    corr.to_csv(out_dir / "table3_correlation.csv")
    vif_df.to_csv(out_dir / "table_vif.csv", index=False)
    t4_df.to_csv(out_dir / "table4_logistic.csv", index=False)
    t5_df.to_csv(out_dir / "table5_rf_importance.csv", index=False)
    cv1_out.to_csv(out_dir / "table6_cv_seed42.csv", index=False)
    multi_df.to_csv(out_dir / "table6b_cv_multiseed.csv", index=False)
    cv_multi.to_csv(out_dir / "table6c_cv_multiseed_raw.csv", index=False)
    with open(out_dir / "tree_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(json.dumps(metrics, indent=2, default=str)[:4000])


if __name__ == "__main__":
    sys.exit(main())

"""Figures comparing all estimators including MLA (overwrites prevalence_estimators.png, se_ratio.png, gold_size_se.png; adds rating_estimators.png)
and outputs/all_methods.json for the report."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
S3 = Path(__file__).resolve().parent.parent; O = S3 / "outputs"; FIG = O / "figures"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]; short = lambda c: c.replace("Absence of ", "")
rd = lambda p: json.loads(open(p, encoding="utf-8").read().replace("NaN", "null"))
E = pd.DataFrame(rd(O / "dsl_supervised.json")["estimates"]); M = rd(O / "mla.json")
A = pd.DataFrame(M["A"]).assign(estimator="MLA")
E = pd.concat([E, A[["construct", "estimator", "prevalence", "prevalence SE", "rating coef", "rating coef SE"]]], ignore_index=True)
base = E[E.estimator == "gold only (100 reviews)"].set_index("construct")
E["SE ratio vs gold only (prevalence)"] = E.apply(lambda r: r["prevalence SE"] / base.loc[r.construct, "prevalence SE"], axis=1)
E["SE ratio vs gold only (rating coef)"] = E.apply(lambda r: r["rating coef SE"] / base.loc[r.construct, "rating coef SE"], axis=1)
EST = [("naive (majority of groups)", "Naive (majority vote)", "#bfbfbf"), ("gold only (100 reviews)", "Human codes only", "#1f3864"), ("DMM", "DMM", "#8faadc"),
       ("DMM-DSL", "DMM-DSL", "#7f6000"), ("DSL, supervised: labels + embedding + genre + length", "DSL, supervised predictor", "#c55a11"), ("MLA", "MLA", "#548235")]
for col, se, fn, xl, lim in (("prevalence", "prevalence SE", "prevalence_estimators.png", "estimated share of reviews coded 1 (95% CI)", (-0.15, 0.75)),
                             ("rating coef", "rating coef SE", "rating_estimators.png", "difference in star rating, coded 1 vs 0 (95% CI)", (-3, 2.5))):
    fig, ax = plt.subplots(figsize=(8.5, 4.8)); y0 = np.arange(len(C6))[::-1] * (len(EST) + 1.5)
    for j, (k, lab, cc) in enumerate(EST):
        d = E[E.estimator == k].set_index("construct").loc[C6]; lo = np.clip(d[col] - 1.96 * d[se], *lim); hi = np.clip(d[col] + 1.96 * d[se], *lim)
        ax.errorbar(d[col], y0 - j, xerr=[d[col] - lo, hi - d[col]], fmt="o", color=cc, ms=4, capsize=2, lw=1.2, label=lab)
    if col == "rating coef": ax.axvline(0, color="black", lw=0.6)
    ax.set_yticks(y0 - 2.5); ax.set_yticklabels([short(c) for c in C6], fontsize=8); ax.set_xlabel(xl + ("; DMM / DMM-DSL intervals cut at the axis" if col == "rating coef" else ""), fontsize=8)
    ax.set_xlim(*lim); ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13)); ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout(); plt.savefig(FIG / fn, dpi=200); plt.close()
S = [("DMM-DSL", "DMM-DSL", "#7f6000"), ("DSL, majority vote (no training)", "DSL, majority vote", "#8faadc"), ("DSL, supervised: labels only", "DSL, supervised (labels)", "#2e5597"),
     ("DSL, supervised: labels + embedding + genre + length", "DSL, supervised (labels + text)", "#c55a11"), ("MLA", "MLA", "#548235")]
fig, axes = plt.subplots(1, 2, figsize=(10, 3.3)); x = np.arange(len(C6)); w = 0.16
for ax, (col, ttl) in zip(axes, (("SE ratio vs gold only (prevalence)", "Share coded 1"), ("SE ratio vs gold only (rating coef)", "Rating effect"))):
    for j, (k, lab, cc) in enumerate(S):
        d = E[E.estimator == k].set_index("construct").loc[C6]; ax.bar(x + (j - 2) * w, np.minimum(d[col], 2.5), w, color=cc, label=lab)
    ax.axhline(1, color="black", lw=0.8, ls="--"); ax.set_xticks(x); ax.set_xticklabels([short(c) for c in C6], fontsize=7, rotation=20); ax.set_ylim(0, 2.5)
    ax.set_title(ttl, fontsize=9); ax.set_ylabel("SE relative to human codes only\n(bars cut at 2.5)", fontsize=7); ax.spines[["top", "right"]].set_visible(False)
axes[0].legend(fontsize=6.5, frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(1.1, 1.22))
plt.tight_layout(); plt.savefig(FIG / "se_ratio.png", dpi=200); plt.close()
# gold-size SE curves incl. MLA
G = pd.DataFrame(rd(O / "gold_size.json")["summary"]); MB = pd.DataFrame(M["B"]).assign(estimator="MLA"); G = pd.concat([G, MB], ignore_index=True)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
for ax, (cse, ttl) in zip(axes, (("mean_SE", "Share coded 1"), ("rating_mean_SE", "Rating effect"))):
    for k, cc in (("human codes only", "#1f3864"), ("DSL, supervised predictor", "#c55a11"), ("MLA", "#548235")):
        v = G[(G.estimator == k) & (G.n > 0)].groupby("n").agg(se=(cse, "mean"), na=("n_actual", "mean")); ax.plot(v.na, v.se, "o-", color=cc, label=k)
    v0 = G[(G.estimator == "human codes only") & (G.n == 100)][cse].mean(); xs = np.array(sorted(G[(G.estimator == "human codes only") & (G.n > 0)].groupby("n").n_actual.mean()))
    ax.plot(xs, v0 * np.sqrt(100 / xs), ls="--", color="grey", lw=1, label="1/√n from 100 human codes"); ax.set_xticks(xs); ax.set_xticklabels([f"{v:.0f}" for v in xs])
    ax.set_xlabel("number of human-coded reviews", fontsize=8); ax.set_ylabel("mean standard error (6 constructs)", fontsize=8); ax.set_title(ttl, fontsize=9)
    ax.legend(fontsize=7, frameon=False); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(FIG / "gold_size_se.png", dpi=200); plt.close()
json.dump({"estimates": E.to_dict("records"), "gold_size": G.to_dict("records")}, open(O / "all_methods.json", "w"), indent=1, default=float)
print(E[E.estimator.isin(["gold only (100 reviews)", "DSL, supervised: labels + embedding + genre + length", "MLA"])][["construct", "estimator", "prevalence", "prevalence SE", "rating coef", "rating coef SE"]].round(3).to_string(index=False))

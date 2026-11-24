"""Figures and collected numbers for the Stage 3 report -> outputs/report_s3.json, outputs/figures/*.png"""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
S3 = Path(__file__).resolve().parent.parent; O = S3 / "outputs"; FIG = O / "figures"; FIG.mkdir(exist_ok=True)
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]; short = lambda c: c.replace("Absence of ", "")
rd = lambda p: json.loads(open(p, encoding="utf-8").read().replace("NaN", "null"))
full, nog, ds = rd(O / "dmm_dsl_Gemma-Qwen-FT-GPT.json"), rd(O / "dmm_dsl_Gemma-Qwen-FT-GPT_nogenre.json"), rd(O / "dsl_supervised.json")
E = pd.DataFrame(ds["estimates"]); U = pd.read_csv(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig")
cost = {}
for k, (pi, po) in {"luna": (0.10, 0.50), "mini": (0.75, 4.50)}.items():
    c = 0
    for f in (f"progress_{k}.jsonl", f"goldfill_{k}.jsonl"):
        for l in open(O / f, encoding="utf-8"):
            r = json.loads(l); c += ((r.get("prompt_tokens") or 0) - (r.get("cached_tokens") or 0)) * pi + (r.get("cached_tokens") or 0) * pi / 10 + (r.get("completion_tokens") or 0) * po
    cost[k] = c / 1e6
cost["embeddings"] = json.load(open(O / "embedding_cost.json"))["cost_usd"]
out = {"ci_full": full["ci"], "ci_nogenre": nog["ci"], "bridge": full["bridge"], "estimates": ds["estimates"], "predictors": ds["predictors"], "cost": cost,
       "genre_top": U["genre: top"].value_counts().to_dict(), "gold_genre_top": U[U.source == "gold"]["genre: top"].value_counts().to_dict(),
       "n_words_median": {"gold": float(U[U.source == "gold"].n_words.median()), "new": float(U[U.source == "new"].n_words.median())},
       "rating_dist": U[U.source == "new"].rating.value_counts().sort_index().to_dict()}
json.dump(out, open(O / "report_s3.json", "w"), indent=1, default=float)
# Figure 1: prevalence estimates with 95% CI
EST = [("naive (majority of groups)", "Naive (majority vote)", "#bfbfbf"), ("gold only (100 reviews)", "Human codes only", "#1f3864"),
       ("DMM", "DMM", "#8faadc"), ("DMM-DSL", "DMM-DSL", "#7f6000"), ("DSL, supervised: labels + embedding + genre + length", "DSL, supervised predictor", "#c55a11")]
fig, ax = plt.subplots(figsize=(8.5, 4.2)); y0 = np.arange(len(C6))[::-1] * (len(EST) + 1.5)
for j, (k, lab, col) in enumerate(EST):
    d = E[E.estimator == k].set_index("construct").loc[C6]; yy = y0 - j
    ax.errorbar(d.prevalence, yy, xerr=1.96 * d["prevalence SE"], fmt="o", color=col, ms=4, capsize=2, lw=1.2, label=lab)
ax.set_yticks(y0 - 2); ax.set_yticklabels([short(c) for c in C6], fontsize=8); ax.set_xlabel("estimated share of reviews coded 1 (95% CI)", fontsize=8)
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13)); ax.spines[["top", "right"]].set_visible(False); ax.set_xlim(-0.15, 0.75)
plt.tight_layout(); plt.savefig(FIG / "prevalence_estimators.png", dpi=200); plt.close()
# Figure 2: SE relative to human codes only
S = [("DMM-DSL", "DMM-DSL", "#7f6000"), ("DSL, majority vote (no training)", "DSL, majority vote", "#8faadc"),
     ("DSL, supervised: labels only", "DSL, supervised (labels)", "#2e5597"), ("DSL, supervised: labels + embedding + genre + length", "DSL, supervised (labels + text)", "#c55a11")]
fig, ax = plt.subplots(figsize=(8.5, 3.0)); x = np.arange(len(C6)); w = 0.2
for j, (k, lab, col) in enumerate(S):
    d = E[E.estimator == k].set_index("construct").loc[C6]; ax.bar(x + (j - 1.5) * w, d["SE ratio vs gold only (prevalence)"], w, color=col, label=lab)
ax.axhline(1, color="black", lw=0.8, ls="--"); ax.text(5.55, 1.03, "human codes only", fontsize=7, ha="right")
ax.set_xticks(x); ax.set_xticklabels([short(c) for c in C6], fontsize=8); ax.set_ylabel("SE relative to\nhuman codes only", fontsize=8); ax.set_ylim(0, 2.2)
ax.legend(fontsize=7, frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.16)); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(FIG / "se_ratio.png", dpi=200); plt.close()
print("ok", cost)

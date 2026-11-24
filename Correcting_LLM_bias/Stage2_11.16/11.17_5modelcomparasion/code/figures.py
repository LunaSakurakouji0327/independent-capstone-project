"""Figures + JSON data for the 11.17 model-comparison report."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
D = Path(__file__).resolve().parent.parent; X = D / "Stage3_results.xlsx"; F = D / "outputs" / "figures"
prev = pd.read_excel(X, sheet_name="share coded 1", index_col=0)
pair = pd.read_excel(X, sheet_name="pairwise kappa")
fl = pd.read_excel(X, sheet_name="Fleiss kappa", index_col=0).iloc[:, 0]
pe = pd.read_excel(X, sheet_name="prompt effect"); cost = pd.read_excel(X, sheet_name="cost")
models = list(prev.columns); cols = ["#1f3864", "#c55a11", "#548235", "#7f6000", "#8faadc"]
fig, ax = plt.subplots(figsize=(9, 3.6)); w = 0.16; x = np.arange(len(prev.index))
for j, m in enumerate(models): ax.bar(x + (j - 2) * w, prev[m], w, label=m, color=cols[j])
ax.set_xticks(x); ax.set_xticklabels([c.replace("Absence of ", "") for c in prev.index], fontsize=8)
ax.set_ylabel("share of 150 reviews coded 1"); ax.legend(fontsize=7, ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12))
ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig(F / "prevalence.png", dpi=200); plt.close()
M = pd.DataFrame(np.eye(len(models)), index=models, columns=models)
for _, r in pair.iterrows():
    a, b = r["pair"].split(" – "); M.loc[a, b] = M.loc[b, a] = r["Macro (6, excl. Change)"]
fig, ax = plt.subplots(figsize=(5.6, 4.4)); im = ax.imshow(M.values, cmap="Blues", vmin=0.3, vmax=1)
ax.set_xticks(range(len(models))); ax.set_xticklabels(models, rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(models))); ax.set_yticklabels(models, fontsize=8)
for i in range(len(models)):
    for j in range(len(models)):
        if i != j: ax.text(j, i, f"{M.values[i, j]:.2f}", ha="center", va="center", fontsize=8, color="white" if M.values[i, j] > 0.62 else "black")
plt.colorbar(im, fraction=0.046); ax.set_title("Pairwise Cohen's κ (mean over 6 constructs)", fontsize=9)
plt.tight_layout(); plt.savefig(F / "pairwise_kappa.png", dpi=200); plt.close()
ep = json.load(open(D.parent / "11.16_humanAIcomparasion_finetune" / "outputs_1epoch" / "epoch_comparison.json"))
json.dump({"models": models, "prev": prev.to_dict(), "pair": pair.to_dict("records"), "fleiss": fl.to_dict(),
           "pe": pe.to_dict("records"), "cost": cost.fillna("").to_dict("records"), "epoch": ep},
          open(D / "outputs" / "report_data.json", "w"), indent=1, default=float)
print("ok")

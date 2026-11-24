"""Extra numbers + figure for the Stage 2 fine-tuning report.
Writes outputs/report_extras.json and outputs/figures/heldout_curves.png."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]
C6 = C[:-1]

def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]

ft = load(OUT / "predictions_finetuned.jsonl")
zs = load(OUT / "predictions_zeroshot.jsonl")
fold_of = {r["review_id"]: r["fold"] for r in ft}

def per_fold(rows):
    res = {}
    for k in range(5):
        rr = [r for r in rows if fold_of.get(r["review_id"]) == k and r["gold"] is not None]
        acc = np.mean([r["pred"] == r["gold"] for r in rr])
        ks = []
        for c in C6:
            g = [r["gold"] for r in rr if r["construct"] == c]
            p = [r["pred"] for r in rr if r["construct"] == c]
            if len(set(g)) > 1 or len(set(p)) > 1:
                k_ = cohen_kappa_score(g, p)
                if not np.isnan(k_):
                    ks.append(k_)
        res[k] = {"acc": float(acc), "macro_kappa": float(np.mean(ks)) if ks else None, "n": len(rr)}
    return res

pos = {}
for c in C:
    g = [r for r in ft if r["construct"] == c and r["gold"] is not None]
    z = [r for r in zs if r["construct"] == c and r["gold"] is not None]
    pos[c] = {"human": int(sum(r["gold"] for r in g)), "ft": int(sum(r["pred"] for r in g)),
              "zs": int(sum(r["pred"] for r in z)), "n": len(g)}

extras = {"per_fold_ft": per_fold(ft), "per_fold_zs": per_fold(zs), "positives": pos}

ev = load(OUT / "eval_log.jsonl")
extras["eval_log"] = ev
json.dump(extras, open(OUT / "report_extras.json", "w"), indent=1)

fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
cols = {2: "#1f3864", 3: "#c55a11", 4: "#548235"}
for k in sorted({r["fold"] for r in ev}):
    rr = sorted([r for r in ev if r["fold"] == k], key=lambda r: r["step"])
    s = [r["step"] for r in rr]
    axes[0].plot(s, [r["heldout_logloss"] for r in rr], "o-", ms=4, color=cols.get(k), label=f"fold {k+1}")
    axes[1].plot(s, [r["heldout_acc"] for r in rr], "o-", ms=4, color=cols.get(k), label=f"fold {k+1}")
axes[0].set_yscale("log"); axes[0].set_ylabel("held-out log-loss (log scale)")
axes[1].set_ylabel("held-out accuracy"); axes[1].set_ylim(0.6, 1.0)
for ax in axes:
    ax.set_xlabel("optimizer step"); ax.axvline(70, color="grey", ls=":", lw=1)
    ax.spines[["top", "right"]].set_visible(False); ax.legend(fontsize=8, frameon=False)
axes[1].text(71, 0.62, "epoch 2 starts", fontsize=7, color="grey")
plt.tight_layout(); plt.savefig(OUT / "figures" / "heldout_curves.png", dpi=200); plt.close()
print(json.dumps({k: v for k, v in extras.items() if k != "eval_log"}, indent=1))

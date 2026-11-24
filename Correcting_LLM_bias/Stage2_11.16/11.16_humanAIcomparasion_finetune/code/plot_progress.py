"""Learning curves: training loss and held-out log-loss / accuracy per fold (from eval_log.jsonl)."""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"; (OUT / "figures").mkdir(parents=True, exist_ok=True)
tr = [json.loads(l) for l in open(OUT / "training_log.jsonl")]
ev = [json.loads(l) for l in open(OUT / "eval_log.jsonl")] if (OUT / "eval_log.jsonl").exists() else []
folds = sorted({r["fold"] for r in ev})
if len(sys.argv) > 1:
    folds = [int(sys.argv[1])]


def roll(v, w=10):
    return [sum(v[max(0, i - w + 1): i + 1]) / len(v[max(0, i - w + 1): i + 1]) for i in range(len(v))]


for k in folds:
    t = [r for r in tr if r["fold"] == k and "wall" in r]
    e = [r for r in ev if r["fold"] == k]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    if t:
        a1.plot([r["step"] for r in t], [r["loss"] for r in t], color="#BBBBBB", lw=0.8, label="training loss (per step)")
        a1.plot([r["step"] for r in t], roll([r["loss"] for r in t]), color="#1F3864", lw=1.8, label="training loss (10-step mean)")
    a1.plot([r["step"] for r in e], [r["heldout_logloss"] for r in e], "o-", color="#C55A11", lw=1.8, label="held-out log-loss")
    a1.set_xlabel("optimizer step (8 examples each)"); a1.set_ylabel("loss"); a1.set_xlim(0, 140); a1.set_ylim(bottom=0)
    a1.legend(fontsize=8, frameon=False); a1.set_title(f"Fold {k+1}: loss"); a1.spines[["top", "right"]].set_visible(False)

    a2.plot([r["step"] for r in e], [r["heldout_acc"] for r in e], "o-", color="#C55A11", lw=1.8, label="held-out accuracy (20 reviews × 7)")
    if e and e[0]["step"] == 0:
        a2.axhline(e[0]["heldout_acc"], color="#7F7F7F", ls="--", lw=1, label=f"step 0 = zero-shot ({e[0]['heldout_acc']:.3f})")
    for r in e:
        a2.annotate(f"{r['heldout_acc']:.2f}", (r["step"], r["heldout_acc"]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7)
    a2.set_xlabel("optimizer step"); a2.set_ylabel("accuracy"); a2.set_xlim(0, 140); a2.set_ylim(0.5, 1.0)
    a2.legend(fontsize=8, frameon=False, loc="lower right"); a2.set_title(f"Fold {k+1}: held-out accuracy"); a2.spines[["top", "right"]].set_visible(False)

    if len(t) > 1:
        sps = (t[-1]["wall"] - t[0]["wall"]) / max(1, t[-1]["step"] - t[0]["step"])
        fig.suptitle(f"Qwen3-14B QLoRA, fold {k+1}: {t[-1]['step']}/140 steps, ~{sps:.0f} s/step", fontsize=10)
    plt.tight_layout()
    fn = OUT / "figures" / f"learning_curve_fold{k+1}.png"
    plt.savefig(fn, dpi=150); plt.close()
    print("saved", fn)

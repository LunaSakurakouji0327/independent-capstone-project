"""Collect the numbers of every step (Stage 2 -> Latin-square redesign) into outputs/report2_data.json and draw the summary figures."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
D = Path(__file__).resolve().parent.parent; F = D.parent / "11.16_humanAIcomparasion_finetune"; O = D / "outputs"; FIG = O / "figures"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
rd = lambda p: json.loads(open(p, encoding="utf-8").read().replace("NaN", "null"))
out = {}
# Stage 2: human vs LLMs, fine-tuning
met = rd(F / "outputs" / "metrics.json"); MAC = "Macro mean (excl. Change)"
names = ["Qwen3-14B fine-tuned (5-fold CV)", "Qwen3-14B zero-shot (same prompt v1)", "GPT-4o (prompt v2, Exp. 3)", "Sonnet 5.5 (prompt v2, Exp. 3)",
         "Gemma 3 12B (prompt v2, Exp. 3)", "Qwen3-14B Ollama (prompt v2, Exp. 3)"]
out["stage2_kappa"] = {n: met["kappa"][f"{n} | {MAC}"] for n in names}
out["stage2_kappa_construct"] = {n: {c: met["kappa"][f"{n} | {c}"][0] for c in C6} for n in names}
out["stage2_diff"] = {k: v for k, v in met["diff_kappa"].items() if MAC in k}
out["epoch"] = rd(F / "outputs_1epoch" / "epoch_comparison.json")
# Stage 3 random design: agreement and cost
out["s3"] = rd(O / "report_data.json")
# gold kappa of all models (incl. Luna / mini on the human-coded reviews)
ci = rd(O / "ci_dmm.json"); out["gold_kappa"] = ci["kap"]
# CI step series on the gold sample, 5 Stage-3 models, BETWEEN-GROUP pairs only (Luna-mini excluded everywhere)
S5 = {"Sonnet 5.5", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"}
alias = {"Sonnet 5.5 (v2)": "Sonnet 5.5", "Gemma 3 12B (v2)": "Gemma 3 12B", "Qwen3-14B fine-tuned (CV, v1)": "Qwen3-14B fine-tuned",
         "GPT-6 Luna (v2/v3/v4)": "GPT-6 Luna", "GPT-5.4 mini (v2/v3/v4)": "GPT-5.4 mini"}
def between(df, c1="model 1", c2="model 2"):
    df = df.copy(); df[c1] = df[c1].replace(alias); df[c2] = df[c2].replace(alias)
    df = df[df[c1].isin(S5) & df[c2].isin(S5)]
    return df[~(df[c1].str.startswith("GPT") & df[c2].str.startswith("GPT"))]
steps = {}
a = between(pd.DataFrame(ci["A"])).rename(columns={"residual corr | X*, length": "rc", "perm p": "p"}); steps["1 length"] = a
e = pd.DataFrame(rd(O / "ci_embed.json")["A"]); steps["2 embedding"] = between(e[e.D == "pc=10"]).rename(columns={"residual corr": "rc"})
pr = pd.read_excel(D / "CI_prompt_results.xlsx", sheet_name="A gold residual moments"); steps["3 embedding + prompt"] = between(pr[pr.D == "pc=10 + prompt"]).rename(columns={"residual corr": "rc"})
la = pd.DataFrame(rd(O / "ci_latin.json")["A"]); steps["4 GPT group + Latin square"] = between(la[la.design == "latin"]).rename(columns={"residual corr": "rc"})
out["steps"] = {s: {c: {"median": float(d[d.construct == c].rc.median()), "sig": int((d[d.construct == c].p < .05).sum()), "pairs": int((d.construct == c).sum())} for c in C6}
                for s, d in steps.items()}
same = pd.read_excel(D / "CI_prompt_results.xlsx", sheet_name="A same vs different prompt")
out["same_prompt"] = same[same.group.isin(["same prompt", "different prompt"])].pivot(index="construct", columns="group", values="residual corr").to_dict()
out["same_n"] = same.groupby("group")["n"].first().to_dict()
# no-gold tests (150 new reviews)
B1 = pd.DataFrame(ci["B"]); Be = pd.DataFrame(rd(O / "ci_embed.json")["Bo"]); Bp = pd.read_excel(D / "CI_prompt_results.xlsx", sheet_name="B overidentification")
Bl = pd.DataFrame(rd(O / "ci_latin.json")["Bo"]); Sl = pd.DataFrame(rd(O / "ci_latin.json")["Bs"])
Se = pd.DataFrame(rd(O / "ci_embed.json")["Bs"]); S1 = pd.DataFrame(ci["S"])
out["nogold"] = {
    "5 models, no covariates": dict(zip(B1.construct, B1["bootstrap p (overidentification)"])),
    "5 models, embedding (5 PCs)": dict(zip(Be[Be.D == "pc=5"].construct, Be[Be.D == "pc=5"]["bootstrap p"])),
    "5 models, embedding + prompt": dict(zip(Bp[Bp.D == "pc=5 + prompt"].construct, Bp[Bp.D == "pc=5 + prompt"]["bootstrap p"])),
    "4 groups, random prompts": dict(zip(Bl[Bl.design == "random"].construct, Bl[Bl.design == "random"]["bootstrap p"])),
    "4 groups, Latin square": dict(zip(Bl[Bl.design == "latin"].construct, Bl[Bl.design == "latin"]["bootstrap p"]))}
out["subset"] = {"4 groups, random prompts": Sl[Sl.design == "random"].set_index("construct")[["min subset prevalence", "max subset prevalence", "heterogeneity p"]].to_dict("index"),
                 "4 groups, Latin square": Sl[Sl.design == "latin"].set_index("construct")[["min subset prevalence", "max subset prevalence", "heterogeneity p"]].to_dict("index")}
out["latin_prev"] = dict(zip(Bl[Bl.design == "latin"].construct, Bl[Bl.design == "latin"].prevalence))
out["latin_worst"] = dict(zip(Bl[Bl.design == "latin"].construct, Bl[Bl.design == "latin"]["worst group pair"]))
out["costs"] = {"Stage 3 labelling (random design, 150 reviews)": 9.745 + 0.1432 + 0.8804, "discarded default-CLI Sonnet calls": 2.70,
                "Luna + 5.4 mini on 100 human-coded reviews (random design)": 0.70, "embeddings (text-embedding-3-large, 250 reviews)": 0.007,
                "Latin-square rerun, 150 new reviews": 7.68, "Latin-square run, 100 human-coded reviews": 7.04}
json.dump(out, open(O / "report2_data.json", "w"), indent=1, default=float)
# figure: median between-group residual correlation by step
fig, ax = plt.subplots(figsize=(9, 3.4)); cols = ["#bfbfbf", "#8faadc", "#2e5597", "#c55a11"]; w = 0.2; x = np.arange(6)
for j, (s, v) in enumerate(out["steps"].items()):
    ax.bar(x + (j - 1.5) * w, [v[c]["median"] for c in C6], w, color=cols[j], label=s[2:])
ax.set_xticks(x); ax.set_xticklabels([c.replace("Absence of ", "") for c in C6], fontsize=8); ax.set_ylabel("median residual correlation\n(between-group pairs, gold sample)", fontsize=8)
ax.axhline(0, color="black", lw=0.6); ax.legend(fontsize=7, ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.14)); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(FIG / "ci_steps.png", dpi=200); plt.close()
# figure: same vs different prompt
sp = pd.DataFrame(out["same_prompt"]).loc[C6]
fig, ax = plt.subplots(figsize=(7, 2.9))
ax.bar(x - 0.18, sp["different prompt"], 0.36, color="#8faadc", label=f"different prompt (n = {out['same_n']['different prompt']})")
ax.bar(x + 0.18, sp["same prompt"], 0.36, color="#c55a11", label=f"same prompt (n = {out['same_n']['same prompt']})")
ax.set_xticks(x); ax.set_xticklabels([c.replace("Absence of ", "") for c in C6], fontsize=8); ax.set_ylabel("residual correlation\nGPT-6 Luna vs GPT-5.4 mini", fontsize=8)
ax.legend(fontsize=7, frameon=False); ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig(FIG / "same_prompt.png", dpi=200); plt.close()
print(json.dumps(out["steps"], indent=0)[:1500]); print(out["nogold"])

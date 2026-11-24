"""Latin-square prompt design: on every review, the three prompted groups (Sonnet, Gemma, GPT = Luna + 5.4 mini)
get three DIFFERENT prompts (v2/v3/v4). The 6 orderings are used equally often and assigned to reviews at random.
GPT models share their group's prompt (within-group dependence is allowed, Egami & Shin Sec. 5.1). Qwen-FT keeps v1."""
import itertools, json, csv, random
from pathlib import Path
D = Path(__file__).resolve().parent.parent; F = D.parent / "11.16_humanAIcomparasion_finetune"
perms = list(itertools.permutations(["v2", "v3", "v4"]))
def make(ids, seed, path):
    rng = random.Random(seed); seq = [perms[i % 6] for i in range(len(ids))]; rng.shuffle(seq)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["sample_id", "sonnet", "gemma", "gpt"]); [w.writerow([i, *p]) for i, p in zip(ids, seq)]
new = [int(r["sample_id"]) for r in csv.DictReader(open(D / "sample_150.csv", encoding="utf-8-sig"))]
gold = [it["review_id"] for it in json.load(open(F / "data" / "dataset.json", encoding="utf-8"))["items"]]
make(new, 31, D / "outputs" / "latin_assignment_new.csv"); make(gold, 32, D / "outputs" / "latin_assignment_gold.csv"); print("ok")

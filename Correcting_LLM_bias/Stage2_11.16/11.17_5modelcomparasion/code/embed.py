"""Embed the 100 human-coded reviews and the 150 new reviews with OpenAI text-embedding-3-large.
Writes outputs/embeddings.npz (ids_gold, E_gold, ids_new, E_new) and records token usage / cost."""
import json, os, csv, urllib.request, numpy as np
from pathlib import Path
D = Path(__file__).resolve().parent.parent; F = D.parent / "11.16_humanAIcomparasion_finetune"
MODEL, PRICE = "text-embedding-3-large", 0.13  # USD per 1M tokens
key = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
gold = json.load(open(F / "data" / "dataset.json", encoding="utf-8"))["items"]
new = list(csv.DictReader(open(D / "sample_150.csv", encoding="utf-8-sig")))
texts = [("gold", it["review_id"], it["text"]) for it in gold] + [("new", int(r["sample_id"]), r["review_text"]) for r in new]

def embed(batch):
    body = json.dumps({"model": MODEL, "input": [t[:20000] for t in batch]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    d = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return [x["embedding"] for x in sorted(d["data"], key=lambda x: x["index"])], d["usage"]["total_tokens"]

vecs, tok = [], 0
for s in range(0, len(texts), 50):
    v, t = embed([x[2] for x in texts[s:s + 50]]); vecs += v; tok += t
V = np.array(vecs, dtype=np.float32); g = np.array([x[0] == "gold" for x in texts])
np.savez(D / "outputs" / "embeddings.npz", ids_gold=np.array([x[1] for x in texts if x[0] == "gold"]), E_gold=V[g],
         ids_new=np.array([x[1] for x in texts if x[0] == "new"]), E_new=V[~g])
json.dump({"model": MODEL, "texts": len(texts), "tokens": tok, "cost_usd": tok * PRICE / 1e6}, open(D / "outputs" / "embedding_cost.json", "w"), indent=1)
print(V.shape, tok, f"${tok * PRICE / 1e6:.4f}")

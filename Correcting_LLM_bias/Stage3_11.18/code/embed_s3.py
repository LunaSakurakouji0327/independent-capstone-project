"""Embed all 3,000 Stage 3 reviews with OpenAI text-embedding-3-large -> outputs/embeddings_s3.npz (unit_id, E)."""
import json, os, csv, urllib.request, numpy as np
from pathlib import Path
S3 = Path(__file__).resolve().parent.parent
key = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
rows = list(csv.DictReader(open(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig")))
vecs, tok = [], 0
for s in range(0, len(rows), 100):
    body = json.dumps({"model": "text-embedding-3-large", "input": [r["review_text"][:20000] for r in rows[s:s + 100]]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    vecs += [x["embedding"] for x in sorted(d["data"], key=lambda x: x["index"])]; tok += d["usage"]["total_tokens"]
np.savez(S3 / "outputs" / "embeddings_s3.npz", unit_id=np.array([r["unit_id"] for r in rows]), E=np.array(vecs, dtype=np.float32))
json.dump({"tokens": tok, "cost_usd": tok * 0.13 / 1e6}, open(S3 / "outputs" / "embedding_cost.json", "w")); print(len(vecs), tok, f"${tok * 0.13 / 1e6:.3f}")

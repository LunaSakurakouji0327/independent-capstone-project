"""Embed the 185 extra human-coded reviews (Yuhao + group) and save all 3,185 embeddings to outputs/embeddings_s3_v2.npz."""
import json, os, csv, urllib.request, numpy as np
from pathlib import Path
S3 = Path(__file__).resolve().parent.parent
key = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
rows = [r for r in csv.DictReader(open(S3 / "data" / "stage3_reviews_v2.csv", encoding="utf-8-sig")) if r["source"] in ("gold_yuhao", "gold_group")]
body = json.dumps({"model": "text-embedding-3-large", "input": [r["review_text"][:20000] for r in rows]}).encode()
req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
d = json.loads(urllib.request.urlopen(req, timeout=180).read()); V = [x["embedding"] for x in sorted(d["data"], key=lambda x: x["index"])]
Z = np.load(S3 / "outputs" / "embeddings_s3.npz")
np.savez(S3 / "outputs" / "embeddings_s3_v2.npz", unit_id=np.r_[Z["unit_id"], [r["unit_id"] for r in rows]], E=np.vstack([Z["E"], np.array(V, dtype=np.float32)]))
t = d["usage"]["total_tokens"]; print(len(V), t, f"${t * 0.13 / 1e6:.4f}")

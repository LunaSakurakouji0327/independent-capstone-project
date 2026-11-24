"""Check what the model assigns to the training target at initialisation."""
import os, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "hf_cache"))
sys.argv = [sys.argv[0], "none"]
import torch
import finetune_cv as F

it = F.ITEMS[0]; c = "Theme"
ex, _ = F.encode(it, c, True)
ids = ex["input_ids"]; nt = sum(1 for t in ex["labels"] if t != -100)
print("tail of sequence:", repr(F.tok.decode(ids[-12:])))
print("target ids:", ids[-nt:], [F.tok.decode([t]) for t in ids[-nt:]], "ID0/ID1:", F.ID0, F.ID1)
full = F.tok.apply_chat_template([{"role": "user", "content": "x"}, {"role": "assistant", "content": "0"}], tokenize=False, enable_thinking=False)
print("template with assistant turn ends:", repr(full[-60:]))

m = F.load_base(); m.eval()
x = torch.tensor([ids], device="cuda")
with torch.no_grad():
    lg_full = m(input_ids=x).logits[0].float()
    lg_keep = m(input_ids=x, logits_to_keep=nt + 1).logits[0].float()
L = len(ids)
for j in range(nt):
    pos = L - nt - 1 + j
    pr = torch.softmax(lg_full[pos], -1)
    top = torch.topk(pr, 5)
    print(f"predict token {j} ({F.tok.decode([ids[pos+1]])!r}): p={pr[ids[pos+1]].item():.4f}; top5 =", [(F.tok.decode([i]), round(v, 3)) for v, i in zip(top.values.tolist(), top.indices.tolist())])
print("full-logit loss:", torch.nn.functional.cross_entropy(lg_full[L - nt - 1:L - 1], torch.tensor(ids[-nt:], device="cuda")).item())
print("kept-logit loss:", torch.nn.functional.cross_entropy(lg_keep[:nt], torch.tensor(ids[-nt:], device="cuda")).item())
print("kept vs full max abs diff:", (lg_keep[:nt] - lg_full[L - nt - 1:L - 1]).abs().max().item())

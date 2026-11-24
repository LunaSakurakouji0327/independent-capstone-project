"""Find which training-mode setting inflates the loss."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "hf_cache"))
sys.argv = [sys.argv[0], "none"]
import torch
import finetune_cv as F
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

exs = [F.encode(it, c, True)[0] for it in F.ITEMS[:3] for c in F.C[:3]]


def loss_of(m, ex):
    x = torch.tensor([ex["input_ids"]], device="cuda")
    nt = sum(1 for t in ex["labels"] if t != -100)
    lg = m(input_ids=x, logits_to_keep=nt + 1).logits[0, :nt].float()
    return torch.nn.functional.cross_entropy(lg, torch.tensor(ex["input_ids"][-nt:], device="cuda")).item()


def avg(m, tag):
    with torch.no_grad():
        print(f"{tag:55s} mean loss {sum(loss_of(m, e) for e in exs)/len(exs):.4f}", flush=True)


m = F.load_base()
m.eval(); avg(m, "base, eval")
m.train(); avg(m, "base, train mode")
m.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); m.train(); avg(m, "base, train + grad ckpt")
m.gradient_checkpointing_disable()
m = prepare_model_for_kbit_training(m, use_gradient_checkpointing=True)
m.train(); avg(m, "after prepare_model_for_kbit_training, train")
m.eval(); avg(m, "after prepare_model_for_kbit_training, eval")
print("dtypes:", {n: p.dtype for n, p in m.named_parameters() if "norm" in n or "embed" in n or "lm_head" in n} and
      sorted({str(p.dtype) for n, p in m.named_parameters()}))
pm = get_peft_model(m, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=F.CFG["target_modules"], task_type="CAUSAL_LM"))
pm.train(); avg(pm, "with fresh LoRA, train")
pm.eval(); avg(pm, "with fresh LoRA, eval")

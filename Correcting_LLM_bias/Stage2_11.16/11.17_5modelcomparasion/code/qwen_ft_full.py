"""Train the final Qwen3-14B QLoRA adapter on ALL 100 human-coded reviews (2 epochs, chosen by Stage 2 1-vs-2-epoch
comparison; all other settings identical to the CV run), then label Stage3/sample_150.csv with prompt v1."""
import sys, os, json, math, time, random, csv
from pathlib import Path
B = Path(r"C:\Users\gujia\Downloads\books")
sys.path.insert(0, str(B / "Stage2_11.16" / "11.16_humanAIcomparasion_finetune" / "code"))
os.environ["EPOCHS"] = "2"
import finetune_cv as F
import torch
from peft import LoraConfig, get_peft_model
from transformers import get_cosine_schedule_with_warmup
import bitsandbytes as bnb
OUTD = B / "Stage2_11.16" / "11.17_5modelcomparasion" / "outputs"; CFG = F.CFG
assert CFG["epochs"] == 2
F.set_seed(CFG["seed"])
base = F.load_base()
base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); base.enable_input_require_grads()
exs = [F.encode(it, c, True)[0] for it in F.ITEMS for c in F.C if it["labels"][c] is not None]
model = get_peft_model(base, LoraConfig(r=CFG["lora_r"], lora_alpha=CFG["lora_alpha"], lora_dropout=CFG["lora_dropout"],
                                        target_modules=CFG["target_modules"], task_type="CAUSAL_LM"))
opt = bnb.optim.PagedAdamW8bit([p for p in model.parameters() if p.requires_grad], lr=CFG["lr"], weight_decay=0.0)
steps = math.ceil(len(exs) * CFG["epochs"] / CFG["grad_accum"])
sch = get_cosine_schedule_with_warmup(opt, int(steps * CFG["warmup_ratio"]), steps)
log = open(OUTD / "qwenft_training_log.jsonl", "w", encoding="utf-8")
model.train(); step, acc, run_loss, t0 = 0, 0, 0.0, time.time()
for ep in range(CFG["epochs"]):
    order = list(range(len(exs))); random.shuffle(order)
    for n, i in enumerate(order):
        ex = exs[i]; x = torch.tensor([ex["input_ids"]], device="cuda")
        nt = sum(1 for t in ex["labels"] if t != -100)
        lg = model(input_ids=x, logits_to_keep=nt + 1).logits[0, :nt].float()
        loss = torch.nn.functional.cross_entropy(lg, torch.tensor(ex["input_ids"][-nt:], device="cuda")) / CFG["grad_accum"]
        loss.backward(); run_loss += loss.item(); acc += 1
        if acc == CFG["grad_accum"] or (ep == CFG["epochs"] - 1 and n == len(order) - 1):
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sch.step(); opt.zero_grad(set_to_none=True); step += 1
            log.write(json.dumps({"step": step, "epoch": ep, "loss": round(run_loss * CFG["grad_accum"] / acc, 4)}) + "\n"); log.flush()
            if step % 20 == 0: print(f"step {step}/{steps} ({time.time()-t0:.0f}s)", flush=True)
            acc, run_loss = 0, 0.0
model.save_pretrained(OUTD / "qwenft_adapter_all100")
print(f"trained {step} steps on {len(exs)} examples in {time.time()-t0:.0f}s", flush=True)
rows = list(csv.DictReader(open(B / "Stage2_11.16" / "11.17_5modelcomparasion" / "sample_150.csv", encoding="utf-8-sig")))
items = [{"review_id": int(r["sample_id"]), "fold": None, "text": r["review_text"], "labels": {c: None for c in F.C}} for r in rows]
p = OUTD / "progress_qwenft.jsonl"
if p.exists(): p.unlink()
F.predict(model, items, "qwenft_all100_v1", p)
print("qwenft labelling finished", flush=True)

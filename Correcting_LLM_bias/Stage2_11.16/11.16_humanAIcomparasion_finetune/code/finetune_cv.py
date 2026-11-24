"""QLoRA fine-tuning of Qwen3-14B with 5-fold CV on the human-coded reviews.

python code/finetune_cv.py zeroshot   -> base model predictions on all 100 x 7 (no training)
python code/finetune_cv.py cv         -> for each fold: train LoRA on 4 folds, predict held-out fold
Resumable: folds already present in the predictions file are skipped.
"""
import os, sys, json, math, time, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "hf_cache"))
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

sys.path.insert(0, str(ROOT / "code"))
from prompts_v1 import prompts as PROMPTS

CFG = {
    "base_model": "unsloth/Qwen3-14B-bnb-4bit",  # Qwen3-14B, NF4 4-bit (bitsandbytes)
    "max_review_tokens": 768,
    "lora_r": 16, "lora_alpha": 32, "lora_dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "epochs": int(os.environ.get("EPOCHS", "2")), "lr": 1e-4, "grad_accum": 8, "warmup_ratio": 0.1, "seed": 42,
}
OUT = ROOT / os.environ.get("OUT_NAME", "outputs")
# early stopping: stop a fold when held-out log-loss rises PATIENCE evals in a row (0 = off)
PATIENCE = int(os.environ.get("PATIENCE", "0"))
OUT.mkdir(exist_ok=True)
data = json.load(open(ROOT / "data" / "dataset.json", encoding="utf-8"))
C, ITEMS, K = data["constructs"], data["items"], data["folds"]


def set_seed(s):
    random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


tok = AutoTokenizer.from_pretrained(CFG["base_model"])
ID0, ID1 = tok.convert_tokens_to_ids("0"), tok.convert_tokens_to_ids("1")


def build_prompt(text, construct):
    ids = tok(text, add_special_tokens=False)["input_ids"]
    truncated = len(ids) > CFG["max_review_tokens"]
    if truncated:
        text = tok.decode(ids[: CFG["max_review_tokens"]]) + " [...]"
    msg = [{"role": "user", "content": PROMPTS[construct].replace("{text}", text)}]
    p = tok.apply_chat_template(msg, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return p, truncated


def encode(item, construct, with_label):
    p, trunc = build_prompt(item["text"], construct)
    pid = tok(p, add_special_tokens=False)["input_ids"]
    if not with_label:
        return pid, trunc
    lab = str(item["labels"][construct])
    tid = tok(lab + "<|im_end|>", add_special_tokens=False)["input_ids"]
    return {"input_ids": pid + tid, "labels": [-100] * len(pid) + tid}, trunc


def load_base():
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    m = AutoModelForCausalLM.from_pretrained(CFG["base_model"], quantization_config=bnb, device_map={"": 0}, torch_dtype=torch.bfloat16, attn_implementation="sdpa")
    m.config.use_cache = False
    return m


@torch.no_grad()
def predict(model, items, tag, path):
    model.eval()
    with open(path, "a", encoding="utf-8") as f:
        for it in items:
            for c in C:
                pid, trunc = encode(it, c, False)
                x = torch.tensor([pid], device="cuda")
                logits = model(input_ids=x, logits_to_keep=1).logits[0, -1].float()
                two = torch.softmax(logits[[ID0, ID1]], -1)
                p1 = two[1].item()
                rec = {"review_id": it["review_id"], "construct": c, "fold": it["fold"], "pred": int(p1 >= 0.5), "p1": round(p1, 5),
                       "gold": it["labels"][c], "truncated": trunc, "run": tag}
                f.write(json.dumps(rec) + "\n")
            f.flush()


EVAL_EVERY = int(os.environ.get("EVAL_EVERY", "20"))  # held-out evaluation for the learning curve (monitoring only; training length stays fixed)


@torch.no_grad()
def eval_heldout(model, test):
    """Binary log-loss and accuracy on the held-out fold, using P(1) = softmax over the '0'/'1' logits."""
    was_training = model.training
    model.eval()
    losses, hits = [], []
    for it in test:
        for c in C:
            g = it["labels"][c]
            if g is None:
                continue
            pid, _ = encode(it, c, False)
            lg = model(input_ids=torch.tensor([pid], device="cuda"), logits_to_keep=1).logits[0, -1].float()
            lp = torch.log_softmax(lg[[ID0, ID1]], -1)
            losses.append(-lp[g].item()); hits.append(int(int(lp[1] > lp[0]) == g))
    if was_training:
        model.train()
    return sum(losses) / len(losses), sum(hits) / len(hits)


def done_folds(path):
    if not path.exists():
        return set()
    s = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l); s.setdefault(r["fold"], 0); s[r["fold"]] += 1
    return {k for k, n in s.items() if n == sum(1 for it in ITEMS if it["fold"] == k) * len(C)}


def main(mode):
    set_seed(CFG["seed"])
    t0 = time.time()
    base = load_base()
    print(f"model loaded in {time.time()-t0:.0f}s; VRAM {torch.cuda.memory_allocated()/2**30:.1f} GB", flush=True)

    if mode == "zeroshot":
        path = OUT / "predictions_zeroshot.jsonl"
        if path.exists(): path.unlink()
        predict(base, ITEMS, "zeroshot", path)
        print("zero-shot done", flush=True)
        return

    path = OUT / "predictions_finetuned.jsonl"
    log = open(OUT / "training_log.jsonl", "a", encoding="utf-8")
    json.dump(CFG, open(OUT / "finetune_config.json", "w"), indent=1)
    # NOTE: prepare_model_for_kbit_training() is deliberately NOT used: with this pre-quantized checkpoint it
    # up-casts parameters in a way that corrupts the model (answer-token loss 0.00 -> 2.8 even in eval mode).
    base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    base.enable_input_require_grads()
    folds = [0] if mode == "smoke" else range(K)
    for k in folds:
        if mode != "smoke" and k in done_folds(path):
            print(f"fold {k}: already done, skipping", flush=True); continue
        set_seed(CFG["seed"] + k)
        train = [it for it in ITEMS if it["fold"] != k]
        test = [it for it in ITEMS if it["fold"] == k]
        exs = [encode(it, c, True)[0] for it in train for c in C if it["labels"][c] is not None]
        lcfg = LoraConfig(r=CFG["lora_r"], lora_alpha=CFG["lora_alpha"], lora_dropout=CFG["lora_dropout"],
                          target_modules=CFG["target_modules"], task_type="CAUSAL_LM")
        model = get_peft_model(base, lcfg)
        import bitsandbytes as bnb
        opt = bnb.optim.PagedAdamW8bit([p for p in model.parameters() if p.requires_grad], lr=CFG["lr"], weight_decay=0.0)
        steps = math.ceil(len(exs) * CFG["epochs"] / CFG["grad_accum"])
        sch = get_cosine_schedule_with_warmup(opt, int(steps * CFG["warmup_ratio"]), steps)
        elog = open(OUT / "eval_log.jsonl", "a", encoding="utf-8")
        def log_eval(step):
            te = time.time(); l, a = eval_heldout(model, test)
            elog.write(json.dumps({"fold": k, "step": step, "heldout_logloss": round(l, 4), "heldout_acc": round(a, 4), "eval_seconds": round(time.time() - te, 1), "wall": time.time()}) + "\n"); elog.flush()
            print(f"fold {k} step {step}: held-out logloss {l:.4f} acc {a:.3f}", flush=True)
            return l
        hist, stop = [], False
        if mode != "smoke":
            log_eval(0)
        model.train()
        step, acc, run_loss, tf = 0, 0, 0.0, time.time()
        for ep in range(CFG["epochs"]):
            order = list(range(len(exs))); random.shuffle(order)
            for n, i in enumerate(order):
                ex = exs[i]
                x = torch.tensor([ex["input_ids"]], device="cuda")
                nt = sum(1 for t in ex["labels"] if t != -100)  # answer tokens at the end
                # only project the last nt+1 hidden states to the vocabulary (saves ~1-2 GB of logits)
                lg = model(input_ids=x, logits_to_keep=nt + 1).logits[0, :nt].float()
                tgt = torch.tensor(ex["input_ids"][-nt:], device="cuda")
                loss = torch.nn.functional.cross_entropy(lg, tgt) / CFG["grad_accum"]
                loss.backward(); run_loss += loss.item(); acc += 1
                if acc == CFG["grad_accum"] or (ep == CFG["epochs"] - 1 and n == len(order) - 1):
                    gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
                    opt.step(); sch.step(); opt.zero_grad(set_to_none=True)
                    step += 1
                    log.write(json.dumps({"fold": k, "step": step, "epoch": ep, "loss": round(run_loss * CFG["grad_accum"] / acc, 4), "grad_norm": round(gnorm, 4), "lr": sch.get_last_lr()[0], "wall": time.time()}) + "\n"); log.flush()
                    if mode != "smoke" and (step % EVAL_EVERY == 0 or step == steps):
                        hist.append(log_eval(step))
                        if PATIENCE and len(hist) > PATIENCE and all(hist[-j] > hist[-j-1] for j in range(1, PATIENCE + 1)):
                            print(f"fold {k}: EARLY STOP at step {step} (held-out logloss rose {PATIENCE} evals in a row)", flush=True)
                            stop = True; break
                    if step % 10 == 0 or mode == "smoke":
                        print(f"fold {k} step {step}/{steps} loss {run_loss*CFG['grad_accum']/acc:.4f} grad_norm {gnorm:.3f} ({time.time()-tf:.0f}s)", flush=True)
                    acc, run_loss = 0, 0.0
                    if mode == "smoke" and step >= 8:
                        print("smoke test finished", flush=True); return
            if stop: break
        model.save_pretrained(OUT / "adapters" / f"fold{k}")
        predict(model, test, f"fold{k}", path)
        print(f"fold {k}: trained {step}/{steps} steps on {len(exs)} examples in {time.time()-tf:.0f}s; predicted {len(test)} reviews", flush=True)
        del opt
        base = model.unload()  # drop LoRA layers, keep the 4-bit base for the next fold
        torch.cuda.empty_cache()
    print("CV done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])

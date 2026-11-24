"""Label the 2,900 new Stage 3 reviews with the final fine-tuned Qwen3-14B adapter (trained on all 100 gold reviews, 2 epochs, prompt v1).
For the 100 gold reviews the out-of-fold 5-fold CV predictions are used instead (the final adapter has seen their labels,
so its predictions on them would be in-sample and invalid for the DSL correction).
Writes outputs/progress_qwenft.jsonl (unit_id, construct, label, p1). Resumable per review."""
import sys, os, json, csv, time
from pathlib import Path
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; F = B / "Stage2_11.16" / "11.16_humanAIcomparasion_finetune"
sys.path.insert(0, str(F / "code")); os.environ["EPOCHS"] = "2"
import finetune_cv as FT
import torch
from peft import PeftModel
OUTP = S3 / "outputs" / "progress_qwenft.jsonl"
done = set()
if OUTP.exists():
    done = {json.loads(l)["unit_id"] for l in open(OUTP, encoding="utf-8")}
EXTRA = "extragold" in sys.argv[1:]  # Yuhao + group-coded reviews: not in the adapter's training data, so its predictions are out of sample
if EXTRA: OUTP = S3 / "outputs" / "extragold_qwenft.jsonl"; done = {json.loads(l)["unit_id"] for l in open(OUTP, encoding="utf-8")} if OUTP.exists() else set()
rows = [r for r in csv.DictReader(open(S3 / "data" / ("stage3_reviews_v2.csv" if EXTRA else "stage3_reviews.csv"), encoding="utf-8-sig"))
        if r["source"] in (("gold_yuhao", "gold_group") if EXTRA else ("new",)) and r["unit_id"] not in done]
print("to label:", len(rows), flush=True)
base = FT.load_base(); model = PeftModel.from_pretrained(base, str(B / "Stage2_11.16" / "11.17_5modelcomparasion" / "outputs" / "qwenft_adapter_all100")); model.eval()
t0 = time.time()
with open(OUTP, "a", encoding="utf-8") as f, torch.no_grad():
    if not done and not EXTRA:   # gold: out-of-fold CV predictions
        for r in map(json.loads, open(F / "outputs" / "predictions_finetuned.jsonl", encoding="utf-8")):
            f.write(json.dumps({"unit_id": f"G{r['review_id']}", "construct": r["construct"], "label": str(r["pred"]), "p1": r["p1"], "prompt": "v1", "source": "5-fold CV"}) + "\n")
    for n, r in enumerate(rows, 1):
        it = {"text": r["review_text"]}
        for c in FT.C:
            pid, trunc = FT.encode(it, c, False)
            lg = model(input_ids=torch.tensor([pid], device="cuda"), logits_to_keep=1).logits[0, -1].float()
            p1 = torch.softmax(lg[[FT.ID0, FT.ID1]], -1)[1].item()
            f.write(json.dumps({"unit_id": r["unit_id"], "construct": c, "label": str(int(p1 >= 0.5)), "p1": round(p1, 5), "prompt": "v1", "truncated": trunc, "source": "final adapter"}) + "\n")
        f.flush()
        if n % 200 == 0: print(f"{n}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)
print("qwenft finished", flush=True)

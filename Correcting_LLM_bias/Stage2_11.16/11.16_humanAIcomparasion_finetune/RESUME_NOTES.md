# Stage 2 fine-tuning: resume notes (written 2026-11-16 14:30)

## State at reboot
- Task: QLoRA fine-tune Qwen3-14B (unsloth/Qwen3-14B-bnb-4bit) on human_coding_100_finished.xlsx,
  stratified 5-fold CV (80 train / 20 test per fold), then 500-bootstrap evaluation and a PDF report.
- Done: zero-shot baseline (outputs/predictions_zeroshot.jsonl), fold 0 and fold 1 (outputs/predictions_finetuned.jsonl,
  outputs/adapters/fold0, fold1). Training log: outputs/training_log.jsonl.
- Remaining: folds 2, 3, 4 (fold numbering 0-based in code; figures use 1-based names).
- outputs/_invalid_run_prepare_kbit/ = an earlier broken run (prepare_model_for_kbit_training corrupted the model). Do not use.

## Why the reboot
dwm.exe held ~4.3 GB of the RTX 5070's 12 GB, so training spilled into shared memory (~150 s/step instead of ~24 s/step).
Monitor was moved to the motherboard (AMD iGPU) port; reboot frees the NVIDIA memory.

## To resume
1. Check GPU is free: `nvidia-smi` (should show ~1 GB used or less before training).
2. From this folder: `venv\Scripts\python code\finetune_cv.py cv`
   - Skips completed folds automatically; from fold 2 on, logs held-out log-loss/accuracy every 20 steps to outputs/eval_log.jsonl.
3. During fold 2, plot curves: `venv\Scripts\python code\plot_progress.py` -> outputs/figures/learning_curve_fold3.png (user wants to see these).
4. After all folds: `venv\Scripts\python code\evaluate.py` (500 bootstrap, metrics.xlsx, figures), then build the PDF report.

## Settings (fixed for all folds)
LoRA r16/alpha32/dropout 0.05 on all attention+MLP projections; lr 1e-4 cosine, warmup 10%; 2 epochs; batch 1 x grad-accum 8 (140 steps);
review truncated at 768 tokens; prompt v1 (code/prompts_v1.py); loss on answer tokens only; no prepare_model_for_kbit_training.

## DONE (2026-11-16 evening)
All 5 folds trained after reboot (~10 s/step, 26 min/fold). evaluate.py run (needs PYTHONIOENCODING=utf-8 on this console).
Report: Stage2_FineTune_Report.pdf (+ report/Stage2_FineTune_Report.docx), built by
`venv\Scripts\python code\report_extras.py` then `node report\make_stage2_report.js raw_stage2.docx` + report\export.ps1.
Headline: macro kappa FT 0.47 vs zero-shot 0.36 (diff 0.10, CI 0.00-0.21); ~= GPT-4o 0.46 / Sonnet 0.45.

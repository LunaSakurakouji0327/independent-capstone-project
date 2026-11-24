# Wait for Gemma (GPU) to finish, then: fine-tuned Qwen -> gpt-6-luna -> gpt-5.4-mini (GPT last, as requested)
cd /c/Users/gujia/Downloads/books/Stage2_11.16/11.17_5modelcomparasion
PY=../11.16_humanAIcomparasion_finetune/venv/Scripts/python; export PYTHONIOENCODING=utf-8
until grep -qE "finished|STOPPED" outputs/run_gemma.log 2>/dev/null; do sleep 30; done
ollama stop gemma3:12b >/dev/null 2>&1; sleep 10
echo "qwenft start $(date)"; $PY -u code/qwen_ft_full.py > outputs/run_qwenft.log 2>&1; echo "qwenft exit $? $(date)"
$PY -u code/label.py luna > outputs/run_luna.log 2>&1; echo "luna exit $? $(date)"
$PY -u code/label.py mini > outputs/run_mini.log 2>&1; echo "mini exit $? $(date)"

#!/bin/bash
# wait for fold 1 predictions, stop the old process, then restart from fold 2 with learning-curve logging
cd "/c/Users/gujia/Downloads/books/Stage2_11.16"
while true; do
  n=$(python -c "import json;print(sum(1 for l in open('outputs/predictions_finetuned.jsonl') if json.loads(l)['fold']==1))" 2>/dev/null || echo 0)
  [ "$n" -ge 140 ] && break
  timeout 30 tail -f /dev/null
done
echo "fold 1 done at $(date); stopping old process 39196"
powershell -NoProfile -c "Stop-Process -Id 39196 -Force -ErrorAction SilentlyContinue"
timeout 15 tail -f /dev/null
python -c "
import json
ls=[l for l in open('outputs/training_log.jsonl') if json.loads(l)['fold']<=1]
open('outputs/training_log.jsonl','w').writelines(ls); print('training log trimmed to', len(ls), 'lines')"
echo "restarting at $(date)"
PYTHONIOENCODING=utf-8 ./venv/Scripts/python code/finetune_cv.py cv 2>&1 | grep -v -i "warn\|symlink\|xet\|it/s\]\|torch.empty"

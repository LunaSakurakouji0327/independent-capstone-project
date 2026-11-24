#!/bin/bash
# wait for fold 1 predictions, stop training, tidy logs, reboot Windows (authorized by user on 2026-11-16)
cd "/c/Users/gujia/Downloads/books/Stage2_11.16"
while true; do
  n=$(python -c "import json;print(sum(1 for l in open('outputs/predictions_finetuned.jsonl') if json.loads(l)['fold']==1))" 2>/dev/null || echo 0)
  [ "$n" -ge 140 ] && break
  timeout 30 tail -f /dev/null
done
echo "fold 1 done at $(date); stopping training process 39196"
powershell -NoProfile -c "Stop-Process -Id 39196,19984 -Force -ErrorAction SilentlyContinue"
timeout 15 tail -f /dev/null
python -c "
import json
ls=[l for l in open('outputs/training_log.jsonl') if json.loads(l)['fold']<=1]
open('outputs/training_log.jsonl','w').writelines(ls); print('training log trimmed to', len(ls), 'lines')"
echo "fold 0 and fold 1 complete; reboot issued at $(date)" >> outputs/STATUS.txt
shutdown /r /t 60 /c "Fine-tuning fold 1 finished. Rebooting to free GPU memory. Run 'shutdown /a' to cancel."

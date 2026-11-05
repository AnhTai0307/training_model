#!/usr/bin/env bash
# Train PhoBERT + CRF cho task jobner (SKILL/TIME/LOC), rồi dự đoán + báo cáo trên test và test_hard.
# Chạy từ bất kỳ đâu: bash train_crf.sh   (biến môi trường PYTHON để đổi trình thông dịch)
#
# --overwrite_data BẮT BUỘC: file cache data_dir/*.cached không phân biệt softmax/crf, dùng nhầm cache
#   của kiến trúc khác sẽ lỗi "mask of the first timestep must all be on".
# Không chạy song song 2 script train trên cùng data_dir (dùng chung file cache).
# --early_stop 5: dừng khi 6 epoch liên tiếp BIO-macro-F1 (token-level, tính cả O) trên dev không tăng.
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=${PYTHON:-python}
ARCH=crf
OUT=outputs/${ARCH}

$PYTHON VPhoBertTagger/main.py train --task jobner --run_test \
  --data_dir data_dir --model_name_or_path vinai/phobert-base --model_arch ${ARCH} \
  --output_dir ${OUT} --max_seq_length 128 --train_batch_size 32 --eval_batch_size 32 \
  --learning_rate 3e-5 --epochs 30 --early_stop 5 --overwrite_data

for SPLIT in test test_hard; do
  $PYTHON data_build/predict_conll.py ${OUT}/best_model.pt data_dir/${SPLIT}.txt ${OUT}/pred_${SPLIT}.txt
  $PYTHON data_build/eval_report.py ${OUT}/pred_${SPLIT}.txt data_dir/${SPLIT}_meta.jsonl | tee ${OUT}/report_${SPLIT}.txt
done

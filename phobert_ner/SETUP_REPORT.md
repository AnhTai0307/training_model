# SETUP_REPORT — NER tiếng Việt (SKILL / TIME / LOC) với VPhoBertTagger

Ngày: 2026-10-28 · Máy: Windows 11, Python 3.12.10, **chỉ CPU** (không có GPU), Java 1.8.0_401.
Trạng thái: pipeline đã chạy được trọn vẹn ở mức **smoke test** (1 epoch, 40 câu train). **Chưa train đầy đủ.**

---

## 0. Tóm tắt nhanh

| Hạng mục | Kết quả |
|---|---|
| Repo | `VPhoBertTagger/` (đã clone từ trước, commit `ab2e63d`); sửa 6 file, +34/−12 dòng — xem §2 |
| Môi trường | `requirements.txt` gốc **không cài được** trên Python 3.12 → bộ chạy được ở `requirements_working.txt` |
| Dữ liệu | train 1503 / dev 185 / test 184 / test_hard 102 câu; template chiếm 39.1% train; 0 lỗi validate |
| Baseline từ điển | F1 = **0.982** trên test, **0.855** trên test_hard |
| Smoke test | softmax, crf, lstm_crf: train → `--run_test` → predict ra file → báo cáo: **đều chạy được** (sau khi sửa 3 bug) |
| Ổ đĩa | **C: đầy 100%** (còn ~1.3GB) — không đủ để train đầy đủ tại máy; mỗi checkpoint ~515MB → dùng Colab |

---

## 1. Cấu trúc thư mục

```
phobert_ner/
├── .venv/                      # virtualenv (đã có sẵn, trống; mình cài thư viện vào đây)
├── VPhoBertTagger/             # repo gốc + các sửa đổi ở §2
├── vncorenlp/                  # VnCoreNLP-1.2.jar (py_vncorenlp), VnCoreNLP-1.1.1.jar (predictor của repo)
│   └── models/wordsegmenter/   # vi-vocab, wordsegmenter.rdr  (chỉ cần annotator wseg)
├── data_build/
│   ├── lexicon.py              # từ điển SKILL (45 khái niệm) / TIME (12) / LOC (8) + biến thể
│   ├── templates.py            # 9 họ template, 99 pattern (mỗi họ ≥ 10 cách diễn đạt)
│   ├── handwritten.txt         # 298 câu gốc viết tay (markup [text|TAG] / [text|TAG|neg])
│   ├── test_hard_raw.txt       # 106 câu test_hard viết tay riêng (102 căn được)
│   ├── common.py               # chuẩn hoá, bỏ dấu, parse markup, tách từ, căn span
│   ├── build_data.py           # pipeline sinh dữ liệu → data_dir/
│   ├── validate_data.py        # kiểm tra định dạng + thống kê
│   ├── baseline_dict.py        # baseline từ điển + regex
│   ├── eval_report.py          # báo cáo F1 entity-level theo loại + theo nhóm
│   ├── predict_conll.py        # (thêm) xuất file dự đoán của model — repo không có chức năng này
│   ├── conll_io.py             # đọc/ghi CoNLL dùng chung
│   ├── alignment_failures.jsonl# 58 câu không căn được span (đã loại)
│   └── all_sentences.jsonl     # toàn bộ câu + token + nhãn + nguồn (để duyệt tay)
├── data_dir/
│   ├── train.txt dev.txt test.txt test_hard.txt      # 4 cột, tab, câu cách nhau dòng trống
│   ├── *_meta.jsonl            # metadata cùng thứ tự câu: nguồn, has_accent, negated, entities...
│   └── preds/baseline_*.txt    # dự đoán baseline (token \t gold \t pred)
├── train_softmax.sh  train_crf.sh  train_lstm_crf.sh
├── notebook_colab.ipynb
├── requirements_working.txt
├── repo_changes.diff           # `git diff` đầy đủ của repo
└── logs/                       # log do repo tự tạo khi chạy predict/test
```

---

## 2. Các thay đổi trong repo

`git diff` đầy đủ: `repo_changes.diff`. Lưu ý: **3 thay đổi đầu đã có sẵn trong working tree trước khi mình bắt đầu** (chưa commit, không phải mình viết). Mình đã đọc và giữ nguyên vì chúng đúng.

| # | File:dòng | Thay đổi | Lý do | Ai sửa |
|---|---|---|---|---|
| 1 | `arguments.py:39-41` | thêm `'jobner'` vào `choices` của `--task` | đăng ký task mới | có sẵn |
| 2 | `constant.py:25`, `constant.py:77-82` | `LABEL2ID_JOBNER` (đúng 7 nhãn) + mục `'jobner'` trong `LABEL_MAPPING` với `header=['token','pos','chunk','ner']` | danh sách nhãn + vị trí cột | có sẵn |
| 3 | `trainer.py:194` | dev loader `dtype='test'` → `dtype='dev'` | code gốc chọn model / early-stop **trên tập test** (rò rỉ test); sửa để dùng `dev.txt` | có sẵn |
| 4 | `dataset.py:44`; `trainer.py:114,116,212,214,304,306`; `predictor.py:28,30` | thêm `weights_only=False` vào mọi `torch.load` | torch ≥ 2.6 đổi mặc định → lỗi thật khi chạy: `_pickle.UnpicklingError: Weights only load failed ... GLOBAL argparse.Namespace was not an allowed global`. Checkpoint/cache do chính pipeline tạo nên tin cậy được | mình |
| 5 | `models/phobert.py:45-49` (PhoBertCrf), `:83-87` (PhoBertLstmCrf) | ghi đè `_init_weights` để gọi `reset_parameters()` cho `CRF` / `nn.LSTM` | transformers mới tắt `torch.nn.init` khi dựng model ⇒ đo được sau `from_pretrained`: CRF ≈ 0 hoặc rác (`7.7e-21`), LSTM **toàn 0**; lần smoke đầu loss CRF = **8 063 929 344**. Sau sửa: CRF ∈ ±0.1, LSTM ∈ ±0.051, loss CRF = 138, trọng số RoBERTa pretrained không đổi | mình |
| 6 | `predictor.py:92-93` | `label_masks = valid_ids` → `label_marks if self.use_crf else valid_ids` | lỗi thật khi predict lstm_crf: `RuntimeError: start (128) + length (1) exceeds dimension size (128)` (với CRF `valid_ids` chứa vị trí 1,2,3… nên `sum()` vượt 128). Giờ giống hệt `processor.py` lúc train | mình |

**Không sửa (cố ý), nhưng cần biết:**
- `main.py test` **hỏng sẵn**: `trainer.py:118` dùng `args.model_arch` mà `get_test_argument()` (`arguments.py:15`) không có → đã chạy thử: `AttributeError: 'Namespace' object has no attribute 'model_arch'` (dòng 139 và 159 còn lỗi `num_workers`/`task` tương tự). Không cần vì `--run_test` trong lệnh train + `predict_conll.py` thay thế.
- Cache `data_dir/*.cached` (`dataset.py:39`) **không phân biệt kiến trúc** → dùng cache của softmax cho crf sẽ lỗi `ValueError: mask of the first timestep must all be on` (đã gặp thật). Script train luôn có `--overwrite_data`; không chạy 2 train song song trên cùng `data_dir`.
- `processor.py:35,117`: `data.fillna(method="ffill")` → FutureWarning ở pandas 2.2 (kết quả không được gán nên vô hại); có thể lỗi ở pandas 3 (**chưa kiểm chứng**) → notebook tự hạ pandas < 3.
- `bert.py`/`vibert.py` có thể bị cùng lỗi khởi tạo CRF như #5 — **chưa kiểm tra**, không dùng trong đồ án.
- Model selection dùng **BIO macro-F1 mức token, tính cả nhãn O** (`trainer.py:72-75`), không phải F1 mức thực thể.

---

## 3. Trả lời 4 câu hỏi Bước 1 (kèm bằng chứng)

**a. Có bắt buộc 4 cột không?** — *Không bắt buộc về mặt logic, nhưng số cột phải khớp `header` của task.*
`processor.py:103 convert_word_segment_examples_features` đọc file bằng `pd.read_csv(..., delimiter='\t', names=header_names)` (`:112-116`) rồi **chỉ dùng** `row.token` (`:120`) và `row.ner` (`:121`); `pos`/`chunk` không bao giờ được đọc. Vị trí cột `ner` do `LABEL_MAPPING[task]['header']` quyết định (vd. `vlsp2018_l1` dùng `['token','ner','tmp1','tmp2']`). Task `jobner` đang để header 4 cột ⇒ file phải có 4 cột với nhãn ở cột 4. Mình giữ 4 cột (đúng định dạng README), **điền `_` giả cố định cho pos và chunk**.
Bẫy ngầm của `read_csv` (validate_data.py đã kiểm tra): token `NA`, `null`, `None`, `nan`… thành NaN và bị coi là **ranh giới câu**; dấu `"` làm lệch quote; 2 dòng trống liên tiếp tạo câu rỗng (với CRF sẽ `raise` lỗi).

**b. Nhãn định nghĩa ở đâu, thêm task mới thế nào?**
`constant.py`: danh sách `LABEL2ID_*` + dict `LABEL_MAPPING[task] = {label2id, id2label, header}`; `arguments.py:39 --task choices`. Trainer lấy `LABEL_MAPPING[args.task]['label2id']` (`trainer.py:177`) và `num_labels=len(label2id)` (`:200-202`). Thêm task = 3 chỗ: hằng số nhãn, mục `LABEL_MAPPING`, `choices`. Thứ tự trong `LABEL2ID_JOBNER` = id lớp; `'O'` phải ở id 0 vì processor đệm nhãn bằng 0 (`tag_ids.extend([0] * ...)`).

**c. predict/demo có tự tách từ câu thô không?** — **Có** (đã chạy thật).
`predictor.py:19` khởi động `VnCoreNLP("vncorenlp/VnCoreNLP-1.1.1.jar", annotators="wseg")` (gói `vncorenlp` cũ); `preprocess()` (`:44-50`) gọi `normalize_text()` rồi `rdrsegmenter.tokenize()`. `demo.py` dùng cùng `ViTagger`. Điều kiện: cần Java, và **chạy từ thư mục chứa `vncorenlp/`** (đường dẫn tương đối) — tức thư mục gốc `phobert_ner/`. Đã chạy `main.py predict` với câu "tôi giỏi tiếng Anh, rảnh vào tối và ở Hải Châu": nạp VnCoreNLP + model thành công, in kết quả (rỗng vì model smoke chỉ 1 epoch).
Đã so sánh tách từ VnCoreNLP-1.1.1 (predictor) với VnCoreNLP-1.2 (`py_vncorenlp`, dùng sinh dữ liệu) trên **toàn bộ 1974 câu**: **0 câu khác nhau**.

**d. requirements.txt có ghim bản cũ / xung đột Python 3.12 không?** — **Có, cài không được.**
Ghim `torch~=1.8.0`, `transformers~=4.18.0`, `pandas~=1.3.5`, `scikit-learn~=1.0.2`, `matplotlib~=3.5.2`, `streamlit~=1.10.0`… Lỗi thật (`pip install --dry-run -r requirements.txt`):
`ERROR: Could not find a version that satisfies the requirement torch~=1.8.0 (from versions: 2.2.0, ..., 2.14.1)`.
(`scikit-learn` còn bị ghi trùng 2 lần.) Bộ chạy được: `requirements_working.txt` (torch 2.7.1 CPU, transformers 4.46.3, pandas 2.2.3, …). Nâng phiên bản kéo theo 2 bug ở §2 (#4, #5).

**Các lỗi môi trường khác gặp phải:**
- `py_vncorenlp.download_model()` lỗi trên Windows: `FileNotFoundError: [WinError 2] ... 'VnCoreNLP-1.2.jar'` vì nó gọi `wget` qua `os.system`. Đã tải thủ công bằng `curl` đúng các URL trong code của nó. (Trên Colab/Linux `wget` có sẵn.)
- `py_vncorenlp.VnCoreNLP()` **tự `os.chdir()`** sang thư mục model → `common.Segmenter` trả lại cwd; mọi script dùng đường dẫn tuyệt đối.
- Console Windows (cp1258) không in được tiếng Việt → chạy với `PYTHONIOENCODING=utf-8`.
- Không cần `underthesea`: `py_vncorenlp` dùng được.

---

## 4. Dữ liệu

### 4.1 Quy ước
- **Chuẩn hoá dấu: kiểu CŨ** (`hòa → hoà`, `thùy → thuỳ`, `ủy → uỷ`). Mình dùng **đúng hàm `normalize_text` của repo** (`helper.py`), vì `predictor.py:45` gọi hàm này lúc suy luận ⇒ train và predict cùng quy ước. (Ngược với ví dụ "hoà → hòa" trong đề bài — đổi được dễ dàng nếu bạn muốn, nhưng khi đó phải sửa cả predictor.) Trước đó áp NFC; `"` → `”`.
- **Gán nhãn:** SKILL = lõi kỹ năng (mức độ "giỏi/thành thạo/cơ bản" là O; điểm "6.5", "750" là O; "IELTS" là SKILL). TIME gồm cả "buổi/ca/sau/từ…đến…"; "vào/rảnh" là O. LOC = tên địa danh hành chính (7 quận/huyện + "Đà Nẵng"), không gồm "quận/huyện/ở/gần"; tên trường, đường, bãi biển là O. Các mục nối bằng "và"/"," là thực thể riêng; khoảng liền mạch ("từ 18h đến 22h", "thứ 2 đến thứ 6") là 1 thực thể. "gia sư", "phục vụ", "bán hàng"… gán SKILL theo từ điển đề bài.
- **Phủ định:** thực thể vẫn gán nhãn bình thường; cờ `negated: true` chỉ nằm trong `*_meta.jsonl`.

### 4.2 Cách sinh
1. 298 câu gốc viết tay (có dấu, không dấu, teencode, không thực thể, phủ định, mức độ, nhiều thực thể, câu dài).
2. Tăng cường câu viết tay: 3 bản **đổi thực thể trong cùng nhóm** (ngôn ngữ↔ngôn ngữ, buổi↔buổi…) + 45% có thêm bản **bỏ dấu toàn câu**. Cùng nhóm với câu gốc.
3. Template: 99 pattern × ≤ 8 câu; ≈ 30% bỏ dấu. Mỗi pattern là một nhóm.
4. Chuẩn hoá → tách từ VnCoreNLP-1.2 → căn span vào token (khớp chuỗi sau NFC). Không căn được ⇒ vào `alignment_failures.jsonl`, **không đoán nhãn**.
5. Khử trùng lặp toàn cục (lower-case) — loại 35 câu.
6. Chia 80/10/10 **theo nhóm**, riêng cho nguồn viết tay và template (seed 13). Số nhóm nằm ở > 1 tập: **0**. test_hard trùng nguyên văn với train: **0**.

### 4.3 Thống kê (`python data_build/validate_data.py`)

| tập | số câu | token | SKILL | TIME | LOC | không thực thể | không dấu | có phủ định | lỗi |
|---|---|---|---|---|---|---|---|---|---|
| train | 1503 | 14475 | 1361 | 912 | 651 | 4.2% | 31.3% | 14.2% | 0 |
| dev | 185 | 1825 | 180 | 96 | 73 | 8.6% | 26.5% | 4.9% | 0 |
| test | 184 | 1860 | 142 | 130 | 87 | 4.9% | 26.6% | 14.1% | 0 |
| test_hard | 102 | 1119 | 90 | 64 | 42 | 3.9% | 20.6% | 26.5% | 0 |

Tỉ lệ template: train 39.1%, dev 40.0%, test 38.6% (yêu cầu ≤ 50%).

**Lỗi căn span: 58 câu** (54 của train/dev/test — 6 câu gốc + 48 câu tăng cường/template; 4 câu test_hard):
- 27 — dấu chấm cuối câu bị VnCoreNLP dính vào từ viết tắt / khung giờ: `T.Khê.`, `8h-12h.`
- 19 — câu không dấu: "son" bị gộp với từ trước: `o_son tra`, `gan_son tra`, `vuc_son tra`
- 7 — gộp từ sai ở câu có dấu: `tiếng Nhật_trình_độ`, `làm_tin học`, `chiều_tối`
- 5 — `q.Hải châu` thành một token

⚠️ Hệ quả: **"son tra" không dấu gần như vắng mặt trong dữ liệu**, và vì lỗi tách từ cũng xảy ra lúc suy luận, model mức token **không thể** trích đúng "ở son tra" không dấu. Đây là giới hạn của bộ tách từ, không phải của model.

---

## 5. Baseline từ điển + regex (`python data_build/baseline_dict.py`)

So khớp dài nhất trên token; token có dấu so khớp chính xác, token không dấu thì bỏ dấu cả hai phía; regex cho khung giờ; "toi"/"sang" không dấu chỉ nhận khi đứng sau từ gợi ý thời gian (tránh nhầm "tôi"). seqeval, mức thực thể:

| | test P / R / F1 | test_hard P / R / F1 |
|---|---|---|
| SKILL | 0.993 / 0.993 / 0.993 | 0.984 / **0.700** / 0.818 |
| TIME | 0.969 / 0.946 / 0.957 | 0.810 / 0.797 / 0.803 |
| LOC | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| **micro** | **0.986 / 0.978 / 0.982** | **0.923 / 0.796 / 0.855** |
| nhóm có dấu (F1) | 0.982 (135 câu) | 0.829 (81 câu) |
| nhóm không dấu (F1) | 0.982 (49 câu) | 0.949 (21 câu) |
| nhóm phủ định (F1) | 0.981 (26 câu) | 0.966 (27 câu) |
| câu không thực thể | 9/9 sạch | 3/4 sạch (1 thực thể thừa) |

⚠️ **Diễn giải quan trọng:** F1 0.98 trên `test` **không có nghĩa là bài toán dễ**. Thực thể trong train/dev/test đều lấy từ cùng từ điển (qua đổi thực thể và template), nên `test` gần như là một tập "đóng" — đo khả năng nhớ từ điển. **Thước đo có ý nghĩa là `test_hard`**, nhất là nhóm OOV (20 câu có thực thể ngoài từ điển: "tiếng Đức", "Figma", "giờ hành chính"…). Model PhoBERT chỉ đáng giá nếu **vượt baseline trên test_hard**. Nếu model trên test chỉ ngang baseline thì cũng là điều dễ hiểu.

---

## 6. Lệnh train và smoke test

- `train_softmax.sh`, `train_crf.sh`, `train_lstm_crf.sh`: `--task jobner --model_name_or_path vinai/phobert-base --max_seq_length 128 --learning_rate 3e-5 --epochs 30 --early_stop 5 --run_test --overwrite_data`, batch 32. Sau khi train, script tự chạy `predict_conll.py` + `eval_report.py` cho test và test_hard → `outputs/<arch>/report_*.txt`. `--early_stop 5` = dừng sau 6 epoch liên tiếp không tăng (`trainer.py`: `cumulative_early_steps > early_stop`).
- `notebook_colab.ipynb`: GPU check → upload zip/Drive → cài Java → cài thư viện (giữ torch CUDA của Colab) → tải VnCoreNLP bằng đường dẫn tuyệt đối → validate + baseline → train 3 kiến trúc → so sánh → predict câu thô → lưu về Drive.

**Smoke test** (CPU, 40 câu train / 20 dev / 20 test, 1 epoch, batch 8):

| arch | train loss | `--run_test` | `predict_conll.py` | mã hoá train = predict |
|---|---|---|---|---|
| softmax | 1.856 | OK | OK | 20/20 câu giống |
| crf | 138.0 (trước sửa #5: 8.06e9) | OK | OK | 20/20 |
| lstm_crf | 139.7 | OK | OK (trước sửa #6: RuntimeError) | 20/20 |

F1 ≈ 0 sau 1 epoch trên 40 câu là **bình thường** — smoke test chỉ chứng minh pipeline chạy. Mỗi epoch ~20–35 giây trên CPU với 40 câu ⇒ train đầy đủ trên CPU máy này không thực tế, cộng thêm ổ đĩa đầy. Các checkpoint smoke đã được xoá để giải phóng chỗ.

Chưa chạy: 3 script `train_*.sh` nguyên vẹn (vì đó là train đầy đủ); `main.py demo` (chưa cài streamlit).

---

## 7. ✅ DANH SÁCH VIỆC BẠN PHẢI TỰ LÀM

1. **Duyệt tay `data_dir/test_hard.txt` (102 câu) trước khi tin bất kỳ con số nào trên test_hard.** Đối chiếu với `data_build/test_hard_raw.txt` (dễ đọc hơn). Mình gán nhãn một mình, không có người thứ hai kiểm tra. Chú ý các câu có quyết định gây tranh cãi: "biển Mỹ Khê" (O), "Toán"/"Lý" (SKILL), "giao báo", "bán bánh mì", "bảo vệ" (SKILL), "ngay cuối tuần này" (TIME cả cụm), "T2, T4 sau 17h" (tách thực thể).
2. **Kiểm tra ngẫu nhiên ≥ 100 câu train** — mở `data_build/all_sentences.jsonl` (có text + token + nhãn + nguồn). Những lỗi đã biết cần để ý: bản đổi thực thể đôi khi **gượng về nghĩa** (vd "biết chơi hát", "làm làm bánh", "cuối tuần thứ 2 đến thứ 6") — nhãn vẫn đúng nhưng câu không tự nhiên.
3. **Duyệt `handwritten.txt` (298 câu gốc)** — mọi câu tăng cường đều kế thừa nhãn của câu gốc; một lỗi ở đây nhân lên ~4 lần.
4. **Quyết định các quy ước còn mở** (§4.1): kiểu dấu cũ hay mới; LOC có gồm phường/đường/địa danh không; "gia sư/phục vụ" là SKILL hay nên tách nhãn công việc; IELTS có gồm điểm số không. Sửa xong chỉ cần chạy lại `build_data.py`.
5. **Xem `data_build/alignment_failures.jsonl` (58 câu)** — nếu muốn giữ, sửa câu trong `handwritten.txt` (vd. bỏ dấu chấm cuối sau từ viết tắt).
6. **Giải phóng ổ C:** (đang đầy 100%) nếu muốn chạy bất cứ thứ gì ở local; hoặc train trên Colab.
7. **Chạy `notebook_colab.ipynb` trên Colab** và báo lại lỗi nếu có (notebook chưa chạy thử lần nào).
8. Cân nhắc tăng tỉ lệ câu không thực thể (hiện chỉ ~4% train) nếu model hay đoán thừa thực thể.
9. Nếu nộp đồ án có kèm repo: commit các thay đổi của `VPhoBertTagger/` (mình **không commit** gì).

---

## 8. Những điểm CHƯA KIỂM CHỨNG / không chắc chắn

- **Toàn bộ notebook Colab chưa chạy**: đặc biệt torch có sẵn của Colab + `transformers==4.46.3`, Java 17 với VnCoreNLP (local chạy với Java 8), pandas 3.
- Không biết chính xác bản transformers nào bắt đầu gây lỗi khởi tạo CRF (#5); mới chỉ kiểm chứng lỗi có ở 4.46.3 và bản sửa đúng ở 4.46.3.
- Chưa có kết quả train thật: không biết PhoBERT có vượt baseline trên test_hard hay không, hay kiến trúc nào tốt nhất.
- Chất lượng nhãn: chỉ một người gán (mình), chưa đo độ đồng thuận.
- Dữ liệu là văn do mình viết + sinh tự động, **không phải câu thật của người tìm việc** ⇒ kết quả khó suy ra cho dữ liệu thật.
- PhoBERT được pre-train với kiểu dấu nào (cũ/mới) — chưa kiểm tra; mình chọn theo `normalize_text` của repo.
- `predictor.convert_tensor` dùng `is_split_into_words=True`, còn processor lúc train mã hoá câu ghép — đã so sánh `input_ids`/`valid_ids` khớp trên 20 câu smoke cho cả 3 kiến trúc, nhưng chưa kiểm tra trên toàn bộ dữ liệu.
- Câu dài hơn 128 subword: đã đo trên toàn bộ dữ liệu hiện tại — dài nhất 55 token / 55 subword PhoBERT, nên `--max_seq_length 128` đủ. Nếu bạn thêm câu dài, cần đo lại (validate_data.py không kiểm tra số subword).
- `main.py demo` (streamlit) chưa cài và chưa thử; `demo.py` tô màu theo nhãn `PER/ORG/LOC/MISC`, nên SKILL/TIME sẽ không được tô màu (đọc code, chưa chạy).

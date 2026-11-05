"""Baseline từ điển + regex. So khớp dài nhất trên chuỗi token đã tách từ.

- Token CÓ dấu: so khớp chính xác (lower-case) với biến thể có dấu trong từ điển.
- Token KHÔNG dấu: bỏ dấu cả hai phía rồi so khớp.
- TIME khung giờ: regex ("sau 6h", "từ 18h đến 22h", "8h-12h", ...).
- Một số khoá không dấu 1 âm tiết rất mơ hồ ("toi" = tôi/tối, "sang" = sáng/sang) chỉ được nhận
  khi token trước là từ gợi ý thời gian (buoi, ca, vao, ranh, ...).

Chạy:  python data_build/baseline_dict.py
Ghi:   data_dir/preds/baseline_{test,test_hard}.txt  (token \\t gold \\t pred) và in báo cáo seqeval.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, has_accent, strip_accents
from conll_io import read_data, write_pred
from lexicon import LEXICON

MAX_SPAN = 8
AMBIGUOUS_NOACC = {"toi", "sang"}
TIME_CUES = {"buoi", "ca", "vao", "ranh", "lam", "tu", "den", "va", "hoac", "sau"}

CLOCK = r"\d{1,2}\s*(h|g|giờ|gio)\s*(\d{2})?"
TIME_RE = re.compile(
    rf"^((sau|từ|tu|trước|truoc|khoảng|khoang)\s+)?{CLOCK}(\s*(sáng|sang|chiều|chieu|tối|toi))?"
    rf"(\s*(-|đến|den|tới|toi)\s*{CLOCK}(\s*(sáng|sang|chiều|chieu|tối|toi))?)?$", re.IGNORECASE)


def build_index():
    acc, noacc = {}, {}
    for etype, lex in LEXICON.items():
        for canon, variants in lex.items():
            for v in set(variants + [canon]):
                k = " ".join(v.lower().split())
                acc.setdefault(k, etype)
                noacc.setdefault(strip_accents(k), etype)
    return acc, noacc


ACC, NOACC = build_index()


def surface(tokens):
    return " ".join(t.replace("_", " ") for t in tokens).lower()


def match(tokens, i, j):
    span = tokens[i:j]
    s = surface(span)
    if TIME_RE.match(s):
        return "TIME"
    if has_accent(s):
        return ACC.get(s)
    k = strip_accents(s)
    etype = NOACC.get(k)
    if etype and k in AMBIGUOUS_NOACC:
        prev = strip_accents(tokens[i - 1].lower()) if i > 0 else ""
        if prev not in TIME_CUES:
            return None
    return etype


def tag(tokens):
    labels = ["O"] * len(tokens)
    i = 0
    while i < len(tokens):
        for j in range(min(len(tokens), i + MAX_SPAN), i, -1):
            etype = match(tokens, i, j)
            if etype:
                labels[i] = "B-" + etype
                for k in range(i + 1, j):
                    labels[k] = "I-" + etype
                i = j
                break
        else:
            i += 1
    return labels


def main():
    from eval_report import report
    out_dir = os.path.join(DATA_DIR, "preds")
    os.makedirs(out_dir, exist_ok=True)
    for split in ("test", "test_hard"):
        tokens, gold = read_data(os.path.join(DATA_DIR, f"{split}.txt"))
        pred = [tag(t) for t in tokens]
        out = os.path.join(out_dir, f"baseline_{split}.txt")
        write_pred(out, tokens, gold, pred)
        print(f"\n######## BASELINE từ điển — {split} ({len(tokens)} câu) -> {out}")
        report(out, os.path.join(DATA_DIR, f"{split}_meta.jsonl"))


if __name__ == "__main__":
    main()

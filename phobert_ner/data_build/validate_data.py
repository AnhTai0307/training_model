"""Kiểm tra data_dir/*.txt (định dạng 4 cột của VPhoBertTagger) và in thống kê.

Chạy:  python data_build/validate_data.py [data_dir]
Thoát mã 1 nếu có lỗi.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, VALID_LABELS, has_accent

N_COLS = 4
SPLITS = ["train", "dev", "test", "test_hard"]
# Giá trị pandas.read_csv mặc định coi là NaN (processor.py đọc file bằng read_csv không tắt na_values)
PANDAS_NA = {"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN",
             "<NA>", "N/A", "NA", "NULL", "NaN", "None", "n/a", "nan", "null"}


def read_sentences(path):
    """-> (sentences, errors). sentence = list[(lineno, cols)]"""
    sents, cur, errors = [], [], []
    with open(path, encoding="utf-8", newline="") as f:
        lines = f.read().split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    prev_blank = False
    for i, raw in enumerate(lines, 1):
        if raw.endswith("\r"):
            errors.append(f"{path}:{i}: có ký tự CR (\\r)")
            raw = raw[:-1]
        if raw.strip() == "":
            if prev_blank or not cur:
                errors.append(f"{path}:{i}: câu rỗng (dòng trống liên tiếp hoặc ở đầu file)")
            if cur:
                sents.append(cur)
            cur, prev_blank = [], True
            continue
        prev_blank = False
        cols = raw.split("\t")
        if len(cols) != N_COLS:
            errors.append(f"{path}:{i}: có {len(cols)} cột, cần {N_COLS}: {raw!r}")
            continue
        if any(c.strip() == "" for c in cols):
            errors.append(f"{path}:{i}: có cột rỗng: {raw!r}")
        cur.append((i, cols))
    if cur:
        sents.append(cur)
    return sents, errors


def check_sentence(path, sent):
    errs = []
    prev = "O"
    for lineno, cols in sent:
        tok, lab = cols[0], cols[-1]
        if lab not in VALID_LABELS:
            errs.append(f"{path}:{lineno}: nhãn không hợp lệ {lab!r}")
        if lab.startswith("I-") and (prev == "O" or prev[2:] != lab[2:]):
            errs.append(f"{path}:{lineno}: lỗi BIO — {lab} đứng sau {prev}")
        if tok in PANDAS_NA:
            errs.append(f"{path}:{lineno}: token {tok!r} sẽ bị pandas đọc thành NaN")
        if '"' in tok or " " in tok:
            errs.append(f"{path}:{lineno}: token {tok!r} chứa dấu nháy kép hoặc khoảng trắng")
        prev = lab
    return errs


def pandas_sentence_count(path):
    """Đếm câu đúng như processor.convert_word_segment_examples_features nhìn thấy."""
    import pandas as pd
    data = pd.read_csv(path, delimiter="\t", encoding="utf-8", skip_blank_lines=False,
                       names=["token", "pos", "chunk", "ner"])
    n, in_sent = 0, False
    for tok in data.token:
        if pd.notna(tok):
            in_sent = True
        elif in_sent:
            n, in_sent = n + 1, False
    return n + (1 if in_sent else 0)


def entities(labels):
    out, cur = [], None
    for l in labels + ["O"]:
        if l.startswith("B-") or l == "O":
            if cur:
                out.append(cur)
            cur = l[2:] if l.startswith("B-") else None
    return out


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR
    all_errors = []
    rows = []
    for sp in SPLITS:
        path = os.path.join(data_dir, f"{sp}.txt")
        if not os.path.exists(path):
            print(f"[bỏ qua] không có {path}")
            continue
        sents, errs = read_sentences(path)
        for s in sents:
            errs += check_sentence(path, s)
        n_pd = pandas_sentence_count(path)
        if n_pd != len(sents):
            errs.append(f"{path}: pandas đọc ra {n_pd} câu nhưng file có {len(sents)} câu")
        all_errors += errs

        ent_c, n_noent, n_noacc, n_neg = Counter(), 0, 0, 0
        for s in sents:
            labs = [c[-1] for _, c in s]
            ents = entities(labs)
            ent_c.update(ents)
            n_noent += not ents
            n_noacc += not has_accent(" ".join(c[0] for _, c in s))
        meta_path = os.path.join(data_dir, f"{sp}_meta.jsonl")
        if os.path.exists(meta_path):
            meta = [json.loads(l) for l in open(meta_path, encoding="utf-8")]
            if len(meta) != len(sents):
                all_errors.append(f"{meta_path}: {len(meta)} dòng metadata != {len(sents)} câu")
            n_neg = sum(m["negated"] for m in meta)
        n = max(1, len(sents))
        rows.append((sp, len(sents), sum(len(s) for s in sents), ent_c["SKILL"], ent_c["JOB"], ent_c["TIME"], ent_c["LOC"],
                     f"{n_noent / n:.1%}", f"{n_noacc / n:.1%}", f"{n_neg / n:.1%}", len(errs)))

    hdr = ("tập", "số câu", "số token", "SKILL", "JOB", "TIME", "LOC", "không thực thể", "không dấu", "có phủ định", "lỗi")
    w = [max(len(str(r[i])) for r in rows + [hdr]) for i in range(len(hdr))]
    print(" | ".join(str(h).ljust(w[i]) for i, h in enumerate(hdr)))
    print("-+-".join("-" * x for x in w))
    for r in rows:
        print(" | ".join(str(v).ljust(w[i]) for i, v in enumerate(r)))
    if all_errors:
        print(f"\nCÓ {len(all_errors)} LỖI:")
        for e in all_errors[:50]:
            print("  " + e)
        sys.exit(1)
    print("\nOK: không có lỗi định dạng / nhãn / BIO / câu rỗng.")


if __name__ == "__main__":
    main()

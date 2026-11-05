"""Báo cáo F1 mức thực thể (seqeval) theo loại nhãn, tách nhóm: có dấu / không dấu / phủ định / không thực thể.

Chạy:  python data_build/eval_report.py <file_dự_đoán> <file_meta.jsonl>
File dự đoán: token \\t gold \\t pred (do baseline_dict.py hoặc predict_conll.py sinh ra).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conll_io import read_meta, read_pred
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
from seqeval.metrics.sequence_labeling import get_entities


def _prf(gold, pred):
    return (precision_score(gold, pred, zero_division=0), recall_score(gold, pred, zero_division=0),
            f1_score(gold, pred, zero_division=0))


def report(pred_path, meta_path):
    tokens, gold, pred = read_pred(pred_path)
    meta = read_meta(meta_path)
    assert len(meta) == len(gold), f"meta {len(meta)} dòng != {len(gold)} câu — sai file meta?"
    for m, t in zip(meta, tokens):
        # kiểm tra meta đúng thứ tự câu
        assert m["text"].replace(" ", "") == "".join(t).replace("_", ""), (m["text"], t)

    print("== Toàn bộ (seqeval, mức thực thể, mode mặc định/conlleval) ==")
    print(classification_report(gold, pred, digits=4, zero_division=0))

    groups = {
        "có dấu": [i for i, m in enumerate(meta) if m["has_accent"]],
        "không dấu": [i for i, m in enumerate(meta) if not m["has_accent"]],
        "phủ định": [i for i, m in enumerate(meta) if m["negated"]],
    }
    print(f"{'nhóm':<12}{'số câu':>8}{'P':>9}{'R':>9}{'F1':>9}")
    for name, idx in groups.items():
        if not idx:
            print(f"{name:<12}{0:>8}")
            continue
        p, r, f = _prf([gold[i] for i in idx], [pred[i] for i in idx])
        print(f"{name:<12}{len(idx):>8}{p:>9.4f}{r:>9.4f}{f:>9.4f}")

    # recall riêng cho các thực thể bị phủ định (thứ tự thực thể trong meta == thứ tự trên nhãn gold)
    hit = tot = 0
    for i, m in enumerate(meta):
        g_ents = get_entities(gold[i])
        assert len(g_ents) == len(m["entities"]), (m["text"], g_ents, m["entities"])
        p_ents = set(get_entities(pred[i]))
        for ge, me in zip(g_ents, m["entities"]):
            if me["negated"]:
                tot += 1
                hit += ge in p_ents
    if tot:
        print(f"Thực thể bị phủ định: model trích đúng {hit}/{tot} ({hit / tot:.1%}) — "
              f"(nhãn vẫn gán cho thực thể phủ định; cờ negated chỉ có trong metadata)")

    idx = [i for i, m in enumerate(meta) if m["n_entities"] == 0]
    if idx:
        fp = sum(len(get_entities(pred[i])) for i in idx)
        clean = sum(not get_entities(pred[i]) for i in idx)
        print(f"Không thực thể: {len(idx)} câu | câu dự đoán sạch (0 thực thể): {clean}/{len(idx)} | "
              f"thực thể dự đoán thừa: {fp}  (F1 không xác định cho nhóm này)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    report(sys.argv[1], sys.argv[2])

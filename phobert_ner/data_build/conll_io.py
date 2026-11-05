"""Đọc/ghi file CoNLL dùng chung cho baseline / predict / eval.

File dữ liệu (repo):   token \\t pos \\t chunk \\t ner
File dự đoán:          token \\t gold \\t pred
"""
import json


def read_conll(path):
    """-> list[list[list[str]]]: câu -> dòng -> cột"""
    sents, cur = [], []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\r\n")
            if not ln.strip():
                if cur:
                    sents.append(cur)
                cur = []
                continue
            cur.append(ln.split("\t"))
    if cur:
        sents.append(cur)
    return sents


def read_data(path):
    """File 4 cột -> (tokens_list, gold_labels_list)"""
    sents = read_conll(path)
    return [[c[0] for c in s] for s in sents], [[c[-1] for c in s] for s in sents]


def write_pred(path, tokens, gold, pred):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for t, g, p in zip(tokens, gold, pred):
            assert len(t) == len(g) == len(p), (t, g, p)
            for a, b, c in zip(t, g, p):
                f.write(f"{a}\t{b}\t{c}\n")
            f.write("\n")


def read_pred(path):
    sents = read_conll(path)
    return [[c[0] for c in s] for s in sents], [[c[1] for c in s] for s in sents], [[c[2] for c in s] for s in sents]


def read_meta(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

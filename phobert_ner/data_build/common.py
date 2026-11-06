"""Tiện ích dùng chung: chuẩn hoá, bỏ dấu, parse markup, tách từ, căn span vào token.

Markup câu viết tay:  "tôi giỏi [tiếng anh|SKILL], rảnh [tối|TIME|neg]"
  - [text|TAG]      thực thể
  - [text|TAG|neg]  thực thể trong ngữ cảnh phủ định (vẫn gán nhãn, cờ negated ghi ở metadata)
"""
import importlib.util
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, "VPhoBertTagger")
VNCORENLP_DIR = os.path.join(ROOT, "vncorenlp")
DATA_DIR = os.path.join(ROOT, "data_dir")
BUILD_DIR = os.path.join(ROOT, "data_build")

ENTITY_TYPES = ("SKILL", "JOB", "TIME", "LOC")
VALID_LABELS = ["O", "B-SKILL", "I-SKILL", "B-JOB", "I-JOB", "B-TIME", "I-TIME", "B-LOC", "I-LOC"]

# Dùng ĐÚNG hàm normalize_text của repo (predictor.py gọi hàm này lúc suy luận),
# để dữ liệu train và đầu vào lúc predict cùng một quy ước dấu.
# Nạp theo đường dẫn file để không kích hoạt vphoberttagger/__init__.py (import cả trainer/predictor).
_spec = importlib.util.spec_from_file_location("_repo_helper", os.path.join(REPO, "vphoberttagger", "helper.py"))
_repo_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_repo_helper)
repo_normalize_text = _repo_helper.normalize_text


def normalize(text: str) -> str:
    """NFC -> normalize_text của repo (kiểu dấu cũ: hòa->hoà, thùy->thuỳ; bỏ ký tự ẩn; gộp khoảng trắng)."""
    return repo_normalize_text(unicodedata.normalize("NFC", text))


def _strip_char(c: str) -> str:
    if c == "đ":
        return "d"
    if c == "Đ":
        return "D"
    base = unicodedata.normalize("NFD", c)[0]
    return base


def strip_accents(text: str) -> str:
    """Bỏ dấu từng ký tự (giữ nguyên độ dài chuỗi NFC => offset span không đổi)."""
    text = unicodedata.normalize("NFC", text)
    return "".join(_strip_char(c) for c in text)


def has_accent(text: str) -> bool:
    return strip_accents(text) != unicodedata.normalize("NFC", text)


_MARK = re.compile(r"\[([^\[\]|]+)\|(SKILL|JOB|TIME|LOC)(\|neg)?\]")


def parse_markup(line: str):
    """-> (text, [ {start,end,label,negated} ])"""
    text, ents, pos = "", [], 0
    for m in _MARK.finditer(line):
        text += line[pos:m.start()]
        s = len(text)
        text += m.group(1)
        ents.append({"start": s, "end": len(text), "label": m.group(2), "negated": bool(m.group(3))})
        pos = m.end()
    text += line[pos:]
    if "[" in text or "]" in text or "|" in text:
        raise ValueError(f"Markup lỗi: {line!r}")
    return text, ents


def parse_normalized(line: str):
    """Chuẩn hoá cả dòng markup (normalize() không đụng tới [ | ]) rồi parse.
    Các phép thay dấu của repo giữ nguyên độ dài nên không làm lệch span."""
    text, ents = parse_markup(normalize(line))
    assert normalize(text) == text, f"normalize không idempotent: {text!r}"
    return text, ents


class Segmenter:
    """Bọc py_vncorenlp (VnCoreNLP-1.2, annotator wseg)."""

    def __init__(self):
        import py_vncorenlp
        cwd = os.getcwd()
        self.model = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=VNCORENLP_DIR)
        os.chdir(cwd)  # py_vncorenlp.VnCoreNLP() tự os.chdir(save_dir) -> trả lại cwd

    def tokens(self, text: str):
        sents = self.model.word_segment(text)
        toks = []
        for s in sents:
            toks.extend(s.split(" "))
        return [t for t in toks if t]


def align(text: str, tokens, ents):
    """Căn span ký tự vào token đã tách. Trả về (labels, None) hoặc (None, lý_do)."""
    offsets, cur = [], 0
    for tok in tokens:
        surface = tok.replace("_", " ")
        while cur < len(text) and text[cur].isspace():
            cur += 1
        if text[cur:cur + len(surface)] != surface:
            # thử so khớp sau chuẩn hoá NFC + bỏ khác biệt khoảng trắng
            cand = text[cur:cur + len(surface)]
            if unicodedata.normalize("NFC", cand) != unicodedata.normalize("NFC", surface):
                return None, f"token {tok!r} không khớp văn bản tại vị trí {cur}: {text[cur:cur+len(surface)+5]!r}"
        offsets.append((cur, cur + len(surface)))
        cur += len(surface)
    labels = ["O"] * len(tokens)
    for e in sorted(ents, key=lambda x: x["start"]):
        idx = [i for i, (s, en) in enumerate(offsets) if s < e["end"] and en > e["start"]]
        if not idx:
            return None, f"thực thể {text[e['start']:e['end']]!r} không trùng token nào"
        if offsets[idx[0]][0] != e["start"] or offsets[idx[-1]][1] != e["end"]:
            got = text[offsets[idx[0]][0]:offsets[idx[-1]][1]]
            return None, (f"biên thực thể {text[e['start']:e['end']]!r} ({e['label']}) cắt ngang token; "
                          f"token phủ: {got!r}")
        if any(labels[i] != "O" for i in idx):
            return None, "hai thực thể chồng lấn"
        labels[idx[0]] = "B-" + e["label"]
        for i in idx[1:]:
            labels[i] = "I-" + e["label"]
    return labels, None

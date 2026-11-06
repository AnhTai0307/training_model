"""Sinh dữ liệu NER (SKILL/TIME/LOC) -> data_dir/{train,dev,test,test_hard}.txt + metadata.

Chạy:  python data_build/build_data.py
"""
import glob
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BUILD_DIR, DATA_DIR, Segmenter, align, has_accent, parse_markup, parse_normalized,
                    strip_accents)
from lexicon import GROUPS, LEXICON
from templates import DEFAULT_PER_PATTERN, FAMILIES, PARTICLES, PER_PATTERN, PRONOUNS

SEED = 13
N_SWAPS = 3            # số biến thể hoán đổi thực thể cho mỗi câu viết tay
P_DEACCENT_HW = 0.45   # xác suất thêm bản bỏ dấu cho câu viết tay có dấu
P_DEACCENT_TPL = 0.3   # xác suất bỏ dấu toàn câu cho câu template
TEMPLATE_RATIO_MAX = 0.45  # template tối đa 45% tổng số câu (yêu cầu: <= 50% tập train)
POS_DUMMY, CHUNK_DUMMY = "_", "_"

rng = random.Random(SEED)


def key(s):
    return strip_accents(s).lower().strip()


# chỉ mục: bề mặt (đã bỏ dấu, lower) -> (type, canonical)
SURFACE_INDEX = {}
for etype, lex in LEXICON.items():
    for canon, variants in lex.items():
        for v in variants + [canon]:
            SURFACE_INDEX.setdefault((etype, key(v)), canon)


def group_of(etype, canon):
    g = GROUPS[etype][canon]
    if etype == "SKILL" and canon in ("IELTS", "TOEIC"):
        return "cert"
    return g


def pick_surface(etype, canon, accented):
    """Câu có dấu -> chọn biến thể bất kỳ; câu không dấu -> bỏ dấu biến thể (đa số viết thường)."""
    v = rng.choice(LEXICON[etype][canon])
    if accented:
        return v
    v = strip_accents(v)
    return v.lower() if rng.random() < 0.7 else v


def to_markup(text, ents):
    out, cur = "", 0
    for e in sorted(ents, key=lambda x: x["start"]):
        out += text[cur:e["start"]] + f"[{text[e['start']:e['end']]}|{e['label']}{'|neg' if e['negated'] else ''}]"
        cur = e["end"]
    return out + text[cur:]


# ---------------------------------------------------------------- câu viết tay
def load_markup_file(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if ln.strip() and not ln.lstrip().startswith("#"):
                rows.append(ln.strip())
    return rows


def swap_variant(text, ents):
    """Đổi mỗi thực thể có trong từ điển sang khái niệm khác cùng nhóm. None nếu không đổi được gì."""
    used = defaultdict(set)
    plan = []
    for e in ents:
        surf = text[e["start"]:e["end"]]
        canon = SURFACE_INDEX.get((e["label"], key(surf)))
        if canon:
            used[e["label"]].add(canon)
        plan.append((e, surf, canon))
    new_ents, out, cur, changed = [], "", 0, False
    for e, surf, canon in sorted(plan, key=lambda x: x[0]["start"]):
        out += text[cur:e["start"]]
        new_surf = surf
        if canon:
            g = group_of(e["label"], canon)
            cands = [c for c in LEXICON[e["label"]] if group_of(e["label"], c) == g and c not in used[e["label"]]]
            if cands:
                c2 = rng.choice(cands)
                used[e["label"]].add(c2)
                new_surf = pick_surface(e["label"], c2, accented=has_accent(text))
                changed = True
        s = len(out)
        out += new_surf
        new_ents.append({**e, "start": s, "end": len(out)})
        cur = e["end"]
    out += text[cur:]
    return (out, new_ents) if changed else None


def build_handwritten(rows):
    recs = []
    for i, line in enumerate(rows):
        gid = f"hw{i:03d}"
        text, ents = parse_markup(line)
        recs.append(dict(group=gid, source="handwritten", aug="orig", markup=line))
        for k in range(N_SWAPS):
            sv = swap_variant(text, ents)
            if sv:
                recs.append(dict(group=gid, source="handwritten", aug=f"swap{k}", markup=to_markup(*sv)))
        if has_accent(text) and rng.random() < P_DEACCENT_HW:
            recs.append(dict(group=gid, source="handwritten", aug="deaccent", markup=strip_accents(line)))
    return recs


# ---------------------------------------------------------------- template
SLOT = re.compile(r"\{(I|P|SKILL|JOB|TIME|LOC)(!neg)?\}")


def fill_pattern(pattern):
    pron = rng.choice(PRONOUNS)
    used = defaultdict(set)
    deacc = rng.random() < P_DEACCENT_TPL

    def repl(m):
        name, neg = m.group(1), bool(m.group(2))
        if name == "I":
            return pron
        if name == "P":
            return rng.choice(PARTICLES)
        cands = [c for c in LEXICON[name] if c not in used[name]]
        canon = rng.choice(cands)
        used[name].add(canon)
        surf = rng.choice(LEXICON[name][canon])
        return f"[{surf}|{name}{'|neg' if neg else ''}]"

    m = SLOT.sub(repl, pattern)
    m = m[0].upper() + m[1:] if rng.random() < 0.3 else m
    if deacc:
        m = strip_accents(m)
        if rng.random() < 0.6:  # kiểu gõ không dấu thường kèm viết thường hết
            m = (m.lower().replace("|skill", "|SKILL").replace("|job", "|JOB")
                 .replace("|time", "|TIME").replace("|loc", "|LOC"))
    return m


def build_templates(n_target):
    recs, patterns = [], []
    for fam, pats in FAMILIES.items():
        for j, p in enumerate(pats):
            patterns.append((fam, j, p))
    per = {fam: PER_PATTERN.get(fam, DEFAULT_PER_PATTERN) for fam in FAMILIES}
    total_cap = sum(per[f] for f, _, _ in patterns)
    scale = min(1.0, n_target / total_cap)
    for fam, j, p in patterns:
        n = max(2, round(per[fam] * scale))
        seen = set()
        tries = 0
        while len(seen) < n and tries < n * 20:
            tries += 1
            m = fill_pattern(p)
            if m in seen:
                continue
            seen.add(m)
            recs.append(dict(group=f"tpl_{fam}_{j:02d}", source="template", aug=fam, markup=m, pattern=p))
    return recs


# ---------------------------------------------------------------- xử lý chung
def process(recs, seg, split_name=None):
    ok, fails = [], []
    for r in recs:
        try:
            text, ents = parse_normalized(r["markup"])
        except Exception as ex:  # markup lỗi => báo lỗi, không đoán
            fails.append({**r, "reason": f"parse: {ex}"})
            continue
        toks = seg.tokens(text)
        labels, reason = align(text, toks, ents)
        if labels is None:
            fails.append({**r, "text": text, "tokens": toks, "reason": reason, "set": split_name})
            continue
        r = {**r, "text": text, "tokens": toks, "labels": labels,
             "has_accent": has_accent(text),
             "entities": [{"text": text[e["start"]:e["end"]], "label": e["label"], "negated": e["negated"]}
                          for e in sorted(ents, key=lambda x: x["start"])]}
        r["negated"] = any(e["negated"] for e in r["entities"])
        r["n_entities"] = len(r["entities"])
        ok.append(r)
    return ok, fails


def split_groups(recs, ratios=(0.8, 0.1, 0.1)):
    by_group = defaultdict(list)
    for r in recs:
        by_group[r["group"]].append(r)
    out = {"train": [], "dev": [], "test": []}
    for source in ("handwritten", "template"):
        gids = sorted(g for g, rs in by_group.items() if rs[0]["source"] == source)
        rng.shuffle(gids)
        total = sum(len(by_group[g]) for g in gids)
        cnt = 0
        for g in gids:
            frac = cnt / total
            name = "train" if frac < ratios[0] else "dev" if frac < ratios[0] + ratios[1] else "test"
            out[name].extend(by_group[g])
            cnt += len(by_group[g])
    for v in out.values():
        rng.shuffle(v)
    return out


def write_conll(path, recs):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for i, r in enumerate(recs):
            for t, l in zip(r["tokens"], r["labels"]):
                f.write(f"{t}\t{POS_DUMMY}\t{CHUNK_DUMMY}\t{l}\n")
            if i != len(recs) - 1:
                f.write("\n")
        f.write("\n")


def write_meta(path, recs, split):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for i, r in enumerate(recs):
            m = {"idx": i, "split": split, "group": r["group"], "source": r["source"], "aug": r["aug"],
                 "text": r["text"], "has_accent": r["has_accent"], "negated": r["negated"],
                 "n_entities": r["n_entities"], "entities": r["entities"]}
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    seg = Segmenter()

    # Gộp handwritten.txt (gốc) + mọi file handwritten_<ten>.txt (mỗi người viết riêng 1 file,
    # tránh đụng chung handwritten.txt -> không conflict khi push git). Thứ tự theo tên file.
    hw_files = [os.path.join(BUILD_DIR, "handwritten.txt")] + \
        sorted(glob.glob(os.path.join(BUILD_DIR, "handwritten_*.txt")))
    hw_rows = []
    for fp in hw_files:
        hw_rows.extend(load_markup_file(fp))
    hw, hw_fail = process(build_handwritten(hw_rows), seg)
    n_tpl_target = int(len(hw) * TEMPLATE_RATIO_MAX / (1 - TEMPLATE_RATIO_MAX))
    tpl, tpl_fail = process(build_templates(n_tpl_target), seg)

    # khử trùng lặp toàn cục (so sánh lower-case) để không rò rỉ câu giống hệt sang tập khác
    seen, data, n_dup = set(), [], 0
    for r in hw + tpl:
        k = r["text"].lower()
        if k in seen:
            n_dup += 1
            continue
        seen.add(k)
        data.append(r)

    splits = split_groups(data)
    for name, recs in splits.items():
        write_conll(os.path.join(DATA_DIR, f"{name}.txt"), recs)
        write_meta(os.path.join(DATA_DIR, f"{name}_meta.jsonl"), recs, name)

    # test_hard: viết tay riêng, không template, không tăng cường
    hard_rows = load_markup_file(os.path.join(BUILD_DIR, "test_hard_raw.txt"))
    hard_recs = [dict(group=f"hard{i:03d}", source="hard", aug="orig", markup=l) for i, l in enumerate(hard_rows)]
    hard, hard_fail = process(hard_recs, seg, "test_hard")
    write_conll(os.path.join(DATA_DIR, "test_hard.txt"), hard)
    write_meta(os.path.join(DATA_DIR, "test_hard_meta.jsonl"), hard, "test_hard")
    train_texts = {r["text"].lower() for r in splits["train"]}
    overlap = [r["text"] for r in hard if r["text"].lower() in train_texts]

    fails = hw_fail + tpl_fail + hard_fail
    with open(os.path.join(BUILD_DIR, "alignment_failures.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in fails:
            f.write(json.dumps({k: r.get(k) for k in ("set", "group", "source", "aug", "markup", "text",
                                                      "tokens", "reason")}, ensure_ascii=False) + "\n")

    with open(os.path.join(BUILD_DIR, "all_sentences.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for name, recs in splits.items():
            for r in recs:
                f.write(json.dumps({"split": name, **{k: r[k] for k in ("group", "source", "aug", "text", "tokens",
                                                                          "labels", "entities")}},
                                   ensure_ascii=False) + "\n")

    print(f"Câu viết tay gốc: {len(hw_rows)} | sau tăng cường căn được: {len(hw)} | lỗi căn: {len(hw_fail)}")
    print(f"Câu template căn được: {len(tpl)} | lỗi căn: {len(tpl_fail)} | số pattern: "
          f"{sum(len(p) for p in FAMILIES.values())}")
    print(f"Bị loại do trùng lặp: {n_dup}")
    for name, recs in splits.items():
        c = Counter(r["source"] for r in recs)
        print(f"{name}: {len(recs)} câu | handwritten={c['handwritten']} template={c['template']} "
              f"({c['template'] / max(1, len(recs)):.1%} template) | nhóm={len({r['group'] for r in recs})}")
    print(f"test_hard: {len(hard)} câu | lỗi căn: {len(hard_fail)} | trùng nguyên văn với train: {len(overlap)}")
    print(f"TỔNG lỗi căn (alignment_failures.jsonl): {len(fails)}")
    # kiểm tra rò rỉ nhóm
    gsplit = defaultdict(set)
    for name, recs in splits.items():
        for r in recs:
            gsplit[r["group"]].add(name)
    leak = [g for g, s in gsplit.items() if len(s) > 1]
    print(f"Nhóm nằm ở >1 tập (phải = 0): {len(leak)}")


if __name__ == "__main__":
    main()

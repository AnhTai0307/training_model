"""Dự đoán bằng checkpoint của VPhoBertTagger trên file đã tách từ (4 cột) -> token \\t gold \\t pred.

Repo không có lệnh ghi file dự đoán (trainer.validate chỉ in metric), nên script này dùng lại
ViTagger.load_model / ViTagger.convert_tensor của repo, bỏ qua bước VnCoreNLP vì dữ liệu đã tách từ sẵn.

Chạy:  python data_build/predict_conll.py <best_model.pt> <data_dir/test.txt> <out_pred.txt> [--no_cuda]
"""
import itertools
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "VPhoBertTagger"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch  # noqa: E402
from conll_io import read_data, write_pred  # noqa: E402
from vphoberttagger.predictor import ViTagger  # noqa: E402


def main(model_path, data_path, out_path, no_cuda=False):
    device = "cuda" if not no_cuda and torch.cuda.is_available() else "cpu"
    model, tokenizer, max_seq_len, label2id, use_crf = ViTagger.load_model(model_path, device=device)
    # đối tượng "giả" ViTagger chỉ đủ thuộc tính cho convert_tensor (không khởi động VnCoreNLP)
    tagger = types.SimpleNamespace(tokenizer=tokenizer, max_seq_len=max_seq_len, use_crf=use_crf, device=device)
    id2label = {i: l for i, l in enumerate(label2id)}

    tokens, gold = read_data(data_path)
    preds, n_trunc = [], 0
    for toks in tokens:
        item = ViTagger.convert_tensor(tagger, toks)
        with torch.no_grad():
            out = model(**item)
        tags = list(itertools.chain(*out.tags)) if isinstance(out.tags[0], list) else out.tags
        p = [id2label[t] for t in tags][:len(toks)]
        if len(p) < len(toks):  # câu dài hơn max_seq_len bị cắt => phần thừa gán O
            n_trunc += 1
            p += ["O"] * (len(toks) - len(p))
        preds.append(p)
    write_pred(out_path, tokens, gold, preds)
    print(f"Đã ghi {len(preds)} câu -> {out_path} (câu bị cắt do max_seq_len: {n_trunc})")


def check_encoding_consistency(model_path, data_path, n=50):
    """So sánh mã hoá lúc predict (ViTagger.convert_tensor) với lúc train (processor) trên n câu đầu."""
    from vphoberttagger.processor import convert_word_segment_examples_features
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    args = ckpt["args"]
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model_name_or_path)
    use_crf = "crf" in args.model_arch
    feats = convert_word_segment_examples_features(data_path, tok, args.label2id,
                                                   ["token", "pos", "chunk", "ner"], args.max_seq_length,
                                                   use_crf=use_crf)
    tagger = types.SimpleNamespace(tokenizer=tok, max_seq_len=args.max_seq_length, use_crf=use_crf, device="cpu")
    tokens, _ = read_data(data_path)
    bad = 0
    for f, toks in list(zip(feats, tokens))[:n]:
        item = ViTagger.convert_tensor(tagger, toks)
        same = torch.equal(item["input_ids"][0], f.input_ids) and torch.equal(item["valid_ids"][0], f.valid_ids)
        bad += not same
    print(f"Kiểm tra mã hoá train vs predict trên {min(n, len(tokens))} câu: {bad} câu khác nhau")
    return bad


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) == 2 and "--check" in sys.argv:
        check_encoding_consistency(a[0], a[1])
    elif len(a) == 3:
        main(*a, no_cuda="--no_cuda" in sys.argv)
    else:
        print(__doc__)
        sys.exit(2)

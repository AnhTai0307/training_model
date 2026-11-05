# Hướng dẫn đóng góp (team)

Mỗi người tự tạo nhánh + dữ liệu mẫu ở máy local, push nhánh lên git, rồi train trên Colab
(Colab clone đúng nhánh đó). Model train ra lưu lên Drive — không push model lên git.

## 0. Chuẩn bị (làm 1 lần)

- Được add làm collaborator trên GitHub repo này.
- Cài git ở máy local (không cần Python/GPU ở local — train sẽ làm trên Colab).
- Set tên/email đúng của bạn (để commit đứng tên bạn):
  ```bash
  git config user.name "Tên thật của bạn"
  git config user.email "email GitHub của bạn"
  ```

## 1. Clone + tạo nhánh riêng (ở máy local)

```bash
git clone https://github.com/letuanlocc/training_model.git
cd training_model
git checkout -b ten/data      # đổi "ten" thành tên bạn
```

## 2. Tạo file dữ liệu riêng của bạn (ở máy local)

Đặt tên theo quy ước `phobert_ner/data_build/handwritten_<ten>.txt` (ví dụ `handwritten_an.txt`) —
**không sửa trực tiếp `handwritten.txt`** (file chung, sửa vào đó dễ bị conflict với người khác).

Viết câu mới theo đúng format markup, mỗi dòng 1 câu:
```
tôi giỏi [tiếng anh|SKILL], rảnh vào [tối|TIME] và ở [Hải Châu|LOC]
Mình tên Lan, sinh viên năm hai, biết [pha chế|SKILL] và có thể làm [ca tối|TIME] ở [Thanh Khê|LOC].
```
- `[text|TAG]` — đánh dấu 1 thực thể, TAG là `SKILL`, `TIME`, hoặc `LOC`.
- `[text|TAG|neg]` — dùng khi câu mang nghĩa phủ định (ví dụ "không biết tiếng Anh"), nhãn vẫn gán bình thường, chỉ thêm cờ phủ định vào metadata.
- Dòng bắt đầu bằng `#` là chú thích, bị bỏ qua.
- Nên viết đa dạng: có dấu / không dấu / teencode, câu ngắn / câu dài, có thực thể / không có thực thể nào, phủ định.
- Chỉ dùng SKILL/TIME/LOC đã có trong `data_build/lexicon.py` — nếu muốn thêm khái niệm mới, thêm vào `lexicon.py` trước (ví dụ thêm 1 quận mới vào `LOC`, hoặc 1 kỹ năng mới vào `SKILL`).

Viết xong **càng nhiều câu càng tốt** (khuyến nghị tối thiểu ~20-30 câu).

## 3. Commit + push nhánh lên GitHub (ở máy local)

```bash
git add phobert_ner/data_build/handwritten_<ten>.txt
# nếu có thêm khái niệm mới vào lexicon.py thì add luôn:
# git add phobert_ner/data_build/lexicon.py
git commit -m "Thêm câu dữ liệu: <mô tả ngắn, ví dụ 'thêm 25 câu teencode cho SKILL/TIME'>"
git push -u origin ten/data
```

## 4. Train trên Colab (Colab tự lấy đúng nhánh của bạn)

Mở `phobert_ner/notebook_colab_team.ipynb` trên Colab. Ở Bước 1, sửa biến `BRANCH` thành đúng tên
nhánh bạn vừa push (`ten/data`), chạy lần lượt các cell — Colab sẽ clone đúng nhánh đó, đã có sẵn
file dữ liệu bạn tạo ở Bước 2, tự sinh dữ liệu + train. Chi tiết xem trong chính notebook.

**KHÔNG push `data_dir/` hay `outputs/` lên git** (đã có trong `.gitignore`) — `data_dir/` dễ conflict
vì mỗi người sinh ra bản khác nhau tùy nhánh của họ có gì. Chỉ 1 người duy nhất, sau khi tất cả các
`handwritten_*.txt` đã được merge vào `main`, mới chạy lại `build_data.py` và push `data_dir/` chính thức 1 lần.

## 5. Lưu model lên Google Drive chung

Notebook đã tự làm bước này ở cuối (lưu vào `phobert_ner_outputs/<arch>_<ten>`). Đặt tên theo `<ten>`
để không đè lên kết quả của người khác, team có thể so sánh sau.

## 6. Tạo Pull Request

Lên GitHub, tạo Pull Request từ nhánh `ten/data` vào `main` để người quản lý repo duyệt và merge.

## Nếu bị conflict khi `git pull`/merge PR

Vì mỗi người có file `handwritten_<ten>.txt` riêng, gần như không bao giờ conflict. Nếu vẫn bị
(hiếm, thường do sửa cùng 1 dòng trong `lexicon.py`), mở file báo conflict, giữ lại cả 2 phần thêm của
2 người (xóa các dòng `<<<<<<<`, `=======`, `>>>>>>>` do git tự chèn), rồi:
```bash
git add <file đã sửa>
git commit
git push
```

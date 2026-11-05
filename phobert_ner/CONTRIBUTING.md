# Hướng dẫn đóng góp (team)

Mỗi người tự tạo dữ liệu mẫu, tự train, rồi push dữ liệu lên git + model lên Drive.
Làm đúng thứ tự dưới đây để không bị conflict với người khác.

## 0. Chuẩn bị (làm 1 lần)

- Được add làm collaborator trên GitHub repo này.
- Cài git, Python (hoặc chỉ cần Colab — xem `notebook_colab_team.ipynb`).
- Set tên/email đúng của bạn (để commit đứng tên bạn):
  ```bash
  git config user.name "Tên thật của bạn"
  git config user.email "email GitHub của bạn"
  ```

## 1. Pull code mới nhất

```bash
git checkout main
git pull
```

## 2. Tạo file dữ liệu riêng của bạn

Đặt tên theo quy ước `data_build/handwritten_<ten>.txt` (ví dụ `handwritten_an.txt`) —
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

## 3. Sinh dữ liệu + train (chạy local, không push data_dir/)

```bash
python data_build/build_data.py      # tự gộp handwritten.txt + mọi handwritten_*.txt hiện có
python data_build/validate_data.py   # kiểm tra lỗi format/alignment
bash train_softmax.sh                # hoặc train_crf.sh / train_lstm_crf.sh — chọn 1 (hoặc train cả 3 để so sánh)
```
Train trên Colab nếu máy không có GPU (xem `notebook_colab_team.ipynb`, Bước 3b).

## 4. Push lên git — CHỈ file dữ liệu gốc của bạn

```bash
git add data_build/handwritten_<ten>.txt
# nếu có thêm khái niệm mới vào lexicon.py thì add luôn:
# git add data_build/lexicon.py
git commit -m "Thêm câu dữ liệu: <mô tả ngắn, ví dụ 'thêm 25 câu teencode cho SKILL/TIME'>"
git push
```

**KHÔNG push:** `data_dir/*` (dữ liệu đã sinh ra), `outputs/` (model), `.venv/`, `vncorenlp/`, file `.zip`
— những thứ này đã có trong `.gitignore`, và `data_dir/` dễ conflict vì mỗi người sinh ra bản khác nhau
tùy lúc nào họ pull. Chỉ 1 người duy nhất, sau khi tất cả các `handwritten_*.txt` đã được merge vào `main`,
mới chạy lại `build_data.py` và push `data_dir/` chính thức 1 lần.

## 5. Lưu model lên Google Drive chung

```bash
cp -r outputs/softmax "<đường dẫn Drive chung>/outputs_<ten>_softmax"
```
Đặt tên theo `<ten>` để không đè lên kết quả của người khác, team có thể so sánh sau.

## Nếu bị conflict khi `git pull`

Vì mỗi người có file `handwritten_<ten>.txt` riêng, gần như không bao giờ conflict. Nếu vẫn bị
(hiếm, thường do sửa cùng 1 dòng trong `lexicon.py`), mở file báo conflict, giữ lại cả 2 phần thêm của
2 người (xóa các dòng `<<<<<<<`, `=======`, `>>>>>>>` do git tự chèn), rồi:
```bash
git add <file đã sửa>
git commit
git push
```

"""Từ điển nguồn cho SKILL / TIME / LOC.

Mỗi khái niệm (canonical) có danh sách cách viết bề mặt (variants).
Biến thể không dấu được sinh tự động khi cần (xem common.strip_accents),
nên ở đây chỉ liệt kê thêm biến thể KHÔNG suy ra được tự động (viết tắt, teencode).

`group` dùng khi hoán đổi thực thể trong câu viết tay: chỉ đổi trong cùng nhóm
để câu vẫn tự nhiên (vd. "giỏi tiếng Anh" -> "giỏi tiếng Nhật", không -> "giỏi giao hàng").
"""

LOC = {
    # canonical: [variants]
    "Hải Châu": ["Hải Châu", "hải châu", "H.Châu", "h.châu", "Hải châu"],
    "Thanh Khê": ["Thanh Khê", "thanh khê", "T.Khê", "Thanh khê"],
    "Sơn Trà": ["Sơn Trà", "sơn trà", "Sơn trà", "S.Trà"],
    "Ngũ Hành Sơn": ["Ngũ Hành Sơn", "ngũ hành sơn", "NHS", "nhs", "Ngũ Hành sơn"],
    "Liên Chiểu": ["Liên Chiểu", "liên chiểu", "Liên chiểu", "L.Chiểu"],
    "Cẩm Lệ": ["Cẩm Lệ", "cẩm lệ", "Cẩm lệ"],
    "Hòa Vang": ["Hòa Vang", "Hoà Vang", "hòa vang", "hoà vang"],
    "Đà Nẵng": ["Đà Nẵng", "đà nẵng", "ĐN", "đn", "Đà nẵng"],
}
LOC_GROUP = {k: "loc" for k in LOC}

TIME = {
    # buổi trong ngày
    "sáng": ["sáng", "buổi sáng", "ca sáng", "sáng sớm"],
    "trưa": ["trưa", "buổi trưa", "ca trưa"],
    "chiều": ["chiều", "buổi chiều", "ca chiều", "chiều muộn"],
    "tối": ["tối", "buổi tối", "ca tối", "tối muộn", "ban đêm", "ca đêm"],
    # ngày
    "cuối tuần": ["cuối tuần", "thứ 7 chủ nhật", "t7 cn", "thứ bảy và chủ nhật"],
    "ngày thường": ["ngày thường", "các ngày trong tuần", "thứ 2 đến thứ 6", "t2-t6"],
    "cả ngày": ["cả ngày", "full ngày", "fulltime cuối tuần"],
    "thứ trong tuần": ["chủ nhật", "thứ 7", "t7", "thứ bảy", "thứ 5", "cn"],
    # kết hợp buổi + ngày
    "tối cuối tuần": ["tối cuối tuần", "tối thứ 7", "sáng chủ nhật", "chiều thứ 7", "tối t7"],
    "tối ngày thường": ["tối các ngày trong tuần", "tối thứ 2 đến thứ 6", "chiều thứ 3", "sáng thứ 5"],
    # khung giờ
    "sau 6h": ["sau 6h", "sau 18h", "sau 17h30", "sau 5h chiều", "sau 9h tối"],
    "khung giờ": ["từ 18h đến 22h", "18h-22h", "từ 7h tới 11h", "8h-12h", "từ 13h đến 17h",
                  "từ 6h đến 10h tối", "14h-18h", "7h30-11h30"],
}
TIME_GROUP = {
    "sáng": "part", "trưa": "part", "chiều": "part", "tối": "part",
    "cuối tuần": "day", "ngày thường": "day", "cả ngày": "day", "thứ trong tuần": "day",
    "tối cuối tuần": "partday", "tối ngày thường": "partday",
    "sau 6h": "clock", "khung giờ": "clock",
}

SKILL = {
    # ngoại ngữ
    "tiếng Anh": ["tiếng Anh", "tiếng anh", "Tiếng Anh", "t.anh", "english", "TA"],
    "tiếng Nhật": ["tiếng Nhật", "tiếng nhật", "Tiếng Nhật"],
    "tiếng Hàn": ["tiếng Hàn", "tiếng hàn", "Tiếng Hàn"],
    "tiếng Trung": ["tiếng Trung", "tiếng trung", "tiếng Hoa"],
    "tiếng Pháp": ["tiếng Pháp", "tiếng pháp"],
    "IELTS": ["IELTS", "ielts"],
    "TOEIC": ["TOEIC", "toeic"],
    # văn phòng / kỹ thuật
    "tin học văn phòng": ["tin học văn phòng", "tin học vp", "THVP", "tin học"],
    "Excel": ["Excel", "excel"],
    "Word": ["Word", "word"],
    "PowerPoint": ["PowerPoint", "powerpoint", "ppt"],
    "lập trình": ["lập trình", "code", "lập trình web", "lập trình Python"],
    "Python": ["Python", "python"],
    "thiết kế": ["thiết kế", "thiết kế đồ họa", "design"],
    "Photoshop": ["Photoshop", "photoshop", "PTS"],
    "Canva": ["Canva", "canva"],
    "chụp ảnh": ["chụp ảnh", "chụp hình", "nhiếp ảnh"],
    "quay phim": ["quay phim", "quay video"],
    "edit video": ["edit video", "dựng video", "chỉnh sửa video", "edit"],
    "nhập liệu": ["nhập liệu", "nhập dữ liệu"],
    "kế toán": ["kế toán"],
    "marketing": ["marketing", "digital marketing"],
    "viết content": ["viết content", "viết bài", "content"],
    # lao động / khả năng thể chất (khả năng có, không phải tên nghề)
    "nấu ăn": ["nấu ăn", "nấu bếp"],
    "lái xe máy": ["lái xe máy", "chạy xe máy"],
    "lái ô tô": ["lái ô tô", "lái xe ô tô"],
    # kỹ năng mềm / nghệ thuật
    "giao tiếp": ["giao tiếp", "kỹ năng giao tiếp"],
    "đàn guitar": ["đàn guitar", "guitar"],
    "piano": ["piano", "đàn piano"],
    "hát": ["hát", "ca hát"],
    "bơi": ["bơi", "bơi lội"],
}
SKILL_GROUP = {}
for _k in SKILL:
    if _k.startswith("tiếng") or _k in ("IELTS", "TOEIC"):
        SKILL_GROUP[_k] = "lang"
    elif _k in ("tin học văn phòng", "Excel", "Word", "PowerPoint", "lập trình", "Python", "thiết kế",
                "Photoshop", "Canva", "chụp ảnh", "quay phim", "edit video", "nhập liệu", "kế toán",
                "marketing", "viết content"):
        SKILL_GROUP[_k] = "tech"
    elif _k in ("giao tiếp", "đàn guitar", "piano", "hát", "bơi"):
        SKILL_GROUP[_k] = "soft"
    else:
        SKILL_GROUP[_k] = "labor"

# JOB: tên công việc / vị trí muốn ứng tuyển (khác SKILL = kỹ năng/khả năng đã có)
JOB = {
    # dịch vụ / bán lẻ
    "bán hàng": ["bán hàng", "bán hàng online", "sale", "nhân viên bán hàng"],
    "tư vấn": ["tư vấn", "tư vấn bán hàng"],
    "chăm sóc khách hàng": ["chăm sóc khách hàng", "CSKH", "cskh"],
    "thu ngân": ["thu ngân"],
    "pha chế": ["pha chế", "pha cà phê", "pha trà sữa", "barista"],
    "phục vụ": ["phục vụ", "phục vụ bàn", "chạy bàn"],
    "phụ bếp": ["phụ bếp"],
    "làm bánh": ["làm bánh"],
    "livestream": ["livestream", "live stream"],
    "MC": ["MC", "dẫn chương trình"],
    # giáo dục / chăm sóc
    "gia sư": ["gia sư", "dạy kèm", "kèm học"],
    "trông trẻ": ["trông trẻ", "giữ trẻ"],
    # vận chuyển / lao động
    "giao hàng": ["giao hàng", "ship hàng", "shipper"],
    "dọn dẹp": ["dọn dẹp", "dọn phòng", "vệ sinh"],
    "bốc xếp": ["bốc xếp", "khuân vác"],
}
JOB_GROUP = {}
for _k in JOB:
    if _k in ("gia sư", "trông trẻ"):
        JOB_GROUP[_k] = "edu_care"
    elif _k in ("giao hàng", "dọn dẹp", "bốc xếp"):
        JOB_GROUP[_k] = "labor"
    else:
        JOB_GROUP[_k] = "service"

LEXICON = {"SKILL": SKILL, "JOB": JOB, "TIME": TIME, "LOC": LOC}
GROUPS = {"SKILL": SKILL_GROUP, "JOB": JOB_GROUP, "TIME": TIME_GROUP, "LOC": LOC_GROUP}

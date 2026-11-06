"""Template sinh câu. Mỗi HỌ (family) có >= 10 cách diễn đạt (pattern).

Slot: {SKILL} {JOB} {TIME} {LOC} ; thêm "!neg" => thực thể trong ngữ cảnh phủ định, vd {SKILL!neg}.
SKILL = kỹ năng/khả năng đã có (giỏi/biết/kinh nghiệm X). JOB = tên công việc/vị trí muốn làm (muốn làm/tìm việc/xin việc X).
Slot phụ (không phải thực thể): {I} đại từ ngôi 1, {P} tiểu từ cuối câu.
Mỗi pattern là một NHÓM khi chia train/dev/test (mọi câu sinh từ một pattern nằm cùng một tập).
"""

PRONOUNS = ["tôi", "mình", "em", "mik", "tớ", "t", "e", "Tôi", "Mình", "Em"]
PARTICLES = ["", "", "", " ạ", " nha", " nhé", " ạ.", ".", " nè", " a"]

FAMILIES = {
    "skill_time_loc": [
        "{I} giỏi {SKILL}, rảnh vào {TIME} và ở {LOC}{P}",
        "{I} biết {SKILL}, có thể làm {TIME} ở {LOC}{P}",
        "{I} ở {LOC}, rảnh {TIME}, biết {SKILL}{P}",
        "{I} muốn làm {JOB} {TIME} tại {LOC}{P}",
        "nhà {I} ở {LOC}, {I} rảnh {TIME} và làm được {JOB}{P}",
        "{I} có kinh nghiệm {SKILL}, rảnh {TIME}, nhà gần {LOC}{P}",
        "{TIME} {I} rảnh, {I} biết {SKILL}, ở khu {LOC}{P}",
        "cần tìm việc {JOB} {TIME} khu vực {LOC}{P}",
        "{I} đang ở {LOC}, tìm việc {JOB} làm {TIME}{P}",
        "{I} làm {JOB} được, giờ rảnh là {TIME}, ở quận {LOC}{P}",
        "{JOB} thì {I} làm được, {TIME} {I} rảnh, {I} ở {LOC}{P}",
        "xin việc {JOB}, {TIME}, {LOC}{P}",
    ],
    "skill_only": [
        "{I} biết {SKILL}{P}",
        "{I} giỏi {SKILL}{P}",
        "{I} có kinh nghiệm {SKILL}{P}",
        "{I} muốn tìm việc {JOB}{P}",
        "{I} từng làm {JOB} một năm{P}",
        "kỹ năng của {I} là {SKILL}{P}",
        "{I} làm được {JOB}{P}",
        "{I} đã học {SKILL} ở trường{P}",
        "{I} có thể nhận việc {JOB}{P}",
        "{I} thích công việc {JOB}{P}",
        "{SKILL} là thế mạnh của {I}{P}",
    ],
    "time_loc": [
        "{I} rảnh {TIME}, ở {LOC}{P}",
        "{I} ở {LOC}, có thể đi làm {TIME}{P}",
        "{I} cần việc {TIME} gần {LOC}{P}",
        "{TIME} {I} rảnh, nhà ở {LOC}{P}",
        "{I} sống ở {LOC} và rảnh {TIME}{P}",
        "{I} muốn làm {TIME} khu vực {LOC}{P}",
        "{I} tìm việc part-time {TIME} ở {LOC}{P}",
        "{I} ở quận {LOC}, giờ rảnh {TIME}{P}",
        "{LOC}, {TIME}{P}",
        "làm {TIME} ở {LOC} được không{P}",
        "{I} có thể làm {TIME} tại {LOC}{P}",
    ],
    "skill_time": [
        "{I} biết {SKILL}, rảnh {TIME}{P}",
        "{I} làm {JOB} {TIME} được{P}",
        "{I} muốn làm {JOB} vào {TIME}{P}",
        "{TIME} {I} có thể làm {JOB}{P}",
        "{I} giỏi {SKILL} và rảnh {TIME}{P}",
        "{I} tìm việc {JOB} {TIME}{P}",
        "{I} có kinh nghiệm {SKILL}, chỉ rảnh {TIME}{P}",
        "{SKILL}, {TIME}{P}",
        "{I} nhận {JOB} {TIME}{P}",
        "{I} rảnh {TIME}, làm {JOB} ok{P}",
        "{I} học {SKILL} rồi, đi làm {TIME} được{P}",
    ],
    "multi_skill_loc": [
        "{I} biết {SKILL} và {SKILL}, ở {LOC}{P}",
        "{I} giỏi {SKILL}, {SKILL} và {SKILL}{P}",
        "{I} làm được {SKILL} lẫn {SKILL}, nhà ở {LOC}{P}",
        "{I} có kinh nghiệm {SKILL} với {SKILL}{P}",
        "{I} biết {SKILL}, {SKILL}, đang ở {LOC}{P}",
        "{I} ở {LOC}, biết {SKILL} và {SKILL}{P}",
        "kỹ năng: {SKILL}, {SKILL}; khu vực: {LOC}{P}",
        "{I} vừa biết {SKILL} vừa biết {SKILL}{P}",
        "{I} muốn làm {JOB} hoặc {JOB} ở {LOC}{P}",
        "{SKILL} và {SKILL} {I} đều làm được{P}",
    ],
    "multi_time_loc": [
        "{I} rảnh {TIME} và {TIME}{P}",
        "{I} rảnh {TIME}, {TIME}, ở {LOC} hoặc {LOC}{P}",
        "{I} có thể làm ở {LOC} hoặc {LOC}{P}",
        "{I} làm được {TIME} hoặc {TIME} ở {LOC}{P}",
        "{I} ở {LOC} nhưng đi làm ở {LOC} được{P}",
        "{TIME} và {TIME} {I} đều rảnh{P}",
        "{I} muốn làm gần {LOC} hoặc {LOC}{P}",
        "{I} rảnh {TIME}, riêng {TIME} thì rảnh cả buổi{P}",
        "{I} ở {LOC}, làm {TIME} với {TIME} được{P}",
        "khu vực {LOC}, {LOC}; giờ {TIME}{P}",
    ],
    "negation": [
        "{I} không rảnh {TIME!neg}{P}",
        "{I} không biết {SKILL!neg}{P}",
        "{I} không rảnh {TIME!neg}, chỉ rảnh {TIME}{P}",
        "{I} không biết {SKILL!neg} nhưng biết {SKILL}{P}",
        "{I} chưa biết {SKILL!neg}{P}",
        "{I} không làm được {TIME!neg}{P}",
        "{I} không ở {LOC!neg}, {I} ở {LOC}{P}",
        "{I} ko rảnh {TIME!neg} đâu{P}",
        "{I} không có kinh nghiệm {JOB!neg}{P}",
        "{I} không muốn làm ở {LOC!neg}{P}",
        "{TIME!neg} thì {I} không rảnh{P}",
        "{I} chưa từng làm {JOB!neg}, nhưng rảnh {TIME}{P}",
    ],
    "level": [
        "{I} hơi biết {SKILL}{P}",
        "{I} thành thạo {SKILL}{P}",
        "{I} biết sơ sơ {SKILL}{P}",
        "{I} giỏi {SKILL} lắm{P}",
        "{I} biết chút ít {SKILL}{P}",
        "{SKILL} của {I} ở mức cơ bản{P}",
        "{I} rất thành thạo {SKILL}, rảnh {TIME}{P}",
        "{I} mới học {SKILL} thôi{P}",
        "{I} biết {SKILL} ở mức khá{P}",
        "{I} {SKILL} tạm được{P}",
        "{I} khá yếu {SKILL}{P}",
    ],
    "no_entity": [
        "{I} muốn tìm việc{P}",
        "{I} cần việc làm thêm{P}",
        "{I} đang tìm việc part-time{P}",
        "{I} chưa có kinh nghiệm{P}",
        "{I} có thể đi làm ngay{P}",
        "{I} muốn ứng tuyển{P}",
        "cho {I} hỏi còn tuyển không{P}",
        "{I} chăm chỉ và chịu khó{P}",
        "{I} cần việc gấp{P}",
        "{I} muốn kiếm thêm thu nhập{P}",
        "{I} là sinh viên năm hai{P}",
    ],
}

# số câu sinh tối đa cho mỗi pattern (no_entity ít hơn vì biến thể thấp => dễ trùng)
PER_PATTERN = {"no_entity": 4}
DEFAULT_PER_PATTERN = 8

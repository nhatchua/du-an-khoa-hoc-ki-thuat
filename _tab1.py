# ==============================================================================
# _tab1.py — Tab 1: Học tập & Phòng Lab
# ==============================================================================
import streamlit as st
import json
import re
from _config import TEXT_ONLY_SUBJECTS
from _ai_client import call_gemini_with_fallback
from _lab import (
    render_smart_lab,
    render_lab_text_block,
    strip_plot_section_from_text,
    _build_text_only_prompt,
)


# ==============================================================================
# PARSE QUIZ TƯƠNG TÁC
# ==============================================================================
def _parse_quiz_questions(text):
    """Parse text bài học AI sinh → list câu hỏi trắc nghiệm."""
    questions = []
    part3_match = re.search(r'(?i)###\s*PHẦN\s*3', text)
    part2_text = text[:part3_match.start()] if part3_match else text

    pattern = r'(?i)(?:\[Q\d+\]|C[âa]u\s*\d+[\.\:]?)'
    parts = re.split(pattern, part2_text)

    for part in parts[1:]:
        lines = [l.strip() for l in part.strip().split('\n') if l.strip()]
        if not lines:
            continue
        q_header = lines[0]
        level, options, correct, explain = "Vận dụng", [], "A", "Gợi ý tự suy luận!"

        match = re.search(r'(?i)\[Mức độ:\s*(.*?)\]', q_header)
        if match:
            level = match.group(1)
            q_header = re.sub(r'(?i)\[Mức độ:\s*.*?\]', '', q_header).strip()

        q_text_lines = [q_header]
        parsing_options = False

        for line in lines[1:]:
            clean_line = re.sub(r'(?i)^\*{0,2}([A-D])\b[\.\:]?\*{0,2}\s*', r'\1. ', line)

            if re.match(r'(?i)###\s*PHẦN\s*3', line):
                break

            if clean_line.upper().startswith(('A.', 'B.', 'C.', 'D.')):
                parsing_options = True
                options.append(clean_line)
            elif re.search(r'(?i)^(CORRECT|ĐÁP ÁN|Đáp án đúng)\s*:', line):
                ext = re.sub(r'[^A-D]', '', line.split(":")[-1].upper())
                if ext:
                    correct = ext[0]
            elif re.search(r'(?i)^(EXPLAIN|GIẢI THÍCH|Gợi ý)\s*:', line):
                explain = line.split(":", 1)[-1].strip()
            else:
                if not parsing_options:
                    q_text_lines.append(line)
                elif options and not clean_line.upper().startswith(('A.', 'B.', 'C.', 'D.')):
                    explain += " " + line

        if len(options) >= 4:
            questions.append({
                "question": " ".join(q_text_lines).strip(),
                "level": level,
                "options": options[:4],
                "correct": correct,
                "explain": explain,
            })
    return questions


# ==============================================================================
# RENDER QUIZ TƯƠNG TÁC
# ==============================================================================
def _render_quiz_interactive(quiz_list):
    """Render danh sách quiz tương tác."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎯 Phần 2: Trắc nghiệm khách quan Socratic")

    for idx, q in enumerate(quiz_list):
        st.markdown(f"**Câu {idx+1}:** `[{q['level']}]` {q['question']}")
        user_choice = st.radio(
            f"Chọn đáp án câu {idx+1}:", q['options'],
            key=f"q_{idx}", label_visibility="collapsed"
        )
        if st.button(f"🔍 Kiểm tra câu {idx+1}", key=f"btn_{idx}"):
            if user_choice:
                choice_letter = re.sub(r'[^A-D]', '', user_choice.strip()[:3]).upper()[:1]
                if choice_letter == q['correct']:
                    st.session_state.quiz_states[idx] = ("correct", "🎉 Xuất sắc! Em tư duy rất chuẩn.")
                else:
                    st.session_state.quiz_states[idx] = ("incorrect", f"💡 **Gợi ý Socratic:** {q['explain']}")
            else:
                st.warning("Vui lòng chọn một đáp án!")

        if idx in st.session_state.quiz_states:
            status, msg = st.session_state.quiz_states[idx]
            if status == "correct":
                st.success(msg)
            else:
                st.warning("🤔 Suy ngẫm thêm gợi ý dưới đây nhé:")
                st.info(msg)
        st.markdown("---")


# ==============================================================================
# RENDER BÀI HỌC
# ==============================================================================
def _render_lesson(lesson_text, subject):
    """Hiển thị Phần 1 + Phần 2 (quiz) + Phần 3 (tự luận)."""
    part2_split = re.split(r'(?i)(?:###\s*)?PHẦN 2[\:\.]?', lesson_text)
    part3_split = re.split(r'(?i)(?:###\s*)?PHẦN 3[\:\.]?', lesson_text)

    # Phần 1
    if len(part2_split) > 0 and part2_split[0].strip():
        cleaned_p1 = re.sub(r'\n\s*\n', '\n\n', part2_split[0].strip())
        cleaned_p1 = re.sub(r'(?:\s*\-\-\-\s*)+$', '', cleaned_p1)
        st.markdown(cleaned_p1)

    # Phần 2
    quiz_list = st.session_state.get("parsed_quiz", [])
    if quiz_list:
        _render_quiz_interactive(quiz_list)
    elif len(part2_split) > 1 and "PHẦN 3" in part2_split[1].upper():
        st.warning("💡 Hệ thống AI vừa sinh ra một định dạng trắc nghiệm mới. Đang hiển thị ở chế độ xem tĩnh:")
        fallback_p2 = re.split(r'(?i)###\s*PHẦN\s*3', part2_split[1])[0]
        st.markdown(fallback_p2.strip())

    # Phần 3
    if len(part3_split) > 1 and part3_split[-1].strip():
        st.markdown("### ✍️ Phần 3: Bài tập tự luận & Hướng dẫn tư duy")
        st.markdown(part3_split[-1].strip())


# ==============================================================================
# PHÒNG LAB — XỬ LÝ RIÊNG
# ==============================================================================
def _render_phong_lab(subject, grade_num, api_key_to_use):
    """Render khu vực Phòng thí nghiệm ảo."""
    st.markdown("---")
    st.markdown(
        '<h4 style="color: #38bdf8; margin-top: 0; margin-bottom: 5px; font-weight: 800;">'
        '🔬 PHÒNG THÍ NGHIỆM ẢO THEO YÊU CẦU (VIRTUAL LAB)</h4>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="color: #cbd5e1; font-size: 15px; margin-bottom: 12px;">'
        f'Hệ thống AI đang liên kết trực tiếp với <b>Môn {subject} - Lớp {grade_num}</b>. '
        f'Nhập yêu cầu mô phỏng đồ thị, tích phân, miền nghiệm, không gian 3D, hoặc sơ đồ tư duy:</div>',
        unsafe_allow_html=True
    )

    lab_command = st.text_input(
        "Lệnh mô phỏng:",
        placeholder="Ví dụ Toán: Vẽ miền nghiệm... Diện tích hình phẳng... Lý/Hóa: Mô phỏng lực...",
        label_visibility="collapsed",
        key="lab_command_input"
    )

    if st.button("✨ Khởi chạy Phòng Lab") and lab_command.strip():
        st.session_state.tram1_count += 1
        with st.spinner("AI đang phân tích ngữ cảnh liên môn và dựng mô hình..."):
            context_text = (
                st.session_state.current_lesson
                if st.session_state.get("current_lesson")
                else "Không có ngữ cảnh bài học trước đó."
            )

            # Chuẩn hóa câu lệnh
            lab_command_norm = re.sub(r'x\s*\*\*\s*2|x\s*\^\s*2|x2\b', 'x²', lab_command)
            lab_command_norm = re.sub(r'x\s*\*\*\s*3|x\s*\^\s*3|x3\b', 'x³', lab_command_norm)
            lab_command_norm = lab_command_norm.rstrip('|').strip()

            # NHÁNH 1: Môn text-only
            if subject in TEXT_ONLY_SUBJECTS:
                try:
                    text_prompt = _build_text_only_prompt(lab_command, subject, grade_num)
                    st.session_state.lab_text_result = call_gemini_with_fallback(text_prompt)
                    st.session_state.lab_data = None
                except Exception as e:
                    st.error(f"Lỗi sinh nội dung: {e}")
                    st.session_state.lab_text_result = None

            # NHÁNH 2: Môn có đồ thị
            else:
                lab_prompt = _build_lab_prompt(lab_command, subject, grade_num, context_text)
                try:
                    raw_json = call_gemini_with_fallback(lab_prompt, json_mode=True)
                    raw_json = raw_json.strip()
                    if raw_json.startswith("```json"):
                        raw_json = raw_json[7:-3].strip()
                    elif raw_json.startswith("```"):
                        raw_json = raw_json[3:-3].strip()
                    st.session_state.lab_data = json.loads(raw_json)
                    st.session_state.lab_text_result = None
                except Exception:
                    fallback_data = _smart_fallback(lab_command)
                    if fallback_data:
                        st.session_state.lab_data = fallback_data
                    else:
                        st.session_state.lab_data = None
                        st.warning(
                            "⚠️ Không nhận diện được yêu cầu. Vui lòng nhập rõ hơn, "
                            "ví dụ: *'Vẽ parabol y = x² - 2x + 1'* hoặc *'Vẽ hàm bậc 3'*"
                        )
                    st.session_state.lab_text_result = None

    # Render kết quả
    if st.session_state.get("lab_text_result"):
        text_content = st.session_state.lab_text_result
        text_content = strip_plot_section_from_text(text_content)
        st.success("✨ Đã khởi tạo nội dung Phòng Lab thành công!")
        render_lab_text_block(text_content)

    if st.session_state.get("lab_data"):
        data = st.session_state.lab_data
        st.success("✨ Đã khởi tạo mô phỏng Phòng Lab liên môn thành công!")
        render_smart_lab(data)


def _smart_fallback(lab_command):
    """Đoán loại đồ thị từ câu lệnh khi AI lỗi."""
    cmd_lower = lab_command.lower()
    cmd_norm = re.sub(r'x\s*\*\*\s*2|x\s*\^\s*2|x2\b', 'x²', cmd_lower)
    cmd_norm = re.sub(r'x\s*\*\*\s*3|x\s*\^\s*3|x3\b', 'x³', cmd_norm)

    if 'x³' in cmd_norm or 'bậc 3' in cmd_norm or 'bậc ba' in cmd_norm:
        return {"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2}
    elif 'x²' in cmd_norm or 'parabol' in cmd_norm or 'bậc 2' in cmd_norm or 'bậc hai' in cmd_norm:
        return {"type": "parabola", "a": 1, "b": -2, "c": 1}
    elif '/' in lab_command and 'x' in cmd_lower:
        return {"type": "func_1_1", "a": 1, "b": 1, "c": 1, "d": -1}
    elif 'sin' in cmd_lower or 'cos' in cmd_lower or 'lượng giác' in cmd_lower:
        return {"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2}
    return None


def _build_lab_prompt(lab_request, subject, grade_num, context_text):
    """Sinh prompt Lab cho môn có đồ thị."""
    return f"""[HỆ TRI THỨC SƯ PHẠM QUỐC GIA - CHUẨN CT GDPT 2018 & QUY CHẾ THI 2026]
Môn học: {subject} | Khối lớp: {grade_num}. 
NGỮ CẢNH BÀI HỌC HIỆN TẠI:
{context_text}

---
Yêu cầu của học sinh: "{lab_request}"
NHIỆM VỤ: Xuất DUY NHẤT 1 khối JSON hợp lệ phân loại mô hình trực quan (KHÔNG VIẾT CHỮ NGOÀI JSON).

QUY TẮC PHÂN LOẠI MÔ HÌNH:
1. DIỆN TÍCH HÌNH PHẲNG: {{"type": "area", "func": "x**2 - 3*x + 2", "a": 0.0, "b": 3.0}}
2. KHỐI TRÒN XOAY 3D: {{"type": "revolve_ox", "func": "2*x + 1", "a": 2.0, "b": 5.0}}
3. HÀM BẬC 3: {{"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2}}
4. HÀM PHÂN THỨC 1/1: {{"type": "func_1_1", "a": 1, "b": 1, "c": 1, "d": -1}}
5. HÀM PHÂN THỨC 2/1: {{"type": "func_2_1", "a": 1, "b": -2, "c": 2, "d": 1, "e": -1}}
6. PARABOL BẬC 2: {{"type": "parabola", "a": 1, "b": -2, "c": 1}}
7. KHÔNG GIAN OXYZ: {{"type": "oxyz", "x": 2, "y": 3, "z": 4}}
8. MÔ PHỎNG NÂNG CAO PYTHON PLOTLY: {{"type": "dynamic_code", "python_code": "fig = go.Figure()\\n# Code vẽ đồ thị\\nsetup_pedagogical_oxy(fig, [-5, 5], [-5, 5])"}}
9. SƠ ĐỒ TƯ DUY MERMAID: {{"type": "mermaid", "code": "graph LR\\n   Root[\\"🎯 TIÊU ĐỀ\\"] --> A[\\"Nhánh 1\\"]"}}

*RÀO CHẮN THÉP:*
- BÁM SÁT 100% NGỮ LIỆU KNTT 2018.
- MÔ PHỎNG NÂNG CAO: BẮT BUỘC gọi `setup_pedagogical_oxy(fig, [x_min, x_max], [y_min, y_max])` ở cuối.
- BIẾN "func" TRONG JSON: KHÔNG DÙNG LATEX. Viết dạng Python (VD: (x**2 - 3*x + 2)/(x - 1)).
- QUY TẮC MERMAID: Dùng `graph LR`. Nhãn trong ngoặc vuông BẮT BUỘC bọc trong ngoặc kép. Không kèm giải thích ngoài JSON."""


# ==============================================================================
# HÀM CHÍNH: RENDER TAB 1
# ==============================================================================
def render_tab_study(grade, subject):
    """Render toàn bộ Tab 1 (Học tập & Phòng Lab)."""
    grade_num = int(grade.split()[1])
    api_key_to_use = st.session_state.get("active_keys_pool", [])

    # Reset khi đổi môn
    if "last_subject_seen" not in st.session_state:
        st.session_state.last_subject_seen = subject
    elif st.session_state.last_subject_seen != subject:
        st.session_state.lab_data = None
        st.session_state.lab_text_result = None
        st.session_state.current_lesson = ""
        st.session_state.last_subject_seen = subject

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📖 Tự học & Chiếm lĩnh kiến thức môn {subject} - Lớp {grade_num}")

    # ========== INPUT BÀI HỌC ==========
    topic_input = st.text_input(
        "📝 Nhập bài học cần chiếm lĩnh kiến thức:",
        placeholder="Ví dụ: Khảo sát hàm số, Hình chóp, Nhị thức Newton...",
        key="topic_input_tab1"
    )

    if st.button("🚀 Soạn bài học chuẩn GDPT 2018") and topic_input.strip():
        st.session_state.tram1_count += 1
        with st.spinner("Đang biên soạn chuẩn ngữ liệu SGK KNTT và cấu trúc Socratic..."):
            study_prompt = _build_study_prompt(topic_input, subject, grade_num)
            try:
                res_text = call_gemini_with_fallback(study_prompt)
                st.session_state.current_lesson = res_text
                st.session_state.parsed_quiz = _parse_quiz_questions(res_text)
                st.session_state.quiz_states = {}
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # ========== RENDER BÀI HỌC ==========
    if st.session_state.get("current_lesson"):
        _render_lesson(st.session_state.current_lesson, subject)

    # ========== PHÒNG LAB ==========
    _render_phong_lab(subject, grade_num, api_key_to_use)


def _build_study_prompt(topic_input, subject, grade_num):
    """Sinh prompt bài học."""
    return f"""[HỆ THỐNG BIÊN SOẠN BÀI HỌC CHUẨN QUỐC GIA - CT GDPT 2018 & QUY CHẾ THI 2026]
Môn học: {subject} | Khối lớp: {grade_num}. Chủ đề bài học: '{topic_input}'.

YÊU CẦU PHÁP LÝ & HỌC THUẬT BẮT BUỘC:
1. BÁM SÁT 100% NGỮ LIỆU & BẢN QUYỀN SGK KẾT NỐI TRI THỨC VỚI CUỘC SỐNG:
   - TOÁN HỌC: TUYỆT ĐỐI CẤM đưa các kiến thức chương trình cũ (2006) vào bài học như: Tích phân từng phần, Tích phân đổi biến số, Đồ thị hàm bậc 4 trùng phương.
   - HÓA HỌC & KHTN: DÙNG 100% DANH PHÁP QUỐC TẾ IUPAC.
   - NGỮ VĂN: Tiếp cận theo ĐẶC TRƯNG THỂ LOẠI. TUYỆT ĐỐI KHÔNG phân tích cơ học bổ dọc. Ngữ liệu ngoài SGK.
   - VẬT LÝ & SINH HỌC: Tuân thủ đúng bản chất hiện tượng, chuẩn SI.
2. QUY ĐỊNH CẤU TRÚC KỸ THUẬT:
   - BBT: DÙNG BẢNG MARKDOWN TIÊU CHUẨN.
   - ĐỒ THỊ: Mô tả bằng lời, ghi chú: "(Kéo xuống Phòng Lab ảo bên dưới để trực quan hóa nhé!)".
   - TRẮC NGHIỆM SOCRATIC: Sinh chính xác 3 câu hỏi trắc nghiệm đánh giá năng lực.
     + Bắt đầu mỗi câu bằng chữ "Câu 1:", "Câu 2:", "Câu 3:".
     + 4 phương án A, B, C, D trên 4 dòng riêng biệt.
     + Kèm dòng "ĐÁP ÁN: [A/B/C/D]" và dòng "GIẢI THÍCH: [Gợi ý tư duy Socratic]".
   - TỰ LUẬN: Sinh 2 bài tập vận dụng kèm HƯỚNG DẪN TƯ DUY 4 BƯỚC (POLYA).
     LỆNH CẤM KỴ: TUYỆT ĐỐI KHÔNG GIẢI CHI TIẾT, KHÔNG VIẾT ĐÁP SỐ.

TIÊU ĐỀ BẮT BUỘC (Phải giữ đúng text này):
### PHẦN 1: TÓM TẮT CỐT LÕI
### PHẦN 2: TRẮC NGHIỆM KHÁCH QUAN SOCRATIC
### PHẦN 3: BÀI TẬP TỰ LUẬN
"""

# ==============================================================================
# _tab1.py — Tab 1: Học tập & Phòng Lab
# ==============================================================================
import streamlit as st
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta

from _config import TEXT_ONLY_SUBJECTS, VN_TZ, get_vn_time
from _ai_client import call_gemini_with_fallback
from _curriculum import BIGDATA_CURRICULUM
from _lab import (
    render_smart_lab,
    render_lab_text_block,
    strip_plot_section_from_text,
    _build_text_only_prompt,
)


# ==============================================================================
# HELPER: RENDER TEXT CÓ LATEX $$...$$ (tách block riêng, không bị vỡ)
# ==============================================================================
def _render_text_with_latex(text: str):
    """Render text, tách $$...$$ ra và render riêng qua st.latex."""
    if not text or not text.strip():
        return

    parts = re.split(r'(\$\$[\s\S]*?\$\$)', text)

    for part in parts:
        if not part or not part.strip():
            continue
        s = part.strip()
        if s.startswith('$$') and s.endswith('$$') and len(s) > 4:
            latex_content = s[2:-2].strip()
            try:
                st.latex(latex_content)
            except Exception:
                st.markdown(part)
        else:
            st.markdown(part)


# ==============================================================================
# PARSE QUIZ TƯƠNG TÁC — CACHE 10 PHÚT
# ==============================================================================
@st.cache_data(show_spinner=False)
def _parse_quiz_questions(text):
    """Parse text bài học AI sinh → list câu hỏi trắc nghiệm. CÓ CACHE."""
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
        q_latex_blocks = []
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
                    if '$$' in line:
                        latex_matches = re.findall(r'\$\$[\s\S]*?\$\$', line)
                        q_latex_blocks.extend(latex_matches)
                        line_clean = re.sub(r'\$\$[\s\S]*?\$\$', '', line).strip()
                        if line_clean:
                            q_text_lines.append(line_clean)
                    else:
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
                "latex_blocks": q_latex_blocks,
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

        for latex_block in q.get("latex_blocks", []):
            _render_text_with_latex(latex_block)
            st.markdown("")

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

    if len(part2_split) > 0 and part2_split[0].strip():
        cleaned_p1 = re.sub(r'(?:\s*\-\-\-\s*)+$', '', part2_split[0].strip())
        _render_text_with_latex(cleaned_p1)

    quiz_list = st.session_state.get("parsed_quiz", [])
    if quiz_list:
        _render_quiz_interactive(quiz_list)
    elif len(part2_split) > 1 and "PHẦN 3" in part2_split[1].upper():
        st.warning("💡 Hệ thống AI vừa sinh ra một định dạng trắc nghiệm mới. Đang hiển thị ở chế độ xem tĩnh:")
        fallback_p2 = re.split(r'(?i)###\s*PHẦN\s*3', part2_split[1])[0]
        _render_text_with_latex(fallback_p2.strip())

    if len(part3_split) > 1 and part3_split[-1].strip():
        st.markdown("### ✍️ Phần 3: Bài tập tự luận & Hướng dẫn tư duy")
        _render_text_with_latex(part3_split[-1].strip())


# ==============================================================================
# ============ TÍNH NĂNG MỚI: KHO CHỦ ĐỀ =======================================
# ==============================================================================

# ----- 1. Chuẩn hóa tiếng Việt không dấu -----
def _remove_diacritics(s: str) -> str:
    """'Khảo sát hàm số' → 'khao sat ham so'"""
    if not s:
        return ""
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def _is_subsequence(query: str, target: str) -> bool:
    """Kiểm tra query có phải subsequence của target không."""
    it = iter(target)
    return all(c in it for c in query)


def _fuzzy_match(query: str, topic: str) -> bool:
    """Tìm kiếm gần đúng: bỏ dấu, bỏ khoảng trắng, substring + subsequence."""
    if not query or not query.strip():
        return True
    q = _remove_diacritics(query).replace(" ", "")
    t = _remove_diacritics(topic).replace(" ", "")
    if not q:
        return True
    if q in t:
        return True
    return _is_subsequence(q, t)


# ----- 2. Khởi tạo state cho topic -----
def _ensure_topic_state():
    """Khởi tạo session_state cho tính năng kho chủ đề."""
    if "topic_history" not in st.session_state:
        st.session_state["topic_history"] = []  # list of dict
    if "topic_favorites" not in st.session_state:
        st.session_state["topic_favorites"] = set()  # set of "subject|topic"


# ----- 3. Lịch sử gần đây -----
def _add_to_history(topic: str, subject: str, grade_num: int):
    """Thêm chủ đề vào lịch sử, giới hạn 5 entry/môn, TTL 7 ngày."""
    _ensure_topic_state()
    history = st.session_state["topic_history"]

    # Xóa entry cũ cùng (subject, topic)
    history = [e for e in history if not (e.get("subject") == subject and e.get("topic") == topic)]

    # Thêm entry mới lên đầu
    history.insert(0, {
        "topic": topic,
        "subject": subject,
        "grade": grade_num,
        "ts": get_vn_time(),
    })

    # Lọc bỏ entry cũ hơn 7 ngày
    now = datetime.now(VN_TZ)
    kept = []
    for e in history:
        try:
            dt = datetime.strptime(e["ts"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
            if (now - dt).days <= 7:
                kept.append(e)
        except Exception:
            kept.append(e)
    history = kept

    # Giới hạn 5 entry/môn
    by_subject = defaultdict(list)
    for e in history:
        by_subject[e.get("subject", "")].append(e)
    result = []
    for subj, entries in by_subject.items():
        entries.sort(key=lambda x: x.get("ts", ""), reverse=True)
        result.extend(entries[:5])
    result.sort(key=lambda x: x.get("ts", ""), reverse=True)

    st.session_state["topic_history"] = result


def _get_history_for_subject(subject: str):
    """Lấy lịch sử gần đây của 1 môn (đã TTL 7 ngày)."""
    _ensure_topic_state()
    history = st.session_state["topic_history"]
    now = datetime.now(VN_TZ)
    result = []
    for e in history:
        if e.get("subject") != subject:
            continue
        try:
            dt = datetime.strptime(e["ts"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
            if (now - dt).days <= 7:
                result.append(e)
        except Exception:
            result.append(e)
    return result[:5]


def _clear_history_for_subject(subject: str):
    """Xóa lịch sử gần đây của 1 môn."""
    _ensure_topic_state()
    st.session_state["topic_history"] = [
        e for e in st.session_state["topic_history"]
        if e.get("subject") != subject
    ]


def _relative_time(ts_str: str) -> str:
    """'2025-...' → '2 giờ trước'."""
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
        now = datetime.now(VN_TZ)
        delta = now - dt
        if delta.days >= 1:
            return f"{delta.days} ngày trước"
        if delta.seconds >= 3600:
            return f"{delta.seconds // 3600} giờ trước"
        if delta.seconds >= 60:
            return f"{delta.seconds // 60} phút trước"
        return "Vừa xong"
    except Exception:
        return ""


# ----- 4. Yêu thích -----
def _is_favorite(subject: str, topic: str) -> bool:
    _ensure_topic_state()
    return f"{subject}|{topic}" in st.session_state["topic_favorites"]


def _toggle_favorite(subject: str, topic: str):
    _ensure_topic_state()
    key = f"{subject}|{topic}"
    favs = st.session_state["topic_favorites"]
    if key in favs:
        favs.discard(key)
    else:
        favs.add(key)
    st.session_state["topic_favorites"] = favs
    st.rerun()


def _get_favorites_for_subject(subject: str):
    _ensure_topic_state()
    prefix = f"{subject}|"
    return [k[len(prefix):] for k in st.session_state["topic_favorites"] if k.startswith(prefix)]


# ----- 5. Lấy chủ đề theo môn + lớp -----
def _get_topics_for_subject_grade(subject: str, grade_num: int, include_lower: bool = False):
    """
    Trả về list topic (str) cho môn + lớp.
    - Môn "Lịch sử & Địa lý" → gộp 2 môn, prefix [Lịch sử]/[Địa lý].
    - include_lower=True → thêm chủ đề lớp thấp hơn, prefix [Lớp X].
    """
    if subject == "Lịch sử & Địa lý":
        curriculum_keys = [("Lịch sử", "[Lịch sử] "), ("Địa lý", "[Địa lý] ")]
    elif subject in BIGDATA_CURRICULUM:
        curriculum_keys = [(subject, "")]
    else:
        return []

    topics = []
    for ck, prefix in curriculum_keys:
        grade_data = BIGDATA_CURRICULUM.get(ck, {})
        # Lớp hiện tại
        if grade_num in grade_data:
            for t in grade_data[grade_num]:
                topics.append(f"{prefix}{t}")
        # Lớp dưới (nếu bật)
        if include_lower:
            for g in sorted(grade_data.keys(), reverse=True):
                if g >= grade_num:
                    continue
                for t in grade_data[g]:
                    topics.append(f"[Lớp {g}] {prefix}{t}")
    return topics


# ----- 6. UI: Link SGK -----
def _render_sgk_link():
    st.markdown(
        '<div style="background: linear-gradient(135deg, #1e293b, #0f172a); '
        'padding: 12px 18px; border-radius: 10px; border: 1.5px solid #38bdf8; '
        'margin-bottom: 16px;">',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            '<div style="color: #f8fafc; font-weight: 700; font-size: 15px;">'
            '📖 <b>Sách giáo khoa điện tử Kết Nối Tri Thức</b><br>'
            '<span style="color: #94a3b8; font-size: 13px; font-weight: 400;">'
            'Tra cứu lý thuyết, bài tập, ví dụ minh họa từ SGK gốc</span></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.link_button(
            "🌐 Mở SGK điện tử",
            "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/",
            use_container_width=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ----- 7. UI: Tìm kiếm + Tabs + Danh sách chủ đề -----
def _render_topic_button_row(topic: str, subject: str, grade_num: int, idx: int):
    """Render 1 row: nút chọn chủ đề + nút ⭐ yêu thích."""
    c1, c2 = st.columns([6, 1])
    with c1:
        display = topic if len(topic) <= 70 else topic[:67] + "..."
        if st.button(
            display,
            key=f"topic_btn_{subject}_{grade_num}_{idx}",
            use_container_width=True,
            help=topic,
        ):
            st.session_state["topic_input_tab1"] = topic
            _add_to_history(topic, subject, grade_num)
            st.rerun()
    with c2:
        is_fav = _is_favorite(subject, topic)
        if st.button(
            "⭐" if is_fav else "☆",
            key=f"fav_btn_{subject}_{grade_num}_{idx}",
            use_container_width=True,
            help="Bỏ yêu thích" if is_fav else "Thêm vào yêu thích",
        ):
            _toggle_favorite(subject, topic)


def _render_topic_suggestions(subject: str, grade_num: int):
    """Render toàn bộ khu vực gợi ý chủ đề (search + tabs + list)."""
    _ensure_topic_state()

    # Nếu môn không có dữ liệu → thông báo nhẹ
    all_topics = _get_topics_for_subject_grade(subject, grade_num, include_lower=False)
    if not all_topics:
        st.caption(
            f"ℹ️ Môn **{subject}** chưa có dữ liệu gợi ý chủ đề. "
            "Bạn vẫn có thể tự nhập chủ đề ở ô bên dưới."
        )
        return

    st.markdown("### 📚 Kho chủ đề gợi ý")

    # ===== SEARCH BOX =====
    query = st.text_input(
        "🔍 Tìm kiếm chủ đề (gõ không dấu cũng được):",
        placeholder="VD: khao sat ham so, tich phan, nhi thuc, dao ham...",
        key=f"topic_search_{subject}_{grade_num}",
        label_visibility="collapsed",
    )

    # ===== TABS =====
    view_mode = st.radio(
        "Chế độ xem:",
        ["📚 Tất cả", "🕐 Gần đây (5)", "⭐ Yêu thích"],
        horizontal=True,
        key=f"topic_view_{subject}",
        label_visibility="collapsed",
    )

    # ===== XÁC ĐỊNH DANH SÁCH HIỂN THỊ =====
    if view_mode == "📚 Tất cả":
        include_lower = st.checkbox(
            "🔄 Bao gồm chủ đề lớp dưới (ôn nền tảng)",
            value=False,
            key=f"include_lower_{subject}_{grade_num}",
        )
        base_list = _get_topics_for_subject_grade(subject, grade_num, include_lower=include_lower)
    elif view_mode == "🕐 Gần đây (5)":
        history = _get_history_for_subject(subject)
        base_list = [e["topic"] for e in history]
        if not base_list:
            st.info("Chưa có chủ đề nào trong lịch sử gần đây của môn này.")
            return
    else:  # ⭐ Yêu thích
        base_list = _get_favorites_for_subject(subject)
        if not base_list:
            st.info("Chưa có chủ đề nào trong danh sách yêu thích. Bấm ⭐ để thêm.")
            return

    # ===== FILTER THEO QUERY =====
    filtered = [t for t in base_list if _fuzzy_match(query, t)]

    # ===== HIỂN THỊ =====
    if query.strip():
        st.caption(f"🔍 Tìm thấy **{len(filtered)}** chủ đề khớp với `{query}`")
    else:
        st.caption(f"📖 Hiển thị **{len(filtered)}** chủ đề")

    if not filtered:
        st.warning("😕 Không tìm thấy chủ đề nào khớp. Thử từ khóa khác nhé!")
        return

    # ===== LIST =====
    for i, topic in enumerate(filtered):
        # Hiển thị thời gian tương đối nếu ở tab "Gần đây"
        if view_mode == "🕐 Gần đây (5)":
            history = _get_history_for_subject(subject)
            ts_str = ""
            for e in history:
                if e["topic"] == topic:
                    ts_str = _relative_time(e["ts"])
                    break
            if ts_str:
                st.caption(f"🕐 {ts_str}")
        _render_topic_button_row(topic, subject, grade_num, i)

    # ===== NÚT XÓA LỊCH SỬ =====
    if view_mode == "🕐 Gần đây (5)":
        if st.button("🗑️ Xóa lịch sử gần đây của môn này", key=f"clear_hist_{subject}"):
            _clear_history_for_subject(subject)
            st.rerun()


# ----- 8. UI: Ôn tập nhiều chủ đề -----
def _render_multi_topic_selector(subject: str, grade_num: int):
    """Expander cho phép chọn nhiều chủ đề và soạn bài ôn tập tổng hợp."""
    all_topics = _get_topics_for_subject_grade(subject, grade_num, include_lower=False)
    if not all_topics:
        return

    with st.expander("📚 Ôn tập nhiều chủ đề (Soạn bài tổng hợp)", expanded=False):
        st.caption(
            "Chọn 2-5 chủ đề bên dưới → AI sẽ soạn **một bài ôn tập tổng hợp** "
            "liên kết các chủ đề với nhau."
        )
        selected = st.multiselect(
            "Chọn các chủ đề cần ôn tập:",
            options=all_topics,
            default=[],
            key=f"multi_topic_{subject}_{grade_num}",
        )
        if st.button(
            "🚀 Soạn bài ôn tập tổng hợp",
            key=f"btn_review_{subject}_{grade_num}",
            use_container_width=True,
        ):
            if len(selected) < 2:
                st.warning("⚠️ Vui lòng chọn ít nhất 2 chủ đề!")
            else:
                _run_review_lesson(selected, subject, grade_num)


def _run_review_lesson(topics: list, subject: str, grade_num: int):
    """Gọi AI soạn bài ôn tập tổng hợp từ nhiều chủ đề."""
    with st.spinner(f"AI đang tổng hợp {len(topics)} chủ đề thành bài ôn tập..."):
        try:
            prompt = _build_review_prompt(topics, subject, grade_num)
            res_text = call_gemini_with_fallback(prompt)
            st.session_state.current_lesson = res_text
            st.session_state.parsed_quiz = _parse_quiz_questions(res_text)
            st.session_state.quiz_states = {}
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi sinh bài ôn tập: {e}")


def _build_review_prompt(topics: list, subject: str, grade_num: int) -> str:
    """Prompt cho bài ôn tập tổng hợp nhiều chủ đề."""
    topics_str = "\n".join(f"  - {t}" for t in topics)
    return f"""[HỆ THỐNG BIÊN SOẠN BÀI ÔN TẬP TỔNG HỢP - CT GDPT 2018]
Môn: {subject} | Lớp: {grade_num}
Các chủ đề cần ôn tập tổng hợp:
{topics_str}

YÊU CẦU: Soạn 1 bài ÔN TẬP TỔNG HỢP liên kết {len(topics)} chủ đề trên.
- Phần 1: SƠ ĐỒ LIÊN KẾT các chủ đề (nêu mối quan hệ giữa chúng).
- Phần 2: 3 CÂU TRẮC NGHIỆM TÍCH HỢP (kiểm tra kiến thức liên chủ đề).
- Phần 3: 2 BÀI TẬP TỰ LUẬN TỔNG HỢP (kèm hướng dẫn tư duy Polya, KHÔNG giải).

TIÊU ĐỀ BẮT BUỘC:
### PHẦN 1: SƠ ĐỒ LIÊN KẾT CHỦ ĐỀ
### PHẦN 2: TRẮC NGHIỆM TÍCH HỢP
### PHẦN 3: BÀI TẬP TỰ LUẬN TỔNG HỢP
"""


# ==============================================================================
# PHÒNG LAB — XỬ LÝ RIÊNG
# ==============================================================================
def _render_phong_lab(subject, grade_num):
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

    ham_so_keywords = [
        "dạng hàm số", "loại hàm số", "các hàm số",
        "sơ đồ hàm số", "phân loại hàm số",
        "tổng hợp hàm số", "hàm số thường gặp",
    ]
    if any(kw in cmd_lower for kw in ham_so_keywords):
        return {
            "type": "mermaid",
            "code": (
                'graph LR\n'
                '   Root["🎯 CÁC LOẠI HÀM SỐ"] --> A["📌 Hàm Đa Thức"]\n'
                '   Root --> B["📌 Hàm Phân Thức"]\n'
                '   Root --> C["📌 Hàm Mũ và Logarit"]\n'
                '   Root --> D["📌 Hàm Lượng Giác"]\n'
                '   A --> A1["Bậc nhất: $y = ax + b$"]\n'
                '   A --> A2["Bậc hai: $y = ax^2 + bx + c$"]\n'
                '   A --> A3["Bậc ba: $y = ax^3 + bx^2 + cx + d$"]\n'
                '   B --> B1["Bậc 1/1: $y = \\\\frac{ax+b}{cx+d}$"]\n'
                '   B --> B2["Bậc 2/1: $y = \\\\frac{ax^2+bx+c}{dx+e}$"]\n'
                '   C --> C1["Hàm mũ: $y = a^x$"]\n'
                '   C --> C2["Hàm logarit: $y = \\\\log_a x$"]\n'
                '   D --> D1["$y = \\\\sin x$, $y = \\\\cos x$"]\n'
                '   D --> D2["$y = \\\\tan x$, $y = \\\\cot x$"]'
            )
        }

    mindmap_keywords = [
        "sơ đồ tư duy", "mindmap", "mind map", "flowchart",
        "lưu đồ", "sơ đồ khối", "sơ đồ cây", "sơ đồ",
    ]
    if any(kw in cmd_lower for kw in mindmap_keywords):
        return {
            "type": "mermaid",
            "code": (
                'graph LR\n'
                '   Root["🎯 SƠ ĐỒ TƯ DUY"] --> A["📌 Nhánh 1: Khái niệm"]\n'
                '   Root --> B["📌 Nhánh 2: Công thức"]\n'
                '   Root --> C["📌 Nhánh 3: Ứng dụng"]\n'
                '   A --> A1["Từ khóa 1.1"]\n'
                '   A --> A2["Từ khóa 1.2"]\n'
                '   B --> B1["Từ khóa 2.1"]\n'
                '   B --> B2["Từ khóa 2.2"]\n'
                '   C --> C1["Từ khóa 3.1"]\n'
                '   C --> C2["Từ khóa 3.2"]'
            )
        }

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
- QUY TẮC TRÌNH DIỄN SƠ ĐỒ MERMAID: Dùng cấu trúc `graph LR`. Nút con chứa 3-6 từ xúc tích. Toàn bộ nhãn trong ngoặc vuông BẮT BUỘC bọc trong ngoặc kép [\"...\"]. Không kèm giải thích thừa ngoài JSON.
- *** CHECKLIST BẮT BUỘC KHI VẼ SƠ ĐỒ TƯ DUY "CÁC DẠNG HÀM SỐ" HOẶC TƯƠNG TỰ: PHẢI liệt kê ĐỦ 4 NHÓM CHÍNH, KHÔNG ĐƯỢC BỎ SÓT:
  + Nhóm 1: Hàm Đa Thức (Bậc nhất, Bậc hai, Bậc ba)
  + Nhóm 2: Hàm Phân Thức (Bậc 1/1, Bậc 2/1)
  + Nhóm 3: Hàm Mũ và Logarit
  + Nhóm 4: Hàm Lượng Giác (sin, cos, tan, cot)
  Mỗi nút con BẮT BUỘC bọc công thức trong cặp $...$ (ví dụ $y = ax + b$, $y = ax^2 + bx + c$). ***"""


# ==============================================================================
# HÀM CHÍNH: RENDER TAB 1
# ==============================================================================
def render_tab_study(grade, subject):
    """Render toàn bộ Tab 1 (Học tập & Phòng Lab)."""
    grade_num = int(grade.split()[1])
    _ensure_topic_state()

    # Reset khi đổi môn
    if "last_subject_seen" not in st.session_state:
        st.session_state.last_subject_seen = subject
    elif st.session_state.last_subject_seen != subject:
        st.session_state.lab_data = None
        st.session_state.lab_text_result = None
        st.session_state.current_lesson = ""
        st.session_state.last_subject_seen = subject
        # Reset ô nhập bài học khi đổi môn
        st.session_state["topic_input_tab1"] = ""
        st.session_state.parsed_quiz = []
        st.session_state.quiz_states = {}

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📖 Tự học & Chiếm lĩnh kiến thức môn {subject} - Lớp {grade_num}")

    # ========== LINK SGK ==========
    _render_sgk_link()

    # ========== GỢI Ý CHỦ ĐỀ ==========
    _render_topic_suggestions(subject, grade_num)

    # ========== INPUT BÀI HỌC ==========
    st.markdown("### 📝 Hoặc tự nhập chủ đề khác:")
    topic_input = st.text_input(
        "Nhập bài học cần chiếm lĩnh kiến thức:",
        placeholder="Ví dụ: Khảo sát hàm số, Hình chóp, Nhị thức Newton...",
        key="topic_input_tab1",
        label_visibility="collapsed",
    )

    if st.button("🚀 Soạn bài học chuẩn GDPT 2018") and topic_input.strip():
        st.session_state.tram1_count += 1
        _add_to_history(topic_input.strip(), subject, grade_num)
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

    # ========== ÔN TẬP NHIỀU CHỦ ĐỀ ==========
    _render_multi_topic_selector(subject, grade_num)

    # ========== PHÒNG LAB ==========
    _render_phong_lab(subject, grade_num)


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
   - BẢNG BIẾN THIÊN (BBT): BẮT BUỘC sinh bằng LaTeX array, đặt trong cặp $$...$$. TUYỆT ĐỐI KHÔNG dùng Markdown table.
     QUY TẮC CHUNG:
     + Số cột dòng x PHẢI KHỚP số cột dòng y' và y.
     + Dùng \\nearrow cho đồng biến (mũi tên lên), \\searrow cho nghịch biến (mũi tên xuống).
     + Ghi rõ CĐ (cực đại), CT (cực tiểu), || cho tiệm cận đứng.
     + Cột có cực trị thì phải có cột trung gian để chèn mũi tên.

     MẪU 1 — Hàm BẬC 3 (y = ax³+bx²+cx+d, có 2 cực trị):
     $$\\begin{{array}}{{|c|ccccccc|}}
     \\hline
     x & -\\infty & & x_1 & & x_2 & & +\\infty \\\\
     \\hline
     y' & & + & 0 & - & 0 & + & \\\\
     \\hline
     y & -\\infty & \\nearrow & y_{{CĐ}} & \\searrow & y_{{CT}} & \\nearrow & +\\infty \\\\
     \\hline
     \\end{{array}}$$

     MẪU 2 — Hàm BẬC 3 vô cực trị (y' luôn dương hoặc luôn âm):
     $$\\begin{{array}}{{|c|ccc|}}
     \\hline
     x & -\\infty & & +\\infty \\\\
     \\hline
     y' & & + & \\\\
     \\hline
     y & -\\infty & \\nearrow & +\\infty \\\\
     \\hline
     \\end{{array}}$$

     MẪU 3 — Hàm PHÂN THỨC 1/1 (y=(ax+b)/(cx+d), có TCĐ):
     $$\\begin{{array}}{{|c|cccc|}}
     \\hline
     x & -\\infty & & x_0 & & +\\infty \\\\
     \\hline
     y' & & - & || & - & \\\\
     \\hline
     y & y_{{TCN}} & \\searrow & || & \\searrow & y_{{TCN}} \\\\
     \\hline
     \\end{{array}}$$

     MẪU 4 — Hàm PHÂN THỨC 2/1 (y=(ax²+bx+c)/(dx+e), có TCĐ + 2 cực trị):
     $$\\begin{{array}}{{|c|ccccccc|}}
     \\hline
     x & -\\infty & & x_1 & & x_0 & & +\\infty \\\\
     \\hline
     y' & & + & 0 & - & || & - & \\\\
     \\hline
     y & +\\infty & \\nearrow & y_{{CĐ}} & \\searrow & -\\infty || +\\infty & \\searrow & y_{{TCN}} \\\\
     \\hline
     \\end{{array}}$$
     (Tương tự mẫu đối xứng cho trường hợp còn lại)

     MẪU 5 — Hàm PARABOL BẬC 2 (y = ax²+bx+c):
     $$\\begin{{array}}{{|c|ccc|}}
     \\hline
     x & -\\infty & & x_0 & & +\\infty \\\\
     \\hline
     y' & & - & 0 & + & \\\\
     \\hline
     y & +\\infty & \\searrow & y_{{CT}} & \\nearrow & +\\infty \\\\
     \\hline
     \\end{{array}}$$
     (Đảo dấu nếu a < 0)

     LƯU Ý CUỐI: CHỌN ĐÚNG MẪU theo loại hàm đang khảo sát. Không bịa thêm mẫu khác.
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

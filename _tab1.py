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
# HELPER: RENDER TEXT CÓ LATEX
# ==============================================================================
def _render_text_with_latex(text: str):
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
# PARSE QUIZ
# ==============================================================================
@st.cache_data(show_spinner=False)
def _parse_quiz_questions(text):
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
                "level": level, "options": options[:4],
                "correct": correct, "explain": explain,
                "latex_blocks": q_latex_blocks,
            })
    return questions


# ==============================================================================
# RENDER QUIZ
# ==============================================================================
def _render_quiz_interactive(quiz_list):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎯 Phần 2: Trắc nghiệm khách quan Socratic")
    for idx, q in enumerate(quiz_list):
        st.markdown(f"**Câu {idx+1}:** `[{q['level']}]` {q['question']}")
        for latex_block in q.get("latex_blocks", []):
            _render_text_with_latex(latex_block)
            st.markdown("")
        user_choice = st.radio(f"Chọn đáp án câu {idx+1}:", q['options'],
                                key=f"q_{idx}", label_visibility="collapsed")
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
# RENDER LESSON
# ==============================================================================
def _render_lesson(lesson_text, subject):
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
# KHO CHỦ ĐỀ — Helpers
# ==============================================================================
def _remove_diacritics(s: str) -> str:
    if not s:
        return ""
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def _is_subsequence(query: str, target: str) -> bool:
    it = iter(target)
    return all(c in it for c in query)


def _fuzzy_match(query: str, topic: str) -> bool:
    if not query or not query.strip():
        return True
    q = _remove_diacritics(query).replace(" ", "")
    t = _remove_diacritics(topic).replace(" ", "")
    if not q:
        return True
    if q in t:
        return True
    return _is_subsequence(q, t)


def _ensure_topic_state():
    if "topic_history" not in st.session_state:
        st.session_state["topic_history"] = []
    if "topic_favorites" not in st.session_state:
        st.session_state["topic_favorites"] = set()


def _add_to_history(topic: str, subject: str, grade_num: int):
    _ensure_topic_state()
    history = st.session_state["topic_history"]
    history = [e for e in history if not (e.get("subject") == subject and e.get("topic") == topic)]
    history.insert(0, {"topic": topic, "subject": subject, "grade": grade_num, "ts": get_vn_time()})
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
    _ensure_topic_state()
    st.session_state["topic_history"] = [
        e for e in st.session_state["topic_history"] if e.get("subject") != subject
    ]


def _relative_time(ts_str: str) -> str:
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


def _get_topics_for_subject_grade(subject: str, grade_num: int, include_lower: bool = False):
    if subject == "Lịch sử & Địa lý":
        curriculum_keys = [("Lịch sử", "[Lịch sử] "), ("Địa lý", "[Địa lý] ")]
    elif subject in BIGDATA_CURRICULUM:
        curriculum_keys = [(subject, "")]
    else:
        return []
    topics = []
    for ck, prefix in curriculum_keys:
        grade_data = BIGDATA_CURRICULUM.get(ck, {})
        if grade_num in grade_data:
            for t in grade_data[grade_num]:
                topics.append(f"{prefix}{t}")
        if include_lower:
            for g in sorted(grade_data.keys(), reverse=True):
                if g >= grade_num:
                    continue
                for t in grade_data[g]:
                    topics.append(f"[Lớp {g}] {prefix}{t}")
    return topics


# ==============================================================================
# SGK EXPANDER — Mở rộng nhiều link
# ==============================================================================
def _render_sgk_link():
    with st.container(border=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(
                '<div style="color: #f8fafc; font-weight: 700; font-size: 15px; padding-top: 6px;">'
                '📖 <b>Sách giáo khoa điện tử & Tài liệu tham khảo</b><br>'
                '<span style="color: #94a3b8; font-size: 13px; font-weight: 400;">'
                'Tra cứu SGK, sách bài tập, chuyên đề, đề thi các cấp</span></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.link_button(
                "🌐 Mở SGK Kết Nối Tri Thức",
                "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/",
                use_container_width=True,
            )

        with st.expander("📚 Mở rộng — Danh sách đầy đủ các nguồn tài liệu", expanded=False):
            st.markdown("##### 🇻🇳 Sách giáo khoa Việt Nam (Kết Nối Tri Thức)")
            cols_sgk = st.columns(7)
            sgk_links = [
                ("📕 Lớp 6", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📗 Lớp 7", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📘 Lớp 8", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📙 Lớp 9", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📕 Lớp 10", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📗 Lớp 11", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
                ("📘 Lớp 12", "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"),
            ]
            for c, (label, url) in zip(cols_sgk, sgk_links):
                with c:
                    st.link_button(label, url, use_container_width=True)

            st.markdown("##### 📝 Sách bài tập & Chuyên đề (Bộ GD&ĐT)")
            col_bt, col_cd = st.columns(2)
            with col_bt:
                st.link_button("📝 Sách bài tập Kết Nối Tri Thức",
                               "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/",
                               use_container_width=True)
            with col_cd:
                st.link_button("📝 Sách chuyên đề học tập",
                               "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/",
                               use_container_width=True)

            st.markdown("##### 🎯 Đề thi & Luyện tập")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.link_button("🎯 Đề thi TN THPT các năm", "https://moet.gov.vn/", use_container_width=True)
            with col_d2:
                st.link_button("🏆 Đề thi HSG Quốc gia", "https://moet.gov.vn/", use_container_width=True)

            st.markdown("##### 🌍 Sách tham khảo nâng cao / Quốc tế")
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1:
                st.link_button("🌍 Cambridge / A-Level", "https://www.cambridge.org/education", use_container_width=True)
            with col_i2:
                st.link_button("🌍 SAT / AP", "https://www.collegeboard.org/", use_container_width=True)
            with col_i3:
                st.link_button("🌍 Olympiad Toán/Lý/Hóa", "https://www.imo-official.org/", use_container_width=True)


# ==============================================================================
# TOPIC SUGGESTIONS
# ==============================================================================
def _render_topic_button_row(topic: str, subject: str, grade_num: int, idx: int):
    c1, c2 = st.columns([6, 1])
    with c1:
        display = topic if len(topic) <= 70 else topic[:67] + "..."
        if st.button(display, key=f"topic_btn_{subject}_{grade_num}_{idx}",
                     use_container_width=True, help=topic):
            st.session_state["topic_input_tab1"] = topic
            _add_to_history(topic, subject, grade_num)
            st.rerun()
    with c2:
        is_fav = _is_favorite(subject, topic)
        if st.button("⭐" if is_fav else "☆",
                     key=f"fav_btn_{subject}_{grade_num}_{idx}",
                     use_container_width=True,
                     help="Bỏ yêu thích" if is_fav else "Thêm vào yêu thích"):
            _toggle_favorite(subject, topic)


def _render_topic_suggestions(subject: str, grade_num: int):
    _ensure_topic_state()
    all_topics = _get_topics_for_subject_grade(subject, grade_num, include_lower=False)
    if not all_topics:
        st.caption(f"ℹ️ Môn **{subject}** chưa có dữ liệu gợi ý chủ đề. "
                   "Bạn vẫn có thể tự nhập chủ đề ở ô bên dưới.")
        return
    st.markdown("### 📚 Kho chủ đề gợi ý")
    query = st.text_input(
        "🔍 Tìm kiếm chủ đề (gõ không dấu cũng được):",
        placeholder="VD: khao sat ham so, tich phan, nhi thuc, dao ham...",
        key=f"topic_search_{subject}_{grade_num}",
        label_visibility="collapsed",
    )
    view_mode = st.radio(
        "Chế độ xem:",
        ["📚 Tất cả", "🕐 Gần đây (5)", "⭐ Yêu thích"],
        horizontal=True, key=f"topic_view_{subject}",
        label_visibility="collapsed",
    )
    if view_mode == "📚 Tất cả":
        include_lower = st.checkbox("🔄 Bao gồm chủ đề lớp dưới (ôn nền tảng)",
                                     value=False,
                                     key=f"include_lower_{subject}_{grade_num}")
        base_list = _get_topics_for_subject_grade(subject, grade_num, include_lower=include_lower)
    elif view_mode == "🕐 Gần đây (5)":
        history = _get_history_for_subject(subject)
        base_list = [e["topic"] for e in history]
        if not base_list:
            st.info("Chưa có chủ đề nào trong lịch sử gần đây của môn này.")
            return
    else:
        base_list = _get_favorites_for_subject(subject)
        if not base_list:
            st.info("Chưa có chủ đề nào trong danh sách yêu thích. Bấm ⭐ để thêm.")
            return
    filtered = [t for t in base_list if _fuzzy_match(query, t)]
    if query.strip():
        st.caption(f"🔍 Tìm thấy **{len(filtered)}** chủ đề khớp với `{query}`")
    else:
        st.caption(f"📖 Hiển thị **{len(filtered)}** chủ đề")
    if not filtered:
        st.warning("😕 Không tìm thấy chủ đề nào khớp. Thử từ khóa khác nhé!")
        return
    for i, topic in enumerate(filtered):
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
    if view_mode == "🕐 Gần đây (5)":
        if st.button("🗑️ Xóa lịch sử gần đây của môn này", key=f"clear_hist_{subject}"):
            _clear_history_for_subject(subject)
            st.rerun()


# ==============================================================================
# ÔN TẬP NHIỀU CHỦ ĐỀ — CHECKBOX GRID (đã bỏ multiselect)
# ==============================================================================
def _render_multi_topic_selector(subject: str, grade_num: int):
    all_topics = _get_topics_for_subject_grade(subject, grade_num, include_lower=False)
    if not all_topics:
        return
    with st.expander("📚 Ôn tập nhiều chủ đề (Soạn bài tổng hợp)", expanded=False):
        st.caption(
            "Tích chọn **2-5 chủ đề** bên dưới → AI sẽ soạn **một bài ôn tập tổng hợp** "
            "liên kết các chủ đề với nhau."
        )
        # Grid checkbox 2 cột
        selected = []
        n_cols = 2
        cols = st.columns(n_cols)
        for i, topic in enumerate(all_topics):
            with cols[i % n_cols]:
                chk_key = f"multi_topic_chk_{subject}_{grade_num}_{i}"
                if st.checkbox(topic, key=chk_key):
                    selected.append(topic)

        # Đếm + cảnh báo
        n_selected = len(selected)
        if n_selected == 0:
            st.caption("👉 Chưa chọn chủ đề nào.")
        elif n_selected < 2:
            st.warning(f"⚠️ Đã chọn **{n_selected}** chủ đề. Cần chọn ít nhất 2.")
        elif n_selected > 5:
            st.warning(f"⚠️ Đã chọn **{n_selected}** chủ đề. Tối đa 5 chủ đề để đảm bảo chất lượng.")
        else:
            st.success(f"✅ Đã chọn **{n_selected}** chủ đề.")

        # Nút soạn bài — chỉ enable khi 2-5 chủ đề
        can_run = 2 <= n_selected <= 5
        if st.button(
            "🚀 Soạn bài ôn tập tổng hợp",
            key=f"btn_review_{subject}_{grade_num}",
            use_container_width=True,
            disabled=not can_run,
        ):
            _run_review_lesson(selected, subject, grade_num)


def _run_review_lesson(topics: list, subject: str, grade_num: int):
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
# PHÒNG LAB
# ==============================================================================
def _render_phong_lab(subject, grade_num):
    st.markdown("---")
    st.markdown(
        '<h4 style="color: #38bdf8; margin-top: 0; margin-bottom: 5px; font-weight: 800;">'
        '🔬 PHÒNG THÍ NGHIỆM ẢO</h4>',
        unsafe_allow_html=True
    )
    tab_preset, tab_ai = st.tabs(["📚 Mô phỏng có sẵn", "✨ Yêu cầu AI tự do"])
    with tab_preset:
        _render_preset_library(subject, grade_num)
    with tab_ai:
        _render_ai_lab_input(subject, grade_num)

    if st.session_state.get("lab_text_result"):
        text_content = st.session_state.lab_text_result
        text_content = strip_plot_section_from_text(text_content)
        st.success("✨ Đã khởi tạo nội dung Phòng Lab thành công!")
        render_lab_text_block(text_content)
    if st.session_state.get("lab_data"):
        data = st.session_state.lab_data
        st.success("✨ Đã khởi tạo mô phỏng Phòng Lab thành công!")
        render_smart_lab(data)


def _render_preset_library(subject, grade_num):
    from _lab_presets import (
        get_all_presets_for_subject_grade_range,
        has_presets_for_subject,
    )
    if not has_presets_for_subject(subject):
        st.info(f"ℹ️ Môn **{subject}** chưa có mô phỏng có sẵn. "
                "Bạn vui lòng dùng tab **✨ Yêu cầu AI tự do** bên cạnh.")
        return
    query = st.text_input(
        "🔍 Tìm mô phỏng (gõ không dấu cũng được):",
        placeholder="VD: khao sat, parabol, tich phan, dao dong, quang hop...",
        key=f"preset_search_{subject}_{grade_num}",
        label_visibility="collapsed",
    )
    if not query.strip():
        current_lesson = st.session_state.get("current_lesson", "")
        suggested = _suggest_presets_by_topic(current_lesson, subject, grade_num)
        if suggested:
            st.markdown("#### 💡 Gợi ý cho bài học hiện tại")
            cols = st.columns(min(len(suggested), 3))
            for i, p in enumerate(suggested[:6]):
                with cols[i % 3]:
                    _render_preset_card(p, subject, grade_num, prefix="sug")
            st.markdown("---")
    include_lower = st.checkbox("🔄 Bao gồm mô phỏng lớp dưới", value=False,
                                 key=f"preset_include_lower_{subject}_{grade_num}")
    all_presets = get_all_presets_for_subject_grade_range(subject, grade_num, include_lower=include_lower)
    if query.strip():
        all_presets = [p for p in all_presets
                       if _fuzzy_match(query, f"{p['name']} {p['desc']} {' '.join(p.get('tags', []))}")]
    if query.strip():
        st.caption(f"🔍 Tìm thấy **{len(all_presets)}** mô phỏng khớp với `{query}`")
    else:
        st.markdown(f"#### 📚 Kho mô phỏng {subject} — Lớp {grade_num}")
    if not all_presets:
        if query.strip():
            st.warning(f"😕 Không tìm thấy mô phỏng nào khớp với `{query}`.")
        return
    for i in range(0, len(all_presets), 3):
        cols = st.columns(3)
        for j in range(3):
            idx = i + j
            if idx >= len(all_presets):
                break
            with cols[j]:
                _render_preset_card(all_presets[idx], subject, grade_num, prefix=f"grid_{idx}")


def _render_preset_card(preset, subject, grade_num, prefix=""):
    btn_key = f"preset_btn_{prefix}_{preset['id']}_{subject}_{grade_num}"
    label = preset["name"]
    if preset.get("grade") and preset["grade"] != grade_num:
        label += f" [Lớp {preset['grade']}]"
    if st.button(label, key=btn_key, use_container_width=True, help=preset["desc"]):
        st.session_state["lab_data"] = preset["data"]
        st.session_state["lab_text_result"] = None
        st.rerun()
    st.caption(preset["desc"])


def _suggest_presets_by_topic(topic, subject, grade_num):
    if not topic:
        return []
    from _lab_presets import get_presets_for
    topic_lower = _remove_diacritics(topic.lower())
    keyword_map = {
        "khao sat": ["func_3", "func_1_1", "func_2_1"],
        "ham bac 3": ["func_3"],
        "ham bac ba": ["func_3"],
        "parabol": ["parabola"],
        "bac hai": ["parabola"],
        "phan thuc": ["func_1_1", "func_2_1"],
        "tich phan": ["area", "revolve_ox"],
        "dien tich": ["area"],
        "khoi tron": ["revolve_ox"],
        "oxyz": ["oxyz", "oxyz_plane", "oxyz_line", "oxyz_sphere"],
        "khong gian": ["oxyz", "oxyz_plane", "oxyz_line", "oxyz_sphere"],
        "toa do": ["oxyz", "oxyz_plane", "oxyz_line", "oxyz_sphere"],
        "mat phang": ["oxyz_plane"],
        "duong thang": ["oxyz_line"],
        "mat cau": ["oxyz_sphere"],
        "so do": ["mermaid"],
        "mindmap": ["mermaid"],
        "tong hop": ["mermaid"],
        "phan loai": ["mermaid"],
        "dao dong": ["mermaid"],
        "song dien tu": ["mermaid"],
        "song co": ["mermaid"],
        "hat nhan": ["mermaid"],
        "newton": ["mermaid"],
        "nang luong": ["mermaid"],
        "nguyen tu": ["mermaid"],
        "lien ket": ["mermaid"],
        "hydrocarbon": ["mermaid"],
        "carbohydrate": ["mermaid"],
        "polymer": ["mermaid"],
        "te bao": ["mermaid"],
        "dai phan tu": ["mermaid"],
        "quang hop": ["mermaid"],
        "ho hap": ["mermaid"],
        "mendel": ["mermaid"],
        "di truyen": ["mermaid"],
    }
    matched_types = set()
    for kw, types in keyword_map.items():
        if kw in topic_lower:
            matched_types.update(types)
    if not matched_types:
        return []
    presets = get_presets_for(subject, grade_num)
    return [p for p in presets if p["data"].get("type") in matched_types]


def _render_ai_lab_input(subject, grade_num):
    st.markdown(
        f'<div style="color: #cbd5e1; font-size: 15px; margin-bottom: 12px;">'
        f'Hệ thống AI liên kết với <b>Môn {subject} - Lớp {grade_num}</b>. '
        f'Nhập yêu cầu mô phỏng đồ thị, tích phân, không gian 3D, hoặc sơ đồ tư duy:</div>',
        unsafe_allow_html=True
    )
    lab_command = st.text_input(
        "Lệnh mô phỏng:",
        placeholder="Ví dụ: Vẽ miền nghiệm... Diện tích hình phẳng... Mô phỏng lực...",
        label_visibility="collapsed",
        key="lab_command_input"
    )
    if st.button("✨ Khởi chạy Phòng Lab", key="btn_ai_lab") and lab_command.strip():
        st.session_state.tram1_count += 1
        with st.spinner("AI đang phân tích ngữ cảnh liên môn và dựng mô hình..."):
            context_text = (st.session_state.current_lesson
                            if st.session_state.get("current_lesson")
                            else "Không có ngữ cảnh bài học trước đó.")
            if subject in TEXT_ONLY_SUBJECTS:
                try:
                    text_prompt = _build_text_only_prompt(lab_command, subject, grade_num)
                    st.session_state.lab_text_result = call_gemini_with_fallback(text_prompt)
                    st.session_state.lab_data = None
                except Exception as e:
                    st.error(f"Lỗi sinh nội dung: {e}")
                    st.session_state.lab_text_result = None
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
                        st.warning("⚠️ Không nhận diện được yêu cầu. Vui lòng nhập rõ hơn, "
                                   "ví dụ: *'Vẽ parabol y = x² - 2x + 1'* hoặc *'Vẽ hàm bậc 3'*")
                    st.session_state.lab_text_result = None


def _smart_fallback(lab_command):
    cmd_lower = lab_command.lower()
    cmd_norm = re.sub(r'x\s*\*\*\s*2|x\s*\^\s*2|x2\b', 'x²', cmd_lower)
    cmd_norm = re.sub(r'x\s*\*\*\s*3|x\s*\^\s*3|x3\b', 'x³', cmd_norm)
    if 'x³' in cmd_norm or 'bậc 3' in cmd_norm or 'bậc ba' in cmd_norm:
        return {"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2}
    elif 'x²' in cmd_norm or 'parabol' in cmd_norm or 'bậc 2' in cmd_norm or 'bậc hai' in cmd_norm:
        return {"type": "parabola", "a": 1, "b": -2, "c": 1}
    elif '/' in lab_command and 'x' in cmd_lower:
        return {"type": "func_1_1", "a": 1, "b": 1, "c": 1, "d": -1}
    return None


def _build_lab_prompt(lab_request, subject, grade_num, context_text):
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
7. ĐIỂM TRONG KHÔNG GIAN OXYZ: {{"type": "oxyz", "x": 2, "y": 3, "z": 4}}
8. MẶT PHẲNG OXYZ: {{"type": "oxyz_plane", "A": 1.0, "B": 2.0, "C": -1.0, "D": -6.0}}
9. ĐƯỜNG THẲNG OXYZ: {{"type": "oxyz_line", "x0": 1.0, "y0": 2.0, "z0": 3.0, "ux": 2.0, "uy": -1.0, "uz": 2.0}}
10. MẶT CẦU OXYZ: {{"type": "oxyz_sphere", "Ix": 1.0, "Iy": 2.0, "Iz": 3.0, "R": 2.5}}
11. MÔ PHỎNG NÂNG CAO PYTHON PLOTLY: {{"type": "dynamic_code", "python_code": "fig = go.Figure()\\n# Code vẽ đồ thị\\nsetup_pedagogical_oxy(fig, [-5, 5], [-5, 5])"}}
12. SƠ ĐỒ TƯ DUY MERMAID: {{"type": "mermaid", "code": "graph LR\\n   Root[\\"🎯 TIÊU ĐỀ\\"] --> A[\\"Nhánh 1\\"]"}}

*RÀO CHẮN THÉP:*
- BÁM SÁT 100% NGỮ LIỆU KNTT 2018.
- BIẾN "func" TRONG JSON: KHÔNG DÙNG LATEX. Viết dạng Python (VD: (x**2 - 3*x + 2)/(x - 1)).
- QUY TẮC TRÌNH DIỄN SƠ ĐỒ MERMAID: Dùng cấu trúc `graph LR`. Nút con chứa 3-6 từ xúc tích. Toàn bộ nhãn trong ngoặc vuông BẮT BUỘC bọc trong ngoặc kép [\"...\"]. Không kèm giải thích thừa ngoài JSON."""


# ==============================================================================
# HÀM CHÍNH: RENDER TAB 1
# ==============================================================================
def render_tab_study(grade, subject):
    grade_num = int(grade.split()[1])
    _ensure_topic_state()
    if "last_subject_seen" not in st.session_state:
        st.session_state.last_subject_seen = subject
    elif st.session_state.last_subject_seen != subject:
        st.session_state.lab_data = None
        st.session_state.lab_text_result = None
        st.session_state.current_lesson = ""
        st.session_state.last_subject_seen = subject
        st.session_state["topic_input_tab1"] = ""
        st.session_state.parsed_quiz = []
        st.session_state.quiz_states = {}

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📖 Tự học & Chiếm lĩnh kiến thức môn {subject} - Lớp {grade_num}")

    _render_sgk_link()
    _render_topic_suggestions(subject, grade_num)

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

    if st.session_state.get("current_lesson"):
        _render_lesson(st.session_state.current_lesson, subject)

    _render_multi_topic_selector(subject, grade_num)
    _render_phong_lab(subject, grade_num)


def _build_study_prompt(topic_input, subject, grade_num):
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
     + Dùng \\nearrow cho đồng biến, \\searrow cho nghịch biến.
     + Ghi rõ CĐ (cực đại), CT (cực tiểu), || cho tiệm cận đứng.
     + Cột có cực trị thì phải có cột trung gian để chèn mũi tên.

     MẪU 1 — Hàm BẬC 3 (có 2 cực trị):
     $$\\begin{{array}}{{|c|ccccccc|}}
     \\hline
     x & -\\infty & & x_1 & & x_2 & & +\\infty \\\\
     \\hline
     y' & & + & 0 & - & 0 & + & \\\\
     \\hline
     y & -\\infty & \\nearrow & y_{{CĐ}} & \\searrow & y_{{CT}} & \\nearrow & +\\infty \\\\
     \\hline
     \\end{{array}}$$

     MẪU 2 — Hàm BẬC 3 vô cực trị:
     $$\\begin{{array}}{{|c|ccc|}}
     \\hline
     x & -\\infty & & +\\infty \\\\
     \\hline
     y' & & + & \\\\
     \\hline
     y & -\\infty & \\nearrow & +\\infty \\\\
     \\hline
     \\end{{array}}$$

     MẪU 3 — Hàm PHÂN THỨC 1/1:
     $$\\begin{{array}}{{|c|cccc|}}
     \\hline
     x & -\\infty & & x_0 & & +\\infty \\\\
     \\hline
     y' & & - & || & - & \\\\
     \\hline
     y & y_{{TCN}} & \\searrow & || & \\searrow & y_{{TCN}} \\\\
     \\hline
     \\end{{array}}$$

     MẪU 4 — Hàm PHÂN THỨC 2/1:
     $$\\begin{{array}}{{|c|ccccccc|}}
     \\hline
     x & -\\infty & & x_1 & & x_0 & & +\\infty \\\\
     \\hline
     y' & & + & 0 & - & || & - & \\\\
     \\hline
     y & +\\infty & \\nearrow & y_{{CĐ}} & \\searrow & -\\infty || +\\infty & \\searrow & y_{{TCN}} \\\\
     \\hline
     \\end{{array}}$$

     MẪU 5 — Hàm PARABOL BẬC 2:
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
   - ĐỒ THỊ: Mô tả bằng lời, ghi chú: "(Kéo xuống Phòng Lab ảo bên dưới để trực quan hóa nhé!)".
   - TRẮC NGHIỆM SOCRATIC: Sinh chính xác 3 câu hỏi trắc nghiệm.
     + Bắt đầu mỗi câu bằng "Câu 1:", "Câu 2:", "Câu 3:".
     + 4 phương án A, B, C, D trên 4 dòng riêng biệt.
     + Kèm dòng "ĐÁP ÁN: [A/B/C/D]" và dòng "GIẢI THÍCH: [Gợi ý tư duy Socratic]".
   - TỰ LUẬN: Sinh 2 bài tập vận dụng kèm HƯỚNG DẪN TƯ DUY 4 BƯỚC (POLYA).
     LỆNH CẤM KỴ: TUYỆT ĐỐI KHÔNG GIẢI CHI TIẾT, KHÔNG VIẾT ĐÁP SỐ.

TIÊU ĐỀ BẮT BUỘC (Phải giữ đúng text này):
### PHẦN 1: TÓM TẮT CỐT LÕI
### PHẦN 2: TRẮC NGHIỆM KHÁCH QUAN SOCRATIC
### PHẦN 3: BÀI TẬP TỰ LUẬN
"""

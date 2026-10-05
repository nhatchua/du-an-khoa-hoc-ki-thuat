# ==============================================================================
# _socratic.py — Tab 2: Gia sư Socratic + nộp bài
# ==============================================================================
import streamlit as st
import json
import re
import requests
from PIL import Image
from _config import get_vn_time
from _ai_client import call_gemini_with_fallback


def _preprocess_upload_image(uploaded_file, max_side: int = 1600):
    """Đọc ảnh, sửa EXIF orientation, resize cạnh dài về max_side."""
    from PIL import ImageOps
    img = Image.open(uploaded_file)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    w, h = img.size
    if max(w, h) > max_side:
        img.thumbnail((max_side, max_side), resample)
    return img


def _image_to_bytes(img) -> bytes:
    """Chuyển PIL Image -> bytes JPEG để lưu vào session_state."""
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _parse_diagnostic(full_res: str) -> dict:
    """Parse khối <DIAGNOSTIC>...</DIAGNOSTIC> an toàn."""
    if "<DIAGNOSTIC>" not in full_res:
        return {}
    try:
        raw = full_res.split("<DIAGNOSTIC>", 1)[1]
        raw = raw.split("</DIAGNOSTIC>", 1)[0].strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception:
        return {}


def _build_socratic_system_prompt(subject, grade_num, student_name, is_essay):
    """System prompt rẽ nhánh theo đặc thù môn học."""
    if is_essay:
        subject_focus = (
            "Đây là môn TỰ LUẬN (Ngữ văn / Lịch sử & Địa lý). "
            "Chẩn đoán tập trung vào: lập luận (luận điểm — luận cứ — dẫn chứng), "
            "bố cục đoạn văn, diễn đạt — dùng từ — ngữ pháp, tính liên kết, "
            "tính thuyết phục, sắc thái biểu cảm."
        )
    elif subject == "Tiếng Anh":
        subject_focus = (
            "Đây là môn Tiếng Anh. Chẩn đoán tập trung vào: ngữ pháp "
            "(thì, cấu trúc câu, sự hòa hợp chủ — vị), từ vựng (dùng sai nghĩa, "
            "sai dạng từ, sai giới từ), chính tả, cách diễn đạt tự nhiên."
        )
    else:
        subject_focus = (
            "Đây là môn TỰ NHIÊN (Toán / Lý / Hóa / Sinh / Tin). "
            "Chẩn đoán tập trung vào: công thức áp dụng, điều kiện xác định, "
            "đơn vị đo, tính toán số học, logic biến đổi, lập luận kết quả, "
            "đọc sai đề, thiếu trường hợp."
        )

    return f"""Bạn là Thầy giáo Gia Sư AI tại Trường THPT Tân Hiệp & Trung tâm Bồi dưỡng Văn hóa Thiện Nhân (An Giang).
Học sinh: "{student_name}" — Môn {subject} — Lớp {grade_num} ({'Cấp THCS' if grade_num <= 9 else 'Cấp THPT'}) — SGK Kết Nối Tri Thức.

{subject_focus}

NGUYÊN TẮC BẤT DI BẤT DỊCH:
- TUYỆT ĐỐI KHÔNG giải hộ, KHÔNG đưa ra đáp án cuối cùng, KHÔNG viết bài mẫu.
- Khen ngợi CỤ THỂ bước học sinh làm ĐÚNG (chỉ ra chính xác bước nào, vì sao đúng).
- Với bước SAI: đặt 1–2 câu hỏi gợi mở để học sinh TỰ nhận ra lỗi, không chỉ thẳng.
- Xưng hô: gọi học sinh là "em", tự xưng "thầy/cô" (chọn 1 và giữ nhất quán suốt bài).
- Ngôn ngữ: tiếng Việt bình dân, dễ hiểu, tuyệt đối không hàn lâm, không dùng từ tiếng Anh.

Cuối bài LUÔN chèn khối (không thêm chữ nào sau khối này):
<DIAGNOSTIC>{{"topic":"...","error_type":"...","evaluation":"..."}}</DIAGNOSTIC>"""


def render_tab_socratic(grade, subject):
    """Render toàn bộ Tab 2 (Gia sư Socratic + nộp bài)."""
    student_name = st.session_state.get("student_name", "Ẩn danh")
    active_keys_pool = st.session_state.get("active_keys_pool", [])
    sheet_webhook_url = st.session_state.get("sheet_webhook_url", "")
    grade_num = int(grade.split()[1])
    is_essay = subject in ["Ngữ văn", "Lịch sử & Địa lý", "Lịch sử", "Địa lý"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"✍️ Gia Sư Socratic Môn: {subject} - Lớp {grade_num}")
    st.caption(
        "Khung Tri Thức Chuẩn Hóa CT GDPT 2018 & SGK Kết Nối Tri Thức • "
        "Vấn đáp Socratic • Dẫn dắt tư duy, không giải hộ."
    )

    has_chat = len(st.session_state.messages) > 0

    # ========== 2 NÚT ĐIỀU KHIỂN ==========
    col_btn1, col_btn2, _spacer = st.columns([1.1, 1.8, 2])
    with col_btn1:
        if st.button("🔄 Làm bài mới", use_container_width=True, key="soc_btn_new"):
            st.session_state.messages = []
            st.session_state.socratic_uploader_key += 1
            st.session_state.socratic_analyzed_keys = set()
            st.rerun()
    with col_btn2:
        if has_chat and st.button(
            "📎 Nộp bài khác (giữ hội thoại)",
            use_container_width=True, key="soc_btn_more"
        ):
            st.session_state.socratic_uploader_key += 1
            st.rerun()

    current_key = st.session_state.socratic_uploader_key

    # ========== UPLOAD ẢNH ==========
    uploaded_file = st.file_uploader(
        "📸 Tải ảnh bài làm của em (JPG, PNG)",
        type=["jpg", "png", "jpeg"],
        key=f"socratic_uploader_{current_key}"
    )

    # ========== XỬ LÝ ẢNH MỚI ==========
    if uploaded_file is not None:
        img_processed = _preprocess_upload_image(uploaded_file)
        img_bytes = _image_to_bytes(img_processed)
        st.image(img_bytes, caption="Bài làm của em", use_container_width=True)

        already_analyzed = current_key in st.session_state.socratic_analyzed_keys

        if not already_analyzed:
            if st.button("🚀 Bắt đầu nhận xét bài làm", type="primary", key="soc_btn_analyze"):
                if not active_keys_pool:
                    st.error("Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
                else:
                    with st.spinner("Gia Sư AI đang đối chiếu chuẩn kiến thức GDPT 2018 (SGK KNTT)..."):
                        try:
                            sys_prompt = _build_socratic_system_prompt(
                                subject, grade_num, student_name, is_essay
                            )
                            full_res = call_gemini_with_fallback(
                                [f"Học sinh {student_name} nộp ảnh bài làm môn {subject} Lớp {grade_num}. Thầy hãy soi kỹ từng bước và nhận xét Socratic:", img_processed],
                                system_instruction=sys_prompt
                            )

                            if not full_res:
                                st.error("Không thể kết nối AI. Vui lòng thử lại sau.")
                            else:
                                student_fb = (
                                    full_res.split("<DIAGNOSTIC>")[0].strip()
                                    if "<DIAGNOSTIC>" in full_res else full_res
                                )
                                diag = _parse_diagnostic(full_res)
                                if diag:
                                    entry = {
                                        "time": get_vn_time(),
                                        "name": student_name,
                                        "grade": grade,
                                        "subject": subject,
                                        "topic": diag.get("topic", "Chung"),
                                        "error_type": diag.get("error_type", "Chưa rõ"),
                                        "evaluation": diag.get("evaluation", ""),
                                        "type": "SOCRATIC_DIAGNOSTIC",
                                    }
                                    st.session_state.analytics_logs.append(entry)
                                    if sheet_webhook_url:
                                        try:
                                            requests.post(sheet_webhook_url, json=entry, timeout=5)
                                        except Exception:
                                            pass

                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": "*(Em đã nộp ảnh bài làm)*",
                                    "image": img_bytes,
                                })
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": student_fb,
                                })
                                st.session_state.socratic_analyzed_keys.add(current_key)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

    # ========== RENDER LỊCH SỬ CHAT ==========
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m.get("image"):
                st.image(m["image"], use_container_width=True)
            st.markdown(m["content"])

    # ========== NÚT GỢI Ý + CHAT INPUT ==========
    if has_chat:
        if st.button("💡 Em cần gợi ý cụ thể hơn (thầy/cô sẽ không giải hộ)", key="soc_btn_hint"):
            with st.spinner("Gia Sư AI đang nghĩ cách gợi mở khác..."):
                try:
                    prompt_hint = (
                        f"Học sinh {student_name} vẫn đang bí sau khi thầy/cô đã gợi mở. "
                        f"Hãy đưa ra MỘT ví dụ TƯƠNG TỰ (khác số liệu, cùng dạng) "
                        f"hoặc MỘT gợi ý bậc thang cụ thể hơn. "
                        f"TUYỆT ĐỐI vẫn không giải hộ bài của em. "
                        f"Ngắn gọn, tiếng Việt bình dân, dễ hiểu."
                    )
                    sys_prompt_hint = _build_socratic_system_prompt(
                        subject, grade_num, student_name, is_essay
                    )
                    rep = call_gemini_with_fallback(
                        prompt_hint, system_instruction=sys_prompt_hint
                    )
                    rep_clean = (
                        rep.split("<DIAGNOSTIC>")[0].strip()
                        if "<DIAGNOSTIC>" in rep else rep
                    )
                    if not rep_clean:
                        st.error("Không nhận được phản hồi. Vui lòng thử lại.")
                    else:
                        st.session_state.messages.append({
                            "role": "assistant", "content": rep_clean
                        })
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi phản hồi: {e}")

        if q := st.chat_input(
            "Em chưa hiểu chỗ nào, hãy hỏi Thầy nhé...",
            key="socratic_chat_input"
        ):
            st.session_state.messages.append({"role": "user", "content": q})
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                try:
                    history = st.session_state.messages[-8:]
                    dialogue_context = "\n".join([
                        f"{msg['role']}: {msg['content']}"
                        for msg in history if msg.get("content")
                    ])
                    sys_prompt_chat = _build_socratic_system_prompt(
                        subject, grade_num, student_name, is_essay
                    )
                    prompt_chat = (
                        f"Ngữ cảnh hội thoại trước:\n{dialogue_context}\n\n"
                        f"Học sinh hỏi tiếp: {q}\n"
                        f"Hãy tiếp tục phương pháp gợi mở Socratic, "
                        f"giải thích bình dân học vụ, không giải hộ:"
                    )
                    rep = call_gemini_with_fallback(
                        prompt_chat, system_instruction=sys_prompt_chat
                    )
                    rep_clean = (
                        rep.split("<DIAGNOSTIC>")[0].strip()
                        if "<DIAGNOSTIC>" in rep else rep
                    )
                    if not rep_clean:
                        st.error("Không nhận được phản hồi. Vui lòng thử lại.")
                    else:
                        st.markdown(rep_clean)
                        st.session_state.messages.append({
                            "role": "assistant", "content": rep_clean
                        })
                except Exception as e:
                    st.error(f"Lỗi phản hồi: {e}")

import streamlit as st
import google.generativeai as genai
import re
import time

# ============================================================
# 1. CẤU HÌNH GIAO DIỆN TRANG
# ============================================================
def setup_page_config():
    st.set_page_config(
        page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
        page_icon="🤖",
        layout="wide"
    )

# ============================================================
# 2. XỬ LÝ VÀ LỌC SẠCH PHẢN HỒI TỪ AI
# ============================================================
def clean_ai_response(text: str) -> str:
    """Lọc bỏ suy luận tiếng Anh, echo prompt, và rác đầu ra của AI."""
    if not text:
        return ""

    pattern = re.compile(
        r"(#{1,3}\s*)?📌?\s*1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI",
        re.IGNORECASE | re.UNICODE
    )
    match = pattern.search(text)
    if match:
        text = text[match.start():]

    text = re.sub(r'(#+ [^\n]*?)"\s*$', r'\1', text, flags=re.MULTILINE)

    lines = text.split('\n')
    filtered = []

    draft_patterns = re.compile(
        r"^\s*[\*\-\s]*("
        r"note\s*:|section\s+[ivx]+|theory|concepts|formulas|"
        r"common mistakes|interactive exercises|multiple choice\s*:|"
        r"short answer\s*:|refining|final polish|wait,|drafting|"
        r"check against|role\s*:|curriculum\s*:|topic\s*:|"
        r"no internal|let'?s go|thinking|reasoning|analysis\s*:|"
        r"step\s+\d+\s*:|here'?s|let me|i will|i'?ll"
        r")",
        re.IGNORECASE
    )

    english_paren = re.compile(r"\([A-Za-z][A-Za-z\s,;:\-]{4,}\)")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append(line)
            continue

        if draft_patterns.match(stripped):
            continue

        if english_paren.search(stripped) and len(stripped) < 200:
            cleaned = english_paren.sub("", stripped).rstrip(".,;: ")
            if cleaned:
                filtered.append(cleaned)
            continue

        if len(stripped) > 15:
            has_vietnamese = bool(re.search(
                r"[àáảãạăâđêôơưèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]",
                stripped, re.IGNORECASE
            ))
            latin_ratio = sum(
                c.isascii() and c.isalpha() for c in stripped
            ) / max(len(stripped), 1)
            if not has_vietnamese and latin_ratio > 0.5:
                continue

        filtered.append(line)

    result = '\n'.join(filtered).strip()
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result

# ============================================================
# 3. GỌI API GEMINI (CHỈ DÙNG CÁC PHIÊN BẢN FLASH MIỄN PHÍ)
# ============================================================
def call_gemini(prompt: str, api_key: str) -> tuple:
    """Tự động quét các model dòng Flash miễn phí."""
    genai.configure(api_key=api_key)
    
    # Chỉ giữ lại các phiên bản Flash và Flash-Lite miễn phí trên Google AI Studio
    model_candidates = [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b"
    ]

    generation_config = genai.types.GenerationConfig(
        temperature=0.0,
        top_p=0.85,
        max_output_tokens=8192,
    )

    last_error = ""
    for model_name in model_candidates:
        retries = 2
        for i in range(retries):
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text, model_name, ""
            except Exception as err:
                err_str = str(err)
                last_error = err_str
                if "429" in err_str and i < retries - 1:
                    time.sleep(2)
                    continue
                if "404" in err_str or "not found" in err_str.lower():
                    break
                break

    return None, "", last_error

# ============================================================
# 4. XÂY DỰNG PROMPT KHỐI KIẾN THỨC
# ============================================================
def build_lesson_prompt(lesson_input: str, subject: str, grade: str) -> str:
    return f"""Bạn là giáo viên Việt Nam soạn bài theo SGK "Kết Nối Tri Thức Với Cuộc Sống".

NHIỆM VỤ: Viết nội dung bài học "{lesson_input}" môn {subject} lớp {grade}.

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung phải bằng TIẾNG VIỆT hoàn toàn. Không chứa từ tiếng Anh.
2. KHÔNG viết suy luận nội tâm, bản nháp, hoặc các chú thích kỹ thuật.
3. CÁC PHẦN LỚN KHÔNG DÙNG DẤU #, chỉ dùng định dạng đánh số thứ tự (Ví dụ: 1. KIẾN THỨC CỐT LÕI).
4. Viết nội dung chi tiết, chuẩn xác theo chương trình giáo dục phổ thông.

CẤU TRÚC ĐẦU RA:

1. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
[Viết từ 3 đến 5 đoạn văn bằng tiếng Việt giải thích lý thuyết, bản chất và công thức cụ thể của bài.]

2. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
[Liệt kê từ 4 đến 6 lỗi sai phổ biến bằng tiếng Việt kèm giải thích ngắn gọn.]

3. BÀI TẬP TƯƠNG TÁC VÀ THỬ THÁCH

A. Dạng Trắc Nghiệm Tương Tác
Câu 1: [Đề bài cụ thể bằng tiếng Việt]
A. [Đáp án]
B. [Đáp án]
C. [Đáp án]
D. [Đáp án]

<details>
<summary>Hướng dẫn từng bước (Nhấp để xem khi cần)</summary>
- Bước 1: [Hướng dẫn giải]
- Bước 2: [Hướng dẫn tiếp theo]
- Gợi ý: [Gợi ý tư duy, không tiết lộ trực tiếp đáp án]
</details>

B. Dạng Tự Luận Trả Lời Ngắn
Câu 2: [Đề bài cụ thể bằng tiếng Việt]

<details>
<summary>Hướng dẫn từng bước (Nhấp để xem khi cần)</summary>
- Bước 1: [Hướng dẫn giải]
- Bước 2: [Hướng dẫn tiếp theo]
</details>
"""

# ============================================================
# 5. GIAO DIỆN THANH BÊN (SIDEBAR)
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.header("⚙️ THIẾT LẬP HỌC TẬP")

        with st.expander("📲 Quét mã QR vào ứng dụng"):
            app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
            st.image(qr_api_url, caption="Quét mã để mở trên điện thoại", width=200)
            st.markdown(f"🔗 **Hoặc nhấn vào đường dẫn:** [{app_url}]({app_url})")

        st.markdown("---")
        st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
        name = st.text_input("Họ và tên:", placeholder="Ví dụ: Nguyễn Văn A")

        st.markdown("---")
        st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
        st.link_button(
            "👉 Lấy Mã Riêng Miễn Phí (15 giây)",
            "https://aistudio.google.com/app/apikey",
            use_container_width=True
        )

        user_api_key = st.text_input(
            "Dán Mã Kết Nối (API Key):",
            type="password",
            placeholder="Nhập mã bí mật tại đây..."
        )

        if user_api_key:
            st.success("🟢 Đang sử dụng đường truyền AI Cá nhân")
            api_key_to_use = user_api_key
        else:
            st.info("🔵 Đang sử dụng đường truyền chung của Trường")
            try:
                api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
            except Exception:
                api_key_to_use = ""

        st.markdown("<br>", unsafe_allow_html=True)

        grade = st.selectbox(
            "Chọn khối lớp",
            ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
            index=5
        )

        subject = st.selectbox(
            "Môn học cần hỗ trợ",
            ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học",
             "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
            index=0
        )

        st.markdown("---")
        st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")
        return grade, subject, api_key_to_use

# ============================================================
# 6. GIAO DIỆN CHÍNH VÀ LUỒNG XỬ LÝ TRẠM 1
# ============================================================
def render_main_interface(grade, subject, api_key_to_use):
    st.markdown(
        "<h1 style='text-align: center; color: #1E88E5;'>"
        "🤖 GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 18px; font-weight: bold;'>"
        "Trường THPT Tân Hiệp</p>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💡 Trạm 1: Học Tập & Phòng Thí Nghiệm",
        "✍️ Trạm 2: Gia Sư Tương Tác",
        "🏆 Trạm 3: Khảo Thí Tự Do",
        "📊 Trạm 4: Nhật Ký Nghiên Cứu",
        "📉 Trạm 5: Thống Kê & Đánh Giá"
    ])

    with tab1:
        st.markdown(f"# 📖 TỰ HỌC & CHIẾM LĨNH KIẾN THỨC: MÔN {subject.upper()} - {grade.upper()}")
        st.markdown("### 📝 **Nhập tên bài học em muốn tổng hợp:**")
        
        lesson_input = st.text_input(
            "Nhập bài học cần chiếm lĩnh kiến thức:",
            placeholder="Ví dụ: Đồ thị hàm số bậc hai...",
            label_visibility="collapsed"
        )

        btn_soan_bai = st.button("🧪 Tổng Hợp Kiến Thức Cốt Lõi", type="primary")

        if btn_soan_bai:
            if not lesson_input.strip():
                st.warning("⚠️ Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
            elif not api_key_to_use:
                st.error("🔑 Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
            else:
                with st.spinner(f"⏳ AI đang phân tích bài: **{lesson_input}**..."):
                    full_prompt = build_lesson_prompt(lesson_input, subject, grade)
                    response_text, model_used, error = call_gemini(full_prompt, api_key_to_use)

                    if response_text:
                        final_text = clean_ai_response(response_text)
                        st.success(f"✅ Đã hoàn thành tổng hợp kiến thức bài: **{lesson_input}**")
                        st.caption(f"🤖 Model Flash đã kết nối thành công: `{model_used}`")
                        st.markdown("---")
                        st.markdown(final_text, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ Không thể kết nối AI. Lỗi chi tiết: `{error}`")

# ============================================================
# 7. KHỞI CHẠY ỨNG DỤNG CHÍNH
# ============================================================
def main():
    setup_page_config()
    grade, subject, api_key_to_use = render_sidebar()
    render_main_interface(grade, subject, api_key_to_use)

if __name__ == "__main__":
    main()

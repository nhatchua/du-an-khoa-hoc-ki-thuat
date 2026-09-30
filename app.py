import streamlit as st
import google.generativeai as genai
import re

# ============================================================
# 1. CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# 2. HÀM LỌC SẠCH PHẢN HỒI AI (NÂNG CẤP)
# ============================================================
def clean_ai_response(text: str) -> str:
    """Lọc bỏ suy luận tiếng Anh, echo prompt, và rác đầu ra của AI."""
    if not text:
        return ""

    # --- Bước 1: Cắt phần rác trước tiêu đề bài học ---
    pattern = re.compile(
        r"(#{1,3}\s*)?📌?\s*I\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI",
        re.IGNORECASE | re.UNICODE
    )
    match = pattern.search(text)
    if match:
        text = text[match.start():]

    # --- Bước 2: Xóa dấu " thừa ở cuối tiêu đề ---
    text = re.sub(r'(#+ [^\n]*?)"\s*$', r'\1', text, flags=re.MULTILINE)

    lines = text.split('\n')
    filtered = []

    # Pattern nháp / echo prompt
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

    # Pattern ngoặc tiếng Anh: "(Theory, concepts, formulas)"
    english_paren = re.compile(r"\([A-Za-z][A-Za-z\s,;:\-]{4,}\)")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append(line)
            continue

        # Bỏ dòng nháp / echo
        if draft_patterns.match(stripped):
            continue

        # Xóa ngoặc tiếng Anh trong tiêu đề
        if english_paren.search(stripped) and len(stripped) < 200:
            cleaned = english_paren.sub("", stripped).rstrip(".,;: ")
            if cleaned:
                filtered.append(cleaned)
            continue

        # Bỏ dòng toàn tiếng Anh (không dấu tiếng Việt)
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
    # Gộp nhiều dòng trống liên tiếp
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


# ============================================================
# 3. HÀM GỌI GEMINI — HARD-CODE MODEL 2.0-FLASH
# ============================================================
def call_gemini(prompt: str, api_key: str) -> tuple:
    """
    Gọi Gemini 2.0 Flash (KHÔNG có thinking → không rác tiếng Anh).
    Fallback sang 2.0-flash-lite nếu model chính lỗi.
    Trả về (text, model_used, error).
    """
    genai.configure(api_key=api_key)

    # Ưu tiên 2.0-flash (không thinking). 2.5-flash để cuối vì có thinking.
    model_priority = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-001",
        "gemini-1.5-flash",
        "gemini-2.5-flash",
    ]

    generation_config = genai.types.GenerationConfig(
        temperature=0.0,
        top_p=0.85,
        max_output_tokens=8192,
    )

    last_error = ""
    for model_name in model_priority:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text, model_name, ""
        except Exception as err:
            last_error = f"{model_name}: {err}"
            continue

    return None, "", last_error


# ============================================================
# 4. THANH BÊN (SIDEBAR)
# ============================================================
with st.sidebar:
    st.header("⚙️ THIẾT LẬP HỌC TẬP")

    with st.expander("📲 Quét mã QR vào ứng dụng bằng điện thoại"):
        st.write("Dùng máy ảnh điện thoại để quét mã bên dưới:")
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

    st.markdown("🎯 **Chọn khối lớp:**")
    grade = st.selectbox(
        "Chọn khối lớp",
        ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
        index=5,
        label_visibility="collapsed"
    )

    st.markdown("📚 **Môn học cần hỗ trợ:**")
    subject = st.selectbox(
        "Môn học cần hỗ trợ",
        ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học",
         "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    with st.expander("🛠️ Báo lỗi ứng dụng & Góp ý"):
        issue_type = st.selectbox(
            "Loại vấn đề gặp phải:",
            [
                "📷 Lỗi nhận diện chữ viết tay / hình ảnh",
                "📊 Lỗi hiển thị đồ thị / Phòng Thí Nghiệm Ảo",
                "🧠 AI giải thích khó hiểu / chưa sát Sách Giảng Dạy",
                "⏳ Ứng dụng phản hồi chậm / quá tải",
                "💡 Đề xuất tính năng mới",
                "❓ Lỗi khác..."
            ],
            label_visibility="collapsed"
        )
        rating = st.feedback("stars")
        feedback_text = st.text_area(
            "Mô tả chi tiết:",
            placeholder="Mô tả cụ thể vấn đề em gặp phải...",
            label_visibility="collapsed"
        )
        if st.button("📩 Gửi phản hồi", use_container_width=True):
            if feedback_text.strip():
                st.success(
                    f"Đã gửi phản hồi thành công! "
                    f"(Loại: {issue_type} • Đánh giá: {rating if rating else 'chưa chọn'}/5)"
                )
            else:
                st.warning("Vui lòng nhập nội dung trước khi gửi!")

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")


# ============================================================
# 5. KHU VỰC CHÍNH
# ============================================================
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

col_b1, col_b2, col_b3, col_b4 = st.columns([1, 2, 2, 1])
with col_b2:
    st.info("📚 Bộ sách: Kết Nối Tri Thức Với Cuộc Sống")
with col_b3:
    st.success("🎯 Chuẩn Chương Trình Giáo Dục Phổ Thông 2018")

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💡 Trạm 1: Học Tập & Phòng Thí Nghiệm",
    "✍️ Trạm 2: Gia Sư Tương Tác",
    "🏆 Trạm 3: Khảo Thí Tự Do",
    "📊 Trạm 4: Nhật Ký Nghiên Cứu",
    "📉 Trạm 5: Thống Kê & Đánh Giá"
])


# ============================================================
# TRẠM 1: TỰ HỌC & CHIẾM LĨNH KIẾN THỨC
# ============================================================
with tab1:
    st.markdown(
        f"# 📖 TỰ HỌC & CHIẾM LĨNH KIẾN THỨC: "
        f"MÔN {subject.upper()} - {grade.upper()}"
    )

    st.markdown("### 📝 **Nhập tên bài học em muốn tổng hợp:**")
    lesson_input = st.text_input(
        "Nhập bài học cần chiếm lĩnh kiến thức:",
        placeholder="Ví dụ: Đồ thị hàm số bậc hai, Hàm số lượng giác...",
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

                # ============================================
                # PROMPT FEW-SHOT — CHỐNG ECHO PROMPT
                # ============================================
                full_prompt = f"""Bạn là giáo viên Việt Nam soạn bài theo SGK "Kết Nối Tri Thức Với Cuộc Sống".

NHIỆM VỤ: Viết nội dung bài học "{lesson_input}" môn {subject} lớp {grade}.

═══════════════════════════════════════════════════
QUY TẮC BẮT BUỘC (vi phạm = thất bại):
═══════════════════════════════════════════════════
1. TOÀN BỘ nội dung phải bằng TIẾNG VIỆT. Không dùng tiếng Anh.
2. KHÔNG viết "Note:", "Section", "(Theory)", "(concepts)", "(formulas)".
3. KHÔNG liệt kê lại cấu trúc. KHÔNG echo lại yêu cầu này.
4. KHÔNG viết suy luận nội tâm, draft, hay thinking.
5. Bắt đầu ngay bằng dòng: # 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
6. Viết nội dung CỤ THỂ cho bài học, KHÔNG viết chung chung.

═══════════════════════════════════════════════════
CẤU TRÚC ĐẦU RA (tuân thủ chính xác):
═══════════════════════════════════════════════════

# 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
[Viết 3-5 đoạn văn tiếng Việt giải thích lý thuyết, công thức, khái niệm cụ thể của bài.]

# ⚠️ II. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
[Liệt kê 4-6 lỗi sai bằng tiếng Việt. Mỗi lỗi 1-2 câu giải thích ngắn gọn.]

# ✍️ III. BÀI TẬP TƯƠNG TÁC & THỬ THÁCH

## 1. Dạng Trắc Nghiệm Tương Tác

**Câu 1:** [Đề bài tiếng Việt cụ thể]
A. [đáp án]
B. [đáp án]
C. [đáp án]
D. [đáp án]

<details>
<summary>🔍 Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</summary>

- **Bước 1:** [hướng dẫn tiếng Việt]
- **Bước 2:** [hướng dẫn tiếng Việt]
- **Gợi ý:** [hướng dẫn cách chọn, TUYỆT ĐỐI không tiết lộ đáp án A/B/C/D]
</details>

<br>

## 2. Dạng Tự Luận Trả Lời Ngắn

**Câu 2:** [Đề bài tiếng Việt]

<details>
<summary>🔍 Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</summary>

- **Bước 1:** [hướng dẫn]
- **Bước 2:** [hướng dẫn]
- **Thử thách:** [câu hỏi cuối]
</details>

═══════════════════════════════════════════════════
VÍ DỤ MẪU VỀ CÁCH VIẾT ĐÚNG (tham khảo văn phong):
═══════════════════════════════════════════════════

# 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ

Hàm số bậc hai có dạng y = ax² + bx + c (a ≠ 0). Đồ thị là một parabol có đỉnh tại điểm I(-b/2a; -Δ/4a). Trục đối xứng là đường thẳng x = -b/2a.

Nếu a > 0, parabol hướng bề lõm lên trên. Nếu a < 0, parabol hướng bề lõm xuống dưới.

# ⚠️ II. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI

1. Nhầm lẫn giữa hoành độ và tung độ của đỉnh.
2. Quên điều kiện a ≠ 0 khi xác định hàm bậc hai.
3. Tính sai dấu của Δ khi áp dụng công thức.

# ✍️ III. BÀI TẬP TƯƠNG TÁC & THỬ THÁCH

## 1. Dạng Trắc Nghiệm Tương Tác

**Câu 1:** Đỉnh của parabol y = x² - 4x + 3 có tọa độ là:
A. (2; -1)
B. (-2; 1)
C. (2; 1)
D. (-2; -1)

<details>
<summary>🔍 Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</summary>

- **Bước 1:** Xác định a = 1, b = -4, c = 3.
- **Bước 2:** Hoành độ đỉnh x = -b/2a = 4/2 = 2.
- **Gợi ý:** Thay x = 2 vào hàm số để tìm y, so sánh với 4 đáp án.
</details>

═══════════════════════════════════════════════════
BẮT ĐẦU VIẾT NGAY. KHÔNG viết lời dẫn. KHÔNG viết tiếng Anh.
═══════════════════════════════════════════════════
"""

                response_text, model_used, error = call_gemini(
                    full_prompt, api_key_to_use
                )

                if response_text:
                    final_text = clean_ai_response(response_text)
                    st.success(
                        f"✅ Đã hoàn thành tổng hợp kiến thức bài: "
                        f"**{lesson_input}** ({subject} - {grade})"
                    )
                    st.caption(f"🤖 Model: `{model_used}`")
                    st.markdown("---")
                    st.markdown(final_text, unsafe_allow_html=True)

                    # --- Debug panel (có thể xóa khi deploy chính thức) ---
                    with st.expander("🐛 Debug: Raw AI Response (dành cho Admin)"):
                        st.code(response_text, language="markdown")
                else:
                    st.error(f"❌ Không thể kết nối AI. Lỗi chi tiết: `{error}`")

    st.markdown("---")

    st.markdown(
        """
        <div style="border: 2px solid #1E88E5; padding: 20px; border-radius: 10px;
                    text-align: center; margin-bottom: 15px; background-color: #0E1117;">
            <h1 style="margin: 0; color: #FFFFFF; font-size: 28px;">
            🔬 PHÒNG THÍ NGHIỆM ẢO</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    lab_input = st.text_input(
        "Mô tả thí nghiệm:",
        placeholder="Ví dụ: Khảo sát đồ thị hàm số bậc 3...",
        label_visibility="collapsed"
    )

    btn_lab = st.button("⚙️ Khởi Chạy Mô Phỏng", type="primary")
    if btn_lab:
        if not lab_input.strip():
            st.warning("⚠️ Vui lòng nhập mô tả thí nghiệm!")
        else:
            st.info(f"🔬 Đang chuẩn bị mô phỏng: **{lab_input}**... (tính năng đang phát triển)")


# ============================================================
# CÁC TRẠM CÒN LẠI
# ============================================================
with tab2:
    st.subheader("Trạm 2: Gia Sư Tương Tác")
    st.write(f"Gia sư AI sẵn sàng đặt câu hỏi gợi mở môn **{subject} ({grade})**...")

with tab3:
    st.subheader("Trạm 3: Khảo Thí Tự Do")
    st.write(f"Khu vực luyện tập và tự kiểm tra môn **{subject} ({grade})**...")

with tab4:
    st.subheader("Trạm 4: Nhật Ký Nghiên Cứu Khoa Học")
    st.write("Theo dõi và ghi chép tiến độ dự án...")

with tab5:
    st.warning("🔒 Trạm Thống Kê & Đánh Giá bị khóa. Vui lòng đăng nhập ở Trạm 4 trước.")

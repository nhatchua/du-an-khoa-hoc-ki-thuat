import streamlit as st
import google.generativeai as genai
import re

# 1. Cấu hình trang
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# HÀM LỌC SẠCH PHẢN HỒI AI (CẢI TIẾN)
# ============================================================
def clean_ai_response(text: str) -> str:
    """Lọc bỏ suy luận tiếng Anh và rác đầu ra của AI."""
    if not text:
        return ""
    
    # 1. Cắt phần rác trước tiêu đề bài học (dùng regex linh hoạt)
    #    Chấp nhận #, ##, ###, khoảng trắng, dấu hai chấm tùy ý
    pattern = re.compile(
        r"(#{1,3}\s*)?📌?\s*I\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI",
        re.IGNORECASE | re.UNICODE
    )
    match = pattern.search(text)
    if match:
        text = text[match.start():]
    
    # 2. Lọc bỏ các dòng nháp tiếng Anh
    lines = text.split('\n')
    filtered_lines = []
    
    # Pattern nháp — CHỈ khớp khi dòng BẮT ĐẦU bằng các từ khóa này
    # (tránh xóa oan dòng tiếng Việt có chứa từ khóa ở giữa)
    draft_start_patterns = re.compile(
        r"^\s*(refining|final polish|wait,|drafting|check against|"
        r"role:|curriculum:|topic:|no internal|let's go|"
        r"multiple choice:|short answer:|question:|hint:|"
        r"thinking|reasoning|analysis:|step \d+:)",
        re.IGNORECASE
    )
    
    for line in lines:
        if draft_start_patterns.match(line):
            continue
        filtered_lines.append(line)
    
    result = '\n'.join(filtered_lines).strip()
    
    # 3. Xóa các dòng tiếng Anh thuần túy (>= 5 từ tiếng Anh liên tiếp)
    #    Đây là lớp bảo vệ cuối cùng
    final_lines = []
    english_line_pattern = re.compile(
        r"^[A-Za-z0-9\s\.,;:'\"\-\(\)\[\]\{\}\?\!/\\]{25,}$"
    )
    for line in result.split('\n'):
        stripped = line.strip()
        # Nếu dòng toàn tiếng Anh/không dấu và dài → nghi là draft
        if stripped and english_line_pattern.match(stripped):
            # Kiểm tra có ký tự tiếng Việt không
            if not re.search(r"[àáảãạăâđêôơưèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", stripped, re.IGNORECASE):
                continue
        final_lines.append(line)
    
    return '\n'.join(final_lines).strip()


# ============================================================
# HÀM GỌI AI VỚI FALLBACK NHIỀU MODEL
# ============================================================
def call_gemini(prompt: str, api_key: str) -> tuple[str | None, str]:
    """Gọi Gemini với danh sách model ưu tiên. Trả về (text, error)."""
    genai.configure(api_key=api_key)
    
    # Danh sách model ưu tiên — 2.0-flash KHÔNG có thinking → sạch tiếng Anh
    preferred_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-2.5-flash",  # fallback cuối (có thinking)
    ]
    
    # Lọc theo model thực tế khả dụng
    try:
        available = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        # Chuẩn hóa tên: bỏ tiền tố "models/"
        available_short = [a.replace("models/", "") for a in available]
        # Ưu tiên model trong danh sách preferred, còn lại thêm vào cuối
        ordered = [m for m in preferred_models if m in available_short]
        ordered += [m for m in available_short if m not in ordered]
    except Exception:
        ordered = preferred_models
    
    generation_config = genai.types.GenerationConfig(
        temperature=0.0,
        top_p=0.8,
    )
    
    last_error = ""
    for model_name in ordered:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text, ""
        except Exception as err:
            last_error = f"{model_name}: {err}"
            continue
    
    return None, last_error


# ============================================================
# 2. THANH BÊN
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
                # TODO: gửi feedback_text + issue_type + rating đến backend
                st.success(f"Đã gửi phản hồi thành công! (Đánh giá: {rating}/5)")
            else:
                st.warning("Vui lòng nhập nội dung trước khi gửi!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")


# ============================================================
# 3. KHU VỰC CHÍNH
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
# TRẠM 1
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
                # Prompt cải tiến — chặn suy luận từ đầu
                full_prompt = f"""BẠN LÀ GIÁO VIÊN SOẠN BÀI THEO SGK "KẾT NỐI TRI THỨC VỚI CUỘC SỐNG" TẠI VIỆT NAM.

QUY TẮC BẮT BUỘC (vi phạm sẽ bị loại):
1. KHÔNG viết bất kỳ suy luận nội tâm, draft, ghi chú, hay thinking nào.
2. KHÔNG viết tiếng Anh dưới bất kỳ hình thức nào.
3. KHÔNG viết lời chào, lời dẫn, hay kết luận ngoài cấu trúc.
4. Bắt đầu trả lời NGAY bằng dòng: "# 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ"
5. Nếu cần suy luận, hãy suy luận trong im lặng và chỉ xuất kết quả cuối cùng.

BÀI HỌC: "{lesson_input}"
MÔN: {subject}
KHỐI: {grade}

TRÌNH BÀY CHÍNH XÁC THEO CẤU TRÚC SAU:

# 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
(Trình bày chi tiết lý thuyết, khái niệm và công thức cốt lõi)

# ⚠️ II. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
(Liệt kê các lỗi sai phổ biến học sinh hay mắc phải)

# ✍️ III. BÀI TẬP TƯƠNG TÁC & THỬ THÁCH

## 1. Dạng Trắc Nghiệm Tương Tác
**Câu 1:** (Đề bài câu hỏi trắc nghiệm)
A. ...
B. ...
C. ...
D. ...

<details>
<summary>🔍 <b>Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

- **Bước 1:** ...
- **Bước 2:** ...
- **Gợi ý lựa chọn:** Hướng dẫn cách phân tích để tìm đáp án đúng. Tuyệt đối không tiết lộ đáp án là A, B, C hay D.
</details>

<br>

## 2. Dạng Tự Luận Trả Lời Ngắn
**Câu 2:** (Đề bài tự luận)

<details>
<summary>🔍 <b>Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

- **Gợi ý bước 1:** ...
- **Gợi ý bước 2:** ...
- **Thử thách học sinh:** Em hãy tính kết quả cuối cùng = ...?
</details>
"""
                
                response_text, error = call_gemini(full_prompt, api_key_to_use)
                
                if response_text:
                    final_text = clean_ai_response(response_text)
                    st.success(
                        f"✅ Đã hoàn thành tổng hợp kiến thức bài: "
                        f"**{lesson_input}** ({subject} - {grade})"
                    )
                    st.markdown("---")
                    st.markdown(final_text, unsafe_allow_html=True)
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

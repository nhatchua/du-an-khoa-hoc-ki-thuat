import streamlit as st
import google.generativeai as genai

# 1. Cấu hình trang
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)

# HÀM LỌC SẠCH VÀ CHẶN DỨT ĐIỂM CÁC DÒNG RÁC
def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    
    # Cắt bỏ nếu có dấu hiệu rác ở đầu
    lower_text = text.lower()
    for keyword in ["role:", "language:", "constraint:", "check:", "refining", "let's write"]:
        idx = lower_text.find(keyword)
        if idx != -1:
            text = text[idx + len(keyword):]
            lower_text = text.lower()

    forbidden_phrases = [
        "role:", "language:", "constraint:", "standard vietnamese", 
        "no english", "internal monologue", "textbook series"
    ]
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line_str = line.strip()
        line_lower = line_str.lower()
        is_bad = any(phrase in line_lower for phrase in forbidden_phrases)
        
        if not is_bad and line_str:
            filtered_lines.append(line)
            
    return '\n'.join(filtered_lines).strip()


# 2. Thanh bên (Sidebar)
with st.sidebar:
    st.header("⚙️ THIẾT LẬP HỌC TẬP")
    
    with st.expander("📲 Quét mã QR vào ứng dụng bằng điện thoại"):
        st.write("Dùng máy ảnh điện thoại để quét mã bên dưới để truy cập nhanh:")
        app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        st.image(qr_api_url, caption="Quét mã để mở trên điện thoại", width=200)
        st.markdown(f"🔗 **Hoặc nhấn vào đường dẫn:** [{app_url}]({app_url})")
    
    st.markdown("---")
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Không bắt buộc):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    
    st.link_button(
        "👉 Lấy Mã Riêng Miễn Phí (15 giây)", 
        "https://aistudio.google.com/app/apikey", 
        use_container_width=True
    )
    
    user_api_key = st.text_input(
        "Dán Mã Kết Nối (API Key) của em vào đây:", 
        type="password", 
        placeholder="Nhập mã bí mật tại đây..."
    )
    
    if user_api_key:
        st.success("🟢 Đang sử dụng đường truyền AI Cá nhân")
        api_key_to_use = user_api_key
    else:
        st.info("🔵 Đang sử dụng đường truyền chung của Trường")
        api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
        
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
        ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
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
        if st.button("📩 Gửi phản hồi đến Thầy", use_container_width=True):
            if feedback_text or issue_type:
                st.success("Cảm ơn em! Phản hồi đã được gửi thành công.")
            else:
                st.warning("Vui lòng nhập nội dung trước khi gửi!")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")


# 3. Khu vực chính
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🤖 GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; font-weight: bold;'>Trường THPT Tân Hiệp</p>", unsafe_allow_html=True)

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

# TRẠM 1: TỰ HỌC & CHIẾM LĨNH KIẾN THỨC
with tab1:
    st.markdown(f"# 📖 TỰ HỌC & CHIẾM LĨNH KIẾN THỨC: MÔN {subject.upper()} - {grade.upper()}")
    
    st.markdown("### 📝 **Nhập tên bài học em muốn tổng hợp:**")
    lesson_input = st.text_input(
        "Nhập bài học cần chiếm lĩnh kiến thức:",
        placeholder="Ví dụ: Đồ thị hàm số bậc hai, Hàm số lượng giác, Mạch điện xoay chiều...",
        label_visibility="collapsed"
    )
    
    btn_soan_bai = st.button("🧪 Tổng Hợp Kiến Thức Cốt Lõi", type="primary")
    
    if btn_soan_bai:
        if not lesson_input.strip():
            st.warning("⚠️ Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
        elif not api_key_to_use:
            st.error("🔑 Chưa phát hiện Mã Kết Nối! Vui lòng dán Mã Kết Nối (API Key) ở thanh bên trái để kích hoạt AI.")
        else:
            with st.spinner(f"⏳ AI đang phân tích dữ liệu chuẩn SGK 'Kết Nối Tri Thức Với Cuộc Sống' cho bài: **{lesson_input}**..."):
                genai.configure(api_key=api_key_to_use)
                
                # Tự động quét model từ API key để tránh lỗi 404
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                except Exception:
                    pass
                
                if not available_models:
                    available_models = [
                        "gemini-2.5-flash",
                        "gemini-2.0-flash",
                        "models/gemini-2.5-flash",
                        "models/gemini-2.0-flash"
                    ]
                
                full_prompt = f"""
Hãy đóng vai một giáo viên giỏi soạn nội dung học tập theo chương trình sách giáo khoa Kết Nối Tri Thức Với Cuộc Sống tại Việt Nam. 
Hãy viết toàn bộ nội dung sau hoàn toàn bằng tiếng Việt chuẩn xác, tuyệt đối không dùng tiếng Anh, không giải thích dài dòng ngoài lề, không viết câu suy luận nội tâm:

Em hãy soạn nội dung kiến thức cho bài học: "{lesson_input}" thuộc môn {subject} ({grade}).

Trình bày chính xác theo cấu trúc sau:

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
                
                generation_config = genai.types.GenerationConfig(
                    temperature=0.0,
                    top_p=0.8
                )
                
                response_text = None
                last_error = ""
                
                for model_name in available_models:
                    try:
                        model = genai.GenerativeModel(model_name=model_name)
                        response = model.generate_content(
                            full_prompt,
                            generation_config=generation_config
                        )
                        if response and response.text:
                            response_text = response.text
                            break
                    except Exception as err:
                        last_error = str(err)
                        continue
                
                if response_text:
                    final_text = clean_ai_response(response_text)
                    st.success(f"✅ Đã hoàn thành tổng hợp kiến thức bài: **{lesson_input}** ({subject} - {grade})")
                    st.markdown("---")
                    st.markdown(final_text, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Không thể kết nối AI. Lỗi chi tiết: `{last_error}`")

    st.markdown("---")
    
    st.markdown(
        """
        <div style="border: 2px solid #1E88E5; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 15px; background-color: #0E1117;">
            <h1 style="margin: 0; color: #FFFFFF; font-size: 28px;">🔬 PHÒNG THÍ NGHIỆM ẢO</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    lab_input = st.text_input(
        "Ví dụ: Mô phỏng chuyển động ném ngang...",
        placeholder="Ví dụ: Khảo sát đồ thị hàm số bậc 3, Mô phỏng chuyển động ném ngang...",
        label_visibility="collapsed"
    )
    
    st.button("⚙️ Khởi Chạy Mô Phỏng", type="primary")

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

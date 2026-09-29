import streamlit as st
import google.generativeai as genai

# 1. Cấu hình trang (Giao diện rộng)
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)

# 2. Thanh bên (Sidebar) - THIẾT LẬP HỌC TẬP
with st.sidebar:
    st.header("THIẾT LẬP HỌC TẬP")
    
    # Hộp quét mã QR vào app
    with st.expander("📲 Quét mã QR vào app trên điện thoại"):
        st.write("Dùng camera điện thoại để quét mã bên dưới để truy cập nhanh:")
        app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        st.image(qr_api_url, caption="Quét mã để mở trên điện thoại", width=200)
        st.markdown(f"🔗 **Hoặc bấm vào link:** [{app_url}]({app_url})")
    
    st.markdown("---")
    
    # THÔNG TIN HỌC SINH
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Tùy chọn):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    
    # ĐƯỜNG TRUYỀN AI CÁ NHÂN
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    
    st.link_button(
        "👉 Lấy Key riêng miễn phí (15s)", 
        "https://aistudio.google.com/app/apikey", 
        use_container_width=True
    )
    
    user_api_key = st.text_input(
        "Dán mã API Key của em vào đây:", 
        type="password", 
        placeholder="AIzaSy..."
    )
    
    if user_api_key:
        st.success("🟢 Đang dùng đường truyền AI Cá nhân")
        api_key_to_use = user_api_key
    else:
        st.info("🔵 Đang dùng đường truyền chung của Trường")
        api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CHỌN KHỐI LỚP & MÔN HỌC
    st.markdown("🎯 **Chọn khối lớp:**")
    grade = st.selectbox(
        "Chọn khối lớp",
        ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
        index=5, # Mặc định chọn Lớp 11
        label_visibility="collapsed"
    )
    
    st.markdown("📚 **Môn học cần hỗ trợ:**")
    subject = st.selectbox(
        "Môn học cần hỗ trợ",
        ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
        index=0, # Mặc định chọn Toán học
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # BÁO LỖI & GÓP Ý
    with st.expander("🛠️ Báo lỗi ứng dụng & Góp ý"):
        issue_type = st.selectbox(
            "Loại vấn đề gặp phải:",
            [
                "📷 Lỗi nhận diện chữ viết tay / hình ảnh",
                "📊 Lỗi hiển thị đồ thị / Phòng Lab ảo",
                "🧠 AI giải thích khó hiểu / chưa sát SGK",
                "⏳ Ứng dụng phản hồi chậm / quá tải",
                "💡 Đề xuất tính năng mới",
                "❓ Lỗi khác..."
            ],
            label_visibility="collapsed"
        )
        rating = st.feedback("stars")
        feedback_text = st.text_area(
            "Mô tả chi tiết:",
            placeholder="Mô tả cụ thể vấn đề...",
            label_visibility="collapsed"
        )
        if st.button("📩 Gửi phản hồi đến Thầy", use_container_width=True):
            if feedback_text or issue_type:
                st.success("Cảm ơn em! Phản hồi đã được gửi đến Thầy.")
            else:
                st.warning("Vui lòng nhập thông tin trước khi gửi!")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")


# 3. Khu vực chính (Main Content)
st.markdown("<h1 style='text-align: center;'>🤖 GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>Trường THPT Tân Hiệp</p>", unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4 = st.columns([1, 2, 2, 1])
with col_b2:
    st.info("📚 Bộ sách: Kết Nối Tri Thức Với Cuộc Sống")
with col_b3:
    st.success("🎯 Chuẩn CT GDPT 2018 / Định dạng 2025")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Hệ thống Trạm (Tabs)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💡 Trạm 1: Học Tập & Phòng Lab",
    "✍️ Trạm 2: Gia Sư Socratic",
    "🏆 Trạm 3: Khảo Thí Tự Do",
    "📊 Trạm 4: Nhật Ký KHKT",
    "📉 Trạm 5: Thống Kê & T-Test"
])

# TRẠM 1: TỰ HỌC & CHIẾM LĨNH KIẾN THỨC
with tab1:
    st.markdown(f"## 📖 Tự học & Chiếm lĩnh kiến thức môn {subject} - {grade}")
    
    lesson_input = st.text_input(
        "Nhập bài học cần chiếm lĩnh kiến thức:",
        placeholder="Ví dụ: Khảo sát hàm số, Hình chóp, Mạch điện xoay chiều...",
        label_visibility="collapsed"
    )
    
    btn_soan_bai = st.button("🧪 Soạn bài học chuẩn GDPT 2018", type="primary")
    
    if btn_soan_bai:
        if not lesson_input.strip():
            st.warning("⚠️ Vui lòng nhập tên bài học trước khi bấm soạn bài!")
        elif not api_key_to_use:
            st.error("🔑 Chưa phát hiện API Key! Vui lòng nhập API Key ở thanh bên (Sidebar) để kích hoạt AI.")
        else:
            with st.spinner(f"⏳ AI đang phân tích dữ liệu chuẩn Sách SGK 'Kết nối tri thức với cuộc sống' cho bài: **{lesson_input}**..."):
                genai.configure(api_key=api_key_to_use)
                
                # 1. Tự động lấy danh sách các model khả dụng từ API Key
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                except Exception as e:
                    pass
                
                # 2. Nếu không lấy được danh sách động, dùng danh sách dự phòng chuẩn
                if not available_models:
                    available_models = [
                        "gemini-2.5-flash",
                        "gemini-2.0-flash",
                        "gemini-1.5-flash",
                        "models/gemini-2.5-flash",
                        "models/gemini-2.0-flash",
                        "models/gemini-1.5-flash"
                    ]
                
                system_prompt = f"""
                Bạn là một Chuyên gia Giáo dục & Giáo viên Giỏi bậc THPT tại Việt Nam.
                Nhiệm vụ của bạn là soạn bài hướng dẫn tự học cho học sinh theo đúng chuẩn Chương trình GDPT 2018 và bộ sách SGK 'Kết nối tri thức với cuộc sống'.

                THÔNG TIN ĐẦU VÀO:
                - Môn học: {subject}
                - Khối lớp: {grade}
                - Tên bài học: {lesson_input}

                YÊU CẦU NỘI DUNG (NGHIÊM CẶT CHỐNG ẢO GIÁC - HALLUCINATION):
                1. CHÍNH XÁC ABSOLUTE: Mọi khái niệm, công thức, định lý, tên gọi phải chính xác tuyệt đối 100% theo chương trình SGK Kết nối tri thức với cuộc sống. Không tự bịa ra kiến thức chưa kiểm chứng.
                2. CẤU TRÚC BÀI HỌC Chuẩn GDPT 2018:
                   - 📌 **I. MỤC TIÊU BÀI HỌC**: (Kiến thức, Năng lực, Phẩm chất)
                   - 🎯 **II. KIẾN THỨC TRỌNG TÂM (SGK Kết nối tri thức)**: Tóm tắt lý thuyết cốt lõi, công thức quan trọng (trình bày công thức Toán/Lý/Hóa bằng LaTeX rõ ràng).
                   - 💡 **III. VÍ DỤ MINH HỌA & VẬN DỤNG**: 2-3 ví dụ có lời giải chi tiết, rõ ràng từng bước.
                   - ⚠️ **IV. CÁC LỖI SAI THƯỜNG GẶP**: Điểm học sinh hay bị nhầm lẫn khi làm bài.
                   - ❓ **V. CÂU HỎI TỰ KIỂM TRA (Socratic)**: 3 câu hỏi trắc nghiệm hoặc tự luận ngắn để học sinh tự đánh giá mức độ hiểu bài.

                MÔI TRƯỜNG HIỂN THỊ: Trình bày bằng Markdown đẹp mắt, mạch lạc, dễ đọc.
                """
                
                response_text = None
                used_model_name = ""
                last_error = ""
                
                # 3. Chạy qua các model lấy được
                for model_name in available_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(system_prompt)
                        if response and response.text:
                            response_text = response.text
                            used_model_name = model_name
                            break
                    except Exception as err:
                        last_error = str(err)
                        continue
                
                if response_text:
                    st.success(f"✅ Đã hoàn thành soạn bài học: **{lesson_input}** ({subject} - {grade}) - Mô hình AI: `{used_model_name}`")
                    st.markdown("---")
                    st.markdown(response_text)
                else:
                    st.error(f"❌ Không thể kết nối AI. Lỗi từ Google API: `{last_error}`")
                    st.info("💡 **Mẹo:** Kiểm tra lại API Key ở Sidebar. Nếu là Key mới tạo, Nhật hãy đảm bảo đã bật Gemini API trong Google AI Studio!")

    st.markdown("---")
    
    # KHU VỰC PHÒNG THÍ NGHIỆM ẢO
    st.markdown(
        """
        <div style="border: 2px solid #1E88E5; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
            <h2 style="margin: 0; color: #ffffff;">🔬 PHÒNG THÍ NGHIỆM ẢO</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    lab_input = st.text_input(
        "Ví dụ: Khảo sát hàm số bậc 3...",
        placeholder="Ví dụ: Khảo sát hàm số bậc 3, Thí nghiệm đo gia tốc trọng trường...",
        label_visibility="collapsed"
    )
    
    st.button("⚙️ Khởi chạy Phòng Lab", type="primary")

with tab2:
    st.subheader("Trạm 2: Gia Sư Socratic")
    st.write(f"Gia sư AI gợi mở câu hỏi môn **{subject} ({grade})**...")

with tab3:
    st.subheader("Trạm 3: Khảo Thí Tự Do")
    st.write(f"Khu vực ôn luyện và làm bài kiểm tra môn **{subject} ({grade})**...")

with tab4:
    st.subheader("Trạm 4: Nhật Ký Khoa Học Kỹ Thuật")
    st.write("Ghi chép tiến độ dự án KHKT...")

with tab5:
    st.warning("🔒 Trạm Thống Kê & Paired T-Test bị khóa. Vui lòng đăng nhập ở Trạm 4 trước.")

import streamlit as st
import google.generativeai as genai

# 1. Cấu hình trang
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)

# 2. Thanh bên (Sidebar)
with st.sidebar:
    st.header("THIẾT LẬP HỌC TẬP")
    
    # Mã QR
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
    
    btn_soan_bai = st.button("🧪 Tổng hợp kiến thức trọng tâm", type="primary")
    
    if btn_soan_bai:
        if not lesson_input.strip():
            st.warning("⚠️ Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
        elif not api_key_to_use:
            st.error("🔑 Chưa phát hiện API Key! Vui lòng nhập API Key ở thanh bên (Sidebar) để kích hoạt AI.")
        else:
            with st.spinner(f"⏳ AI đang tổng hợp kiến thức cốt lõi cho bài: **{lesson_input}**..."):
                genai.configure(api_key=api_key_to_use)
                
                # Danh sách model lấy động
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
                        "gemini-1.5-flash",
                        "models/gemini-2.5-flash",
                        "models/gemini-2.0-flash",
                        "models/gemini-1.5-flash"
                    ]
                
                # Prompt hoàn toàn bằng Tiếng Việt, định dạng Kiến thức cốt lõi & Không cho đáp án
                system_prompt = f"""
                Bạn là một trợ lý học tập AI chuyên tóm tắt kiến thức cốt lõi dành cho học sinh THPT.
                Hãy tổng hợp nội dung bài học theo đúng bộ sách SGK 'Kết nối tri thức với cuộc sống'.
                
                QUY TẮC BẮT BUỘC:
                1. TUYỆT ĐỐI KHÔNG DÙNG TIẾNG ANH. Toàn bộ thuật ngữ, tiêu đề, nội dung phải trình bày 100% bằng Tiếng Việt chuẩn.
                2. NỘI DUNG LÀ KIẾN THỨC CỐT LÕI (Dạng ghi nhớ/Sổ tay học tập), KHÔNG soạn thành dạng giáo án giảng dạy hay mục tiêu bài học.
                3. PHẦN VÍ DỤ VÀ BÀI TẬP:
                   - Trình bày rõ ràng, mỗi ý/bước phải XUỐNG DÒNG minh bạch.
                   - Có phần gợi ý định hướng các bước làm.
                   - CỰC KỲ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG CHO ĐÁP ÁN/ĐÁP SỐ CỦA BÀI TẬP. Để trống kết quả cuối cùng dưới dạng '...' hoặc đặt câu hỏi gợi mở để học sinh tự tính toán/suy luận.

                THÔNG TIN BÀI HỌC:
                - Môn học: {subject}
                - Khối lớp: {grade}
                - Tên bài học: {lesson_input}

                CẤU TRÚC TRÌNH BÀY (Dùng Markdown đẹp mắt):

                📌 **1. TÓM TẮT KIẾN THỨC CỐT LÕI**
                - Công thức, định lý, khái niệm quan trọng nhất (Dùng LaTeX cho công thức toán/lý/hóa).
                - Các tính chất/quy tắc cần ghi nhớ.

                ⚠️ **2. CÁC ĐIỂM DỄ BỊ LẪN LỘN / SAI LẦM CẦN TRÁNH**
                - 2-3 lưu ý ngắn gọn giúp học sinh không bị mất điểm khi làm bài.

                ✍️ **3. VÍ DỤ MINH HỌA & THỬ THÁCH TƯƠNG TÁC**
                - Cho 2 ví dụ tiêu biểu.
                - Mỗi ví dụ cần xuống dòng rõ ràng các phần:
                  + **Đề bài:** ...
                  + **Gợi ý từng bước:**
                    * Bước 1: ...
                    * Bước 2: ...
                  + **Thử thách học sinh:** (Đặt câu hỏi yêu cầu học sinh tự tính ra kết quả cuối cùng - KHÔNG đưa ra đáp số).
                """
                
                response_text = None
                used_model_name = ""
                last_error = ""
                
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
                    st.success(f"✅ Đã tổng hợp xong kiến thức: **{lesson_input}** ({subject} - {grade})")
                    st.markdown("---")
                    st.markdown(response_text)
                else:
                    st.error(f"❌ Không thể kết nối AI. Lỗi từ Google API: `{last_error}`")
                    st.info("💡 **Mẹo:** Kiểm tra lại mã API Key ở thanh bên (Sidebar) nhé!")

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

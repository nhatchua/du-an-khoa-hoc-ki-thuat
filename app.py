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
    st.header("⚙️ THIẾT LẬP HỌC TẬP")
    
    # Mã QR
    with st.expander("📲 Quét mã QR vào ứng dụng bằng điện thoại"):
        st.write("Dùng máy ảnh điện thoại để quét mã bên dưới để truy cập nhanh:")
        app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        st.image(qr_api_url, caption="Quét mã để mở trên điện thoại", width=200)
        st.markdown(f"🔗 **Hoặc nhấn vào đường dẫn:** [{app_url}]({app_url})")
    
    st.markdown("---")
    
    # THÔNG TIN HỌC SINH
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Không bắt buộc):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    
    # ĐƯỜNG TRUYỀN AI CÁ NHÂN
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

# 4. Hệ thống Trạm
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
            with st.spinner(f"⏳ AI đang phân tích dữ liệu chuẩn Sách Giáo Khoa 'Kết Nối Tri Thức Với Cuộc Sống' cho bài: **{lesson_input}**..."):
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
                
                # Cấu hình giảm ảo giác (temperature = 0.2)
                generation_config = genai.types.GenerationConfig(
                    temperature=0.2,
                    top_p=0.95
                )

                system_prompt = f"""
                Bạn là một Trợ Lý Giáo Dục AI chuyên viết Sổ Tay Kiến Thức Cốt Lõi cho học sinh phổ thông tại Việt Nam.
                Nhiệm vụ: Tổng hợp kiến thức bài học chuẩn theo Chương trình Giáo dục phổ thông 2018 - Bộ sách 'Kết nối tri thức với cuộc sống'.

                THÔNG TIN BÀI HỌC DỰ KIẾN:
                - Môn học chọn: {subject}
                - Khối lớp chọn: {grade}
                - Bài học yêu cầu: {lesson_input}

                QUY TẮC BẮT BUỘC (VI PHẠM SẼ BỊ LỖI):
                1. TUYỆT ĐỐI 100% KHÔNG DÙNG TIẾNG ANH. Không ghi câu suy luận tiếng Anh, không ghi ghi chú tiếng Anh. Toàn bộ câu chữ từ đầu đến cuối PHẢI là Tiếng Việt chuẩn.
                2. KHÔNG SOẠN THEO DẠNG GIÁO ÁN GIẢNG DẠY (không ghi Mục tiêu, Năng lực, Phẩm chất...). Trình bày theo dạng "Sổ tay ghi nhớ - Kiến thức trọng tâm".
                3. TIÊU ĐỀ MỤC LỚN PHẢI VIẾT HOA VÀ CÓ CỠ CHỮ LỚN (Định dạng # hoặc ## trong Markdown).
                4. CHỐNG ẢO GIÁC & CHUẨN SGK: Nếu bài học thuộc khối lớp khác trong bộ SGK 'Kết nối tri thức với cuộc sống' (ví dụ bài thuộc Lớp 10 nhưng người dùng chọn Lớp 11), hãy âm thầm căn chỉnh kiến thức chuẩn theo SGK Kết nối tri thức mà KHÔNG được ghi lời giải thích hay tranh luận bằng tiếng Anh.
                5. QUY TẮC BÀI TẬP VÀ VÍ DỤ:
                   - BẮT BUỘC bao gồm cả 2 dạng: **1. Dạng Trắc Nghiệm** và **2. Dạng Tự Luận Trả Lời Ngắn**.
                   - Xuống dòng rõ ràng cho từng lựa chọn, từng bước hướng dẫn.
                   - PHẦN HƯỚNG DẪN GIẢI: Nằm hoàn toàn trong thẻ `<details><summary>🔍 Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</summary>...</details>`.
                   - BẮT BUỘC: TUYỆT ĐỐI KHÔNG RA ĐÁP SỐ / ĐÁP ÁN CUỐI CÙNG. Đặt dấu '...?' hoặc câu hỏi gợi mở để học sinh tự tính toán.

                CẤU TRÚC TRÌNH BÀY HOÀN CHỈNH (Trình bày đúng định dạng bên dưới):

                # 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
                - Định nghĩa, khái niệm cốt lõi.
                - Công thức trọng tâm (Dùng định dạng LaTeX rõ ràng).
                - Các tính chất/quy tắc bắt buộc thuộc lòng.

                # ⚠️ II. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
                - 2-3 điểm học sinh rất hay nhầm lẫn hoặc khoanh sai đáp án.

                # ✍️ III. BÀI TẬP TƯƠNG TÁC & THỬ THÁCH

                ## 1. Dạng Trắc Nghiệm Tương Tác
                **Câu hỏi:** (Ghi đề bài trắc nghiệm)  
                A. ...  
                B. ...  
                C. ...  
                D. ...  

                <details>
                <summary>🔍 <b>Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

                * **Bước 1:** ...  
                * **Bước 2:** ...  
                * **Gợi ý:** Sử dụng công thức trên để loại trừ các đáp án sai. (KHÔNG ĐƯỢC CHỈ RA ĐÁP ÁN ĐÚNG LÀ A, B, C HOẶC D).
                </details>

                <br>

                ## 2. Dạng Tự Luận Trả Lời Ngắn
                **Câu hỏi:** (Ghi đề bài tự luận)  

                <details>
                <summary>🔍 <b>Nhấp vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

                * **Gợi ý bước 1:** ...  
                * **Gợi ý bước 2:** ...  
                * **Thử thách học sinh:** Em hãy thay số vào công thức và tính ra đáp số cuối cùng = ...?
                </details>
                """
                
                response_text = None
                used_model_name = ""
                last_error = ""
                
                for model_name in available_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(
                            system_prompt,
                            generation_config=generation_config
                        )
                        if response and response.text:
                            response_text = response.text
                            used_model_name = model_name
                            break
                    except Exception as err:
                        last_error = str(err)
                        continue
                
                if response_text:
                    st.success(f"✅ Đã hoàn thành tổng hợp kiến thức bài: **{lesson_input}** ({subject} - {grade})")
                    st.markdown("---")
                    st.markdown(response_text, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Không thể kết nối AI. Chi tiết lỗi từ hệ thống: `{last_error}`")
                    st.info("💡 **Mẹo:** Nhật kiểm tra lại Mã Kết Nối (API Key) ở thanh bên trái nhé!")

    st.markdown("---")
    
    # KHU VỰC PHÒNG THÍ NGHIỆM ẢO
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

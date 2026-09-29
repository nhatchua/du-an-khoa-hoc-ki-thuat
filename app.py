import streamlit as st

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
        
        # Link web ứng dụng
        app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
        
        # Tạo mã QR tự động từ link web
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        
        # Hiển thị ảnh mã QR
        st.image(qr_api_url, caption="Quét mã để mở trên điện thoại", width=200)
        
        # Hiển thị link bấm trực tiếp
        st.markdown(f"🔗 **Hoặc bấm vào link:** [{app_url}]({app_url})")
    
    st.markdown("---")
    
    # THÔNG TIN HỌC SINH
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Tùy chọn):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    
    # ĐƯỜNG TRUYỀN AI CÁ NHÂN
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    
    # Nút bấm mở thẳng trang lấy API Key trên Google AI Studio
    st.link_button(
        "👉 Lấy Key riêng miễn phí (15s)", 
        "https://aistudio.google.com/app/apikey", 
        use_container_width=True
    )
    
    # Ô nhập API Key
    user_api_key = st.text_input(
        "Dán mã API Key của em vào đây:", 
        type="password", 
        placeholder="AIzaSy..."
    )
    
    # Thông báo trạng thái đường truyền
    if user_api_key:
        st.success("🟢 Đang dùng đường truyền AI Cá nhân")
    else:
        st.info("🔵 Đang dùng đường truyền chung của Trường")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CHỌN KHỐI LỚP & MÔN HỌC
    st.markdown("🎯 **Chọn khối lớp:**")
    grade = st.selectbox(
        "Chọn khối lớp",
        ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
        index=6, # Mặc định chọn Lớp 12
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
    
    # BÁO LỖI & GÓP Ý (ĐÃ THÊM ĐÁNH GIÁ SAO VÀ MÔ TẢ CHI TIẾT)
    with st.expander("🛠️ Báo lỗi ứng dụng & Góp ý"):
        st.markdown("**Loại vấn đề gặp phải:**")
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
        
        # Thanh đánh giá sao (Star rating)
        rating = st.feedback("stars")
        
        st.markdown("**Mô tả chi tiết:**")
        feedback_text = st.text_area(
            "Mô tả chi tiết:",
            placeholder="Mô tả cụ thể vấn đề hoặc ý kiến đóng góp...",
            label_visibility="collapsed"
        )
        
        if st.button("📩 Gửi phản hồi đến Thầy", use_container_width=True):
            if feedback_text or issue_type:
                st.success("Cảm ơn em! Phản hồi đã được gửi đến Thầy.")
            else:
                st.warning("Vui lòng nhập thông tin trước khi gửi!")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # TRIẾT LÝ
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")


# 3. Khu vực chính (Main Content)
st.markdown("<h1 style='text-align: center;'>🤖 GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>Trường THPT Tân Hiệp & Trung tâm Thiện Nhân • Đồng hành từ Lớp 6 đến Lớp 12</p>", unsafe_allow_html=True)

# Badge thông tin
col_b1, col_b2, col_b3, col_b4 = st.columns([1, 2, 2, 1])
with col_b2:
    st.info("📚 Bộ sách: Kết Nối Tri Thức Với Cuộc Sống")
with col_b3:
    st.success("🎯 Chuẩn CT GDPT 2018 / Format 2025")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Hệ thống Trạm (Tabs chuyển hướng)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💡 Trạm 1: Học Tập & Phòng Lab",
    "✍️ Trạm 2: Gia Sư Socratic",
    "🏆 Trạm 3: Khảo Thí Tự Do",
    "📊 Trạm 4: Nhật Ký KHKT",
    "📉 Trạm 5: Thống Kê & T-Test"
])

with tab1:
    st.subheader("Trạm 1: Học Tập & Phòng Lab")
    st.write("Nội dung học tập và phòng lab thực hành...")

with tab2:
    st.subheader("Trạm 2: Gia Sư Socratic")
    st.write("Gia sư AI gợi mở câu hỏi theo phương pháp Socratic...")

with tab3:
    st.subheader("Trạm 3: Khảo Thí Tự Do")
    st.write("Khu vực ôn luyện và làm bài kiểm tra...")

with tab4:
    st.subheader("Trạm 4: Nhật Ký Khoa Học Kỹ Thuật")
    st.write("Ghi chép tiến độ dự án KHKT...")

with tab5:
    st.warning("🔒 Trạm Thống Kê & Paired T-Test bị khóa. Vui lòng đăng nhập ở Trạm 4 trước.")

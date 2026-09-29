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
    
    # Hộp quét mã QR
    with st.expander("📲 Quét mã QR vào app trên điện thoại"):
        st.write("Dùng camera điện thoại để quét mã bên dưới:")
        # st.image("link_anh_qr.png") # Bỏ comment nếu có ảnh QR
    
    st.markdown("---")
    
    # THÔNG TIN HỌC SINH
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Tùy chọn):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    
    # ĐƯỜNG TRUYỀN AI CÁ NHÂN
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    st.button("👉 Lấy Key riêng miễn phí (15s)", use_container_width=True)


# 3. Khu vực chính (Main Content)
# Tiêu đề chính
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

# Nội dung từng Trạm
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

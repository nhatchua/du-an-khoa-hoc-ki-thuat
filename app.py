# 2. Thanh bên (Sidebar) - THIẾT LẬP HỌC TẬP
with st.sidebar:
    st.header("THIẾT LẬP HỌC TẬP")
    
    # Hộp quét mã QR
    with st.expander("📲 Quét mã QR vào app trên điện thoại"):
        st.write("Dùng camera điện thoại để quét mã QR.")
    
    st.markdown("---")
    
    # THÔNG TIN HỌC SINH
    st.subheader("👨‍🎓 THÔNG TIN HỌC SINH")
    name = st.text_input("Họ và tên em (Tùy chọn):", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    
    # ĐƯỜNG TRUYỀN AI CÁ NHÂN
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    
    # Nút lấy key
    st.button("👉 Lấy Key riêng miễn phí (15s)", use_container_width=True)
    
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
    
    # BÁO LỖI & GÓP Ý
    with st.expander("🛠️ Báo lỗi ứng dụng & Góp ý"):
        st.text_area("Mô tả lỗi hoặc góp ý của em:")
        st.button("Gửi phản hồi")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # TRIẾT LÝ
    st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")

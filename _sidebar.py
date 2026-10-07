# ==============================================================================
# _sidebar.py — Sidebar: logo, QR, API key, thông tin HS, feedback
# ==============================================================================
import streamlit as st
import requests
import base64
from _config import APP_URL, get_vn_time


def _get_local_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        return ""


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_global_logs_cached(webhook_url: str):
    """Fetch global logs từ Google Sheets — cache 5 phút."""
    try:
        res = requests.get(webhook_url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return None


def render_sidebar():
    """
    Render toàn bộ sidebar.
    Trả về (grade, subject).
    """
    with st.sidebar:
        # ========== LOGO + TIÊU ĐỀ ==========
        logo_b64 = _get_local_img_as_base64("LOGO THIỆN NHÂN 3D.jpg")
        logo_html = (
            f'<img src="data:image/jpeg;base64,{logo_b64}" class="thiennhan-logo" alt="Logo">'
            if logo_b64
            else (
                '<div style="background: linear-gradient(45deg, #0f172a, #1e293b); '
                'padding: 8px 12px; border-radius: 8px; color: #f8fafc; '
                'font-weight: 800; font-size: 14px; border: 1.5px solid #38bdf8; '
                'box-shadow: 0 0 10px rgba(56,189,248,0.4);">THIỆN NHÂN</div>'
            )
        )

        school_icon_svg = (
            "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
            "viewBox='0 0 24 24' fill='%2338bdf8'><path d='M12 3L1 9l4 2.18v6L12 21"
            "l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9z"
            "M17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z'/></svg>"
        )

        st.markdown(
            f'<div class="brand-container">'
            f'<img src="{school_icon_svg}" class="school-icon" alt="Icon Trường">'
            f'{logo_html}</div>'
            '<div style="text-align: center; margin-bottom: 15px;">'
            '<h2 style="color: #38bdf8; font-weight: 800; font-size: 1.8rem; '
            'margin: 0; text-shadow: 0px 2px 4px rgba(0,0,0,0.5);">THIẾT LẬP HỌC TẬP</h2>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ========== QR CODE ==========
        with st.expander("📱 Quét mã QR vào app trên điện thoại", expanded=False):
            qr_api_url = (
                f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={APP_URL}"
            )
            st.image(qr_api_url, caption="Bật camera Zalo/iPhone quét mượt mà!",
                     use_container_width=True)
            st.markdown(f'<div class="short-link-badge">🔗 {APP_URL}</div>',
                        unsafe_allow_html=True)

        # ========== API KEY ==========
        st.markdown("---")
        st.markdown("### 🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN (0 ĐỒNG)")

        st.link_button(
            "👉 Lấy Key riêng miễn phí (15s)",
            "https://aistudio.google.com/apikey",
            use_container_width=True,
        )
        user_custom_key = st.text_input(
            "Dán mã API Key của em vào đây:",
            type="password",
            placeholder="AIzaSy...",
        )

        # ========== SECRETS ==========
        raw_sheet_url = st.secrets.get("GOOGLE_SHEET_URL", "")
        sheet_webhook_url = "".join(raw_sheet_url.split()) if raw_sheet_url else ""

        sheet_view_url_secret = st.secrets.get("GOOGLE_SHEET_VIEW_URL", "")
        sheet_view_url = (
            "".join(sheet_view_url_secret.split())
            if sheet_view_url_secret else sheet_webhook_url
        )

        # ===== Fetch global logs (CACHED 5 PHÚT) =====
        if not st.session_state.global_stats_loaded and sheet_webhook_url:
            data_gs = _fetch_global_logs_cached(sheet_webhook_url)
            if data_gs:
                st.session_state.global_logs = data_gs
                st.session_state.global_exam_count = len(
                    [x for x in data_gs if x.get("type") == "EXAM_RESULT"]
                )
            st.session_state.global_stats_loaded = True

        # ========== FIX CỨNG: CHỈ DÙNG API KEY CÁ NHÂN ==========
        active_keys_pool = (
            [user_custom_key.strip()] if user_custom_key.strip() else []
        )

        if not active_keys_pool:
            st.error(
                "### ⚠️ BẮT BUỘC NHẬP MÃ KẾT NỐI AI CÁ NHÂN\n\n"
                "Để đảm bảo công bằng và tránh quá tải đường truyền chung của Trường, "
                "hệ thống yêu cầu **mỗi học sinh tự lấy API Key riêng** "
                "(hoàn toàn miễn phí, chỉ mất 15 giây).\n\n"
                "**Hướng dẫn 3 bước:**\n"
                "1. 👉 Bấm nút **'Lấy Key riêng miễn phí (15s)'** ở thanh bên trái\n"
                "2. 🔑 Đăng nhập Google → Bấm **'Create API key'** → Copy mã `AIzaSy...`\n"
                "3. 📋 Dán mã vào ô **'Dán mã API Key của em vào đây'** ở thanh bên trái\n\n"
                "*💡 Mã này là của riêng em, miễn phí vĩnh viễn, không chia sẻ cho ai.*\n\n"
                "**Sau khi dán mã xong, app sẽ tự động chạy lại và cho em sử dụng bình thường.**"
            )
            st.stop()

        st.sidebar.success("🟢 Em đang dùng đường truyền AI Cá nhân!")

        # Lưu vào session_state để module khác đọc
        st.session_state.active_keys_pool = active_keys_pool
        st.session_state.sheet_webhook_url = sheet_webhook_url
        st.session_state.sheet_view_url = sheet_view_url

        # ========== THÔNG TIN HỌC SINH ==========
        st.markdown("---")
        st.markdown("### 👤 THÔNG TIN HỌC SINH")
        student_name_input = st.text_input(
            "Họ và tên của em:",
            placeholder="Ví dụ: Nguyễn Văn A...",
        )
        student_name = (
            student_name_input.strip() if student_name_input.strip() else "Ẩn danh"
        )
        st.session_state.student_name = student_name

        all_grades = [f"Lớp {i}" for i in range(6, 13)]
        grade = st.selectbox("🎯 Chọn khối lớp:", all_grades, index=6)
        grade_num = int(grade.split()[1])

        available_subjects = (
            ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh",
             "Lịch sử & Địa lý", "Tin học", "Giáo dục công dân"]
            if grade_num <= 9
            else ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Ngữ văn",
                  "Tiếng Anh", "Lịch sử", "Địa lý", "Tin học",
                  "Giáo dục kinh tế và pháp luật"]
        )
        subject = st.selectbox("📚 Môn học cần hỗ trợ:", available_subjects)

        # ========== FEEDBACK FORM ==========
        st.markdown("---")
        with st.expander("🛠️ Báo lỗi ứng dụng & Góp ý trải nghiệm", expanded=False):
            fb_category = st.selectbox(
                "Loại vấn đề gặp phải:",
                ["📷 Lỗi nhận diện chữ", "📊 Lỗi đồ thị Lab",
                 "🤖 AI giải thích khó hiểu", "⏳ Ứng dụng chậm", "💡 Đề xuất mới"],
            )
            fb_rating = st.feedback("stars", key="fb_stars")
            fb_detail = st.text_area("Mô tả chi tiết:", key="fb_text")

            if st.button("📤 Gửi phản hồi", use_container_width=True) and fb_detail.strip():
                fb_entry = {
                    "time": get_vn_time(),
                    "name": student_name,
                    "grade": grade,
                    "subject": subject,
                    "category": fb_category,
                    "rating": fb_rating + 1 if fb_rating is not None else 5,
                    "detail": fb_detail.strip(),
                    "type": "USER_FEEDBACK",
                }
                st.session_state.feedback_logs.append(fb_entry)
                if sheet_webhook_url:
                    try:
                        requests.post(sheet_webhook_url, json=fb_entry, timeout=5)
                    except Exception:
                        pass
                st.success("Đã gửi phản hồi thành công!")

        # ========== THỐNG KÊ NHANH ==========
        st.markdown("---")
        st.markdown("### 📈 THỐNG KÊ THỰC NGHIỆM (KHKT)")
        col_sb1, col_sb2, col_sb3 = st.columns(3)
        with col_sb1:
            st.metric("Tự học (T1)", f"{st.session_state.tram1_count}")
        with col_sb2:
            st.metric("Socratic (T2)", f"{st.session_state.tram2_count}")
        with col_sb3:
            current_exam_count = len(
                [x for x in st.session_state.get("analytics_logs", [])
                 if x.get("type") == "EXAM_RESULT"]
            )
            total_display_count = max(
                current_exam_count,
                st.session_state.get("global_exam_count", 0),
            )
            st.metric("Khảo thí (T3)", f"{total_display_count}")

        with st.expander("📚 SGK Điện Tử (Kết Nối Tri Thức)", expanded=False):
            sgk_url = "https://www.vniteach.com/sach-dien-tu-ket-noi-tri-thuc/"
            st.image(
                f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={sgk_url}",
                use_container_width=True,
            )
            st.link_button("🌐 Mở sách điện tử ngay", sgk_url, use_container_width=True)

        st.info("💡 **Triết lý:** Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")

    return grade, subject

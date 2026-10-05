# ==============================================================================
# app.py — ENTRY POINT
# Hệ Sinh Thái Lớp Học Đảo Ngược — Trường THPT Tân Hiệp & Thiện Nhân
# ==============================================================================
import streamlit as st

# ============ IMPORTS MODULE ============
from _config import init_session_state
from _styles import apply_styles
from _sidebar import render_sidebar
from _tab1 import render_tab_study
from _socratic import render_tab_socratic
from _exam import render_tab_exam
from _analytics import render_tab_analytics


# ==============================================================================
# CẤU HÌNH TRANG
# ==============================================================================
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# KHỞI TẠO
# ==============================================================================
init_session_state()
apply_styles()


# ==============================================================================
# HEADER
# ==============================================================================
st.markdown(
    '<div class="main-header">'
    '<div class="main-title">🏫 GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</div>'
    '<div class="sub-title">Trường THPT Tân Hiệp & Trung tâm Thiện Nhân • '
    'Đồng hành từ Lớp 6 đến Lớp 12</div>'
    '<div style="margin-top: 8px;">'
    '<span class="badge-tag">Bộ sách: Kết Nối Tri Thức Với Cuộc Sống</span>'
    '<span class="badge-tag" style="border-color: #34d399; color: #34d399; margin-left: 8px;">'
    'Chuẩn CT GDPT 2018 & Quy chế 2026</span></div></div>',
    unsafe_allow_html=True
)


# ==============================================================================
# SIDEBAR (trả về grade, subject)
# ==============================================================================
grade, subject = render_sidebar()


# ==============================================================================
# TABS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "💡 Trạm 1: Học Tập & Phòng Lab",
    "✍️ Trạm 2: Gia Sư Socratic & Nộp Bài",
    "📝 Trạm 3: Khảo Thí Độc Lập",
    "📊 Trạm 4: Dữ Liệu KHKT & Tự Động Vá Lỗi"
])


with tab1:
    render_tab_study(grade, subject)

with tab2:
    render_tab_socratic(grade, subject)

with tab3:
    render_tab_exam(grade, subject)

with tab4:
    render_tab_analytics(grade, subject)

# ==============================================================================
# _config.py — Hằng số + Khởi tạo session_state
# ==============================================================================
import streamlit as st
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))


def get_vn_time():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")


APP_URL = "https://giasuaithiennhanedu-r5bwggdappdvrmtne2wv3dw.streamlit.app"


# ==============================================================================
# DANH SÁCH MODEL GEMINI THẬT (2024-2025) — FALLBACK KHI KHÔNG QUÉT ĐƯỢC API
#
# ⚠️ LƯU Ý QUAN TRỌNG:
# Đây CHỈ là danh sách FALLBACK khi app không quét được API.
# App sẽ ưu tiên QUÉT API (client.models.list()) để biết CHÍNH XÁC
# model nào khả dụng cho TỪNG API KEY cụ thể của mỗi học sinh.
#
# → Mỗi học sinh có thể có model khác nhau, tùy vào key của họ.
# ==============================================================================
FALLBACK_MODELS = [
    "gemini-2.0-flash-exp",      # Experimental, nhanh, ổn định
    "gemini-1.5-flash",          # Ổn định, phổ biến
    "gemini-1.5-flash-8b",       # Nhẹ, nhanh
    "gemini-1.5-pro",            # Mạnh hơn, chậm hơn
]

# Alias cũ — giữ để tương thích ngược
ALL_GEMINI_MODELS = FALLBACK_MODELS


def get_model_priority(name: str) -> int:
    """
    Xếp hạng ưu tiên model — SỐ NHỎ = ƯU TIÊN CAO.
    CHỈ xếp hạng các model THẬT đang tồn tại (2.0, 1.5, alias latest).
    Tuyệt đối KHÔNG xếp hạng các model ảo (2.5, 3.x).
    """
    n = (name or "").lower()

    # ===== Dòng 2.x — Mới nhất =====
    if "2.0-flash-exp" in n:               return 1
    if "2.0-flash-lite" in n:              return 2
    if "2.0-flash" in n:                   return 3
    if "2.0-pro" in n:                     return 4
    if "2.0" in n:                         return 5

    # ===== Alias "latest" — Luôn trỏ tới bản mới nhất =====
    if "flash-latest" in n:                return 6
    if "pro-latest" in n:                  return 7

    # ===== Dòng 1.5 — Ổn định =====
    if "1.5-flash" in n and "8b" not in n: return 10
    if "1.5-flash-8b" in n:                return 11
    if "1.5-pro" in n:                     return 12
    if "1.5" in n:                         return 13

    # ===== Experimental khác =====
    if "exp" in n:                         return 20

    # ===== Không xác định =====
    return 99


TEXT_ONLY_SUBJECTS = {
    "Hóa học", "Sinh học", "Lịch sử", "Địa lý",
    "Lịch sử & Địa lý", "Giáo dục công dân",
    "Giáo dục kinh tế và pháp luật",
}


def init_session_state():
    """Khởi tạo toàn bộ session_state một lần. Gọi ở đầu app.py."""

    # ===== Lists =====
    for key in ["messages", "analytics_logs", "feedback_logs",
                "parsed_quiz", "va_loi_logs"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # ===== Counters =====
    if "tram1_count" not in st.session_state:
        st.session_state.tram1_count = 0
    if "tram2_count" not in st.session_state:
        st.session_state.tram2_count = 0

    # ===== Trạm 1 — Học tập & Lab =====
    if "chat" not in st.session_state:
        st.session_state.chat = None
    if "current_lesson" not in st.session_state:
        st.session_state.current_lesson = ""
    if "lab_data" not in st.session_state:
        st.session_state.lab_data = None
    if "lab_text_result" not in st.session_state:
        st.session_state.lab_text_result = None
    if "quiz_states" not in st.session_state:
        st.session_state.quiz_states = {}
    if "last_subject_seen" not in st.session_state:
        st.session_state.last_subject_seen = ""

    # ===== Trạm 2 — Socratic =====
    if "socratic_uploader_key" not in st.session_state:
        st.session_state.socratic_uploader_key = 0
    if "socratic_analyzed_keys" not in st.session_state:
        st.session_state.socratic_analyzed_keys = set()
    if "current_diagnostic" not in st.session_state:
        st.session_state.current_diagnostic = {}
    if "first_feedback" not in st.session_state:
        st.session_state.first_feedback = ""

    # ===== Trạm 3 — Khảo thí =====
    if "exam_state" not in st.session_state:
        st.session_state.exam_state = "config"
    if "exam_data" not in st.session_state:
        st.session_state.exam_data = None
    if "violation_count" not in st.session_state:
        st.session_state.violation_count = 0
    if "exam_answers" not in st.session_state:
        st.session_state.exam_answers = {}
    if "tram3_chat_messages" not in st.session_state:
        st.session_state.tram3_chat_messages = []

    # ===== Trạm 4 — KHKT =====
    if "tab4_authenticated" not in st.session_state:
        st.session_state.tab4_authenticated = False
    if "run_ttest" not in st.session_state:
        st.session_state.run_ttest = False

    # ===== Global =====
    if "working_model" not in st.session_state:
        st.session_state.working_model = None
    if "global_stats_loaded" not in st.session_state:
        st.session_state.global_stats_loaded = False
    if "global_exam_count" not in st.session_state:
        st.session_state.global_exam_count = 0
    if "global_logs" not in st.session_state:
        st.session_state.global_logs = []

    # ===== Biến do sidebar set =====
    if "active_keys_pool" not in st.session_state:
        st.session_state.active_keys_pool = []
    if "sheet_webhook_url" not in st.session_state:
        st.session_state.sheet_webhook_url = ""
    if "sheet_view_url" not in st.session_state:
        st.session_state.sheet_view_url = ""
    if "student_name" not in st.session_state:
        st.session_state.student_name = "Ẩn danh"

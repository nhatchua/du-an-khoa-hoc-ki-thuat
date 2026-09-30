import streamlit as st
import google.generativeai as genai
import re
import json

# 1. Cấu hình trang
st.set_page_config(
    page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
    page_icon="🤖",
    layout="wide"
)

# HÀM LỌC SẠCH SIÊU MẠNH: TỰ ĐỘNG CẮT VÀ XÓA SẠCH MỌI DÒNG NHÁP TIẾNG ANH
def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    
    # 1. Cắt bỏ toàn bộ phần rác nằm trước tiêu đề bài học
    start_keywords = ["# 📌 I. KIẾN THỨC CỐT LÕI", "I. KIẾN THỨC CỐT LÕI"]
    best_idx = -1
    for kw in start_keywords:
        idx = text.find(kw)
        if idx != -1:
            best_idx = idx
            break
    
    if best_idx != -1:
        text = text[best_idx:]
        
    # 2. Lọc bỏ các dòng nháp / suy luận nội tâm tiếng Anh rải rác bên trong nội dung
    lines = text.split('\n')
    filtered_lines = []
    
    english_draft_patterns = [
        "refining", "final polish", "wait,", "drafting", "check against", 
        "role:", "curriculum:", "topic:", "no internal", "let's go",
        "multiple choice:", "short answer:", "question:", "hint:"
    ]
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        is_draft = any(pattern in line_lower for pattern in english_draft_patterns)
        
        if not is_draft:
            filtered_lines.append(line)
            
    return '\n'.join(filtered_lines).strip()

def call_gemini_with_fallback(prompt, json_mode=False):
    api_key = st.session_state.get("api_key_to_use", "")
    if not api_key:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    genai.configure(api_key=api_key)
    
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash"
    ]
    
    config = genai.types.GenerationConfig(temperature=0.0)
    if json_mode:
        config = genai.types.GenerationConfig(temperature=0.0, response_mime_type="application/json")
        
    last_err = None
    for m_name in models:
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt, generation_config=config)
            if res and res.text:
                return res.text
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"Không thể gọi AI. Lỗi: {last_err}")

def parse_quiz_questions(text):
    questions = []
    # Logic giả lập tách câu hỏi đơn giản hoặc bóc tách từ text trả về
    return questions

def render_dynamic_python_lab(code):
    try:
        exec(code, globals())
    except Exception as e:
        st.error(f"Lỗi hiển thị Phòng Lab: {e}")

def render_smart_lab(data):
    st.write(data)

# Khởi tạo session state
if "quiz_states" not in st.session_state:
    st.session_state.quiz_states = {}
if "current_lesson" not in st.session_state:
    st.session_state.current_lesson = ""
if "parsed_quiz" not in st.session_state:
    st.session_state.parsed_quiz = []
if "lab_data" not in st.session_state:
    st.session_state.lab_data = None

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
    name = st.text_input("Họ và tên:", placeholder="Ví dụ: Nguyễn Văn A")
    
    st.markdown("---")
    st.subheader("🔑 ĐƯỜNG TRUYỀN AI CÁ NHÂN")
    
    st.link_button(
        "👉 Lấy Mã Riêng Miễn Phí (15 giây)", 
        "https://aistudio.google.com/app/apikey", 
        use_container_width=True
    )
    
    user_api_key = st.text_input(
        "Dán Mã Kết Nối (API Key):", 
        type="password", 
        placeholder="Nhập mã bí mật tại đây..."
    )
    
    if user_api_key:
        st.success("🟢 Đang sử dụng đường truyền AI Cá nhân")
        st.session_state.api_key_to_use = user_api_key
    else:
        st.info("🔵 Đang sử dụng đường truyền chung của Trường")
        st.session_state.api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("🎯 **Chọn khối lớp:**")
    grade = st.selectbox(
        "Chọn khối lớp",
        ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
        index=5,
        label_visibility="collapsed"
    )
    grade_num = grade.replace("Lớp ", "")
    
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
        if st.button("📩 Gửi phản hồi", use_container_width=True):
            if feedback_text or issue_type:
                st.success("Đã gửi phản hồi thành công.")
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

# ------------------------------------------------------------------------------
# TRẠM 1: LÝ THUYẾT & PHÒNG LAB
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📖 Tự học & Chiếm lĩnh kiến thức môn {subject} - Lớp {grade_num}")
    
    topic_input = st.text_input("📝 Nhập bài học cần chiếm lĩnh kiến thức:", placeholder="Ví dụ: Khảo sát hàm số, Hình chóp...")
    
    if st.button("🚀 Soạn bài học chuẩn GDPT 2018") and topic_input.strip():
        with st.spinner("Đang biên soạn chuẩn ngữ liệu SGK KNTT và cấu trúc Socratic..."):
            study_prompt = f"""
            Môn học: {subject} LỚP {grade_num}, Bộ sách Kết Nối Tri Thức. Chủ đề: '{topic_input}'.
            NẾU yêu cầu sai môn học, CHỈ IN RA: "Hình như em đang chọn nhầm môn học rồi kìa! 😊" VÀ DỪNG LẠI.
            NẾU ĐÚNG MÔN: TUYỆT ĐỐI CẤM nhắc "Hàm bậc 4 trùng phương". CẤM Lực căng dây T âm.
            KIỂM TRA CHÉO NỘI BỘ TRƯỚC KHI XUẤT: Đảm bảo Bảng biến thiên (nghiệm y'=0, dấu đạo hàm, chiều mũi tên) và Cực trị chính xác 100% về mặt toán học/vật lý. Tự giải nháp 2 lần.
            YÊU CẦU:
            ### PHẦN 1: TÓM TẮT CỐT LÕI (Dùng Bảng Markdown)
            ### PHẦN 2: TRẮC NGHIỆM KHÁCH QUAN SOCRATIC (3 câu, 4 đáp án A, B, C, D rõ ràng. KHÔNG dùng "hình bên". Cuối mỗi câu ghi "CORRECT: [A/B/C/D]" và "EXPLAIN: [Gợi ý tư duy]")
            ### PHẦN 3: BÀI TẬP TỰ LUẬN & HƯỚNG DẪN TƯ DUY
            (TỬ HUYỆT SƯ PHẠM: Ở PHẦN 3 NÀY, BẠN CHỈ ĐƯỢC CHO ĐỀ BÀI VÀ VẠCH RA CÁC BƯỚC GỢI Ý TƯ DUY. TUYỆT ĐỐI KHÔNG ĐƯỢC GIẢI CHI TIẾT HAY ĐƯA RA KẾT QUẢ CUỐI CÙNG! NẾU BẠN GIẢI SẴN RA ĐÁP ÁN LÀ BẠN ĐÃ PHÁ HOẠI TRIẾT LÝ SOCRATIC CỦA HỆ THỐNG!)
            """
            try:
                raw_res = call_gemini_with_fallback(study_prompt)
                res_text = clean_ai_response(raw_res)
                st.session_state.current_lesson = res_text
                st.session_state.parsed_quiz = parse_quiz_questions(res_text)
                st.session_state.quiz_states = {}
            except Exception as e:
                st.error(f"Lỗi: {e}")

    if st.session_state.get("current_lesson"):
        lesson_text = st.session_state.current_lesson
        part2_split = re.split(r'(?i)(?:###\s*)?PHẦN 2[\:\.]?', lesson_text)
        part3_split = re.split(r'(?i)(?:###\s*)?PHẦN 3[\:\.]?', lesson_text)
        
        if len(part2_split) > 0 and part2_split[0].strip():
            st.markdown(f'<div class="markdown-text-container">{re.sub(r"\\n{3,}", "\\n\\n", part2_split[0].strip())}</div>', unsafe_allow_html=True)

        quiz_list = st.session_state.get("parsed_quiz", [])
        if quiz_list:
            st.markdown("### 🎯 Phần 2: Trắc nghiệm khách quan Socratic")
            for idx, q in enumerate(quiz_list):
                st.info(f"**Câu {idx+1}:** `[{q['level']}]` {q['question']}")
                
                clean_opts_t1 = [str(opt).replace("\\infty", "∞").replace("\infty", "∞") for opt in q['options']]
                user_choice = st.radio(f"Chọn đáp án câu {idx+1}:", clean_opts_t1, key=f"q_{idx}", label_visibility="collapsed")
                if st.button(f"🔍 Kiểm tra câu {idx+1}", key=f"btn_{idx}"):
                    choice_letter = re.sub(r'[^A-D]', '', user_choice.strip()[:3]).upper()[:1]
                    if choice_letter == q['correct']: 
                        st.session_state.quiz_states[idx] = ("correct", "🎉 Xuất sắc!")
                    else: 
                        st.session_state.quiz_states[idx] = ("incorrect", f"💡 **Gợi ý:** {q['explain']}")
                
                if idx in st.session_state.quiz_states:
                    status, msg = st.session_state.quiz_states[idx]
                    if status == "correct": 
                        st.success(msg)
                    else: 
                        st.warning("🤔 Chưa chính xác!")
                        st.info(msg)
        
        if len(part3_split) > 1 and part3_split[-1].strip():
            st.markdown("### ✍️ Phần 3: Bài tập tự luận & Hướng dẫn tư duy")
            st.markdown(re.sub(r'\n{3,}', '\n\n', part3_split[-1].strip()).replace("\nBài", "\n\n<br>**Bài"), unsafe_allow_html=True)

    # ------------------ PHÒNG LAB ------------------
    st.markdown("---")
    with st.container():
        st.markdown("""<div style="background: linear-gradient(145deg, #0f172a, #1e293b); border: 2px solid #0ea5e9; padding: 20px; border-radius: 15px 15px 0 0; text-align: center;"><h3 style="color: white; margin: 0;">🔬 PHÒNG THÍ NGHIỆM ẢO</h3></div>""", unsafe_allow_html=True)
        lab_command = st.text_input("Lệnh mô phỏng:", placeholder="Ví dụ: Khảo sát hàm số bậc 3...", label_visibility="collapsed")
        
        if st.button("✨ Khởi chạy Phòng Lab") and lab_command.strip():
            with st.spinner("Phòng Lab đang dựng mô hình..."):
                lab_prompt = f"""Môn học: {subject}. Khối: {grade_num}. Ngữ cảnh: {st.session_state.get("current_lesson", "")}. Yêu cầu: "{lab_command}"
                CHỈ XUẤT 1 KHỐI JSON (KHÔNG BỌC TICK ```). 
                Dùng {{"type": "func_3", "a":.., "b":.., "c":.., "d":..}} cho hàm bậc 3. Dùng "func_1_1" hoặc "func_2_1" tương ứng. Dùng "dynamic_code" với `go.Figure()` cho vật lý. Dùng "mermaid" cho Sinh/Hóa.
                """
                try:
                    raw_json = call_gemini_with_fallback(lab_prompt, json_mode=True)
                    json_match = re.search(r'\{.*\}', raw_json.strip(), re.DOTALL)
                    if json_match: 
                        st.session_state.lab_data = json.loads(json_match.group(0))
                    else: 
                        st.session_state.lab_data = None
                except Exception as e: 
                    st.error(f"Lỗi: {e}")
        
        if st.session_state.get("lab_data"):
            st.success("✨ Khởi tạo thành công!")
            st.info(f"💡 {st.session_state.lab_data.get('explanation', '')}")
            if st.session_state.lab_data.get("type") == "dynamic_code": 
                render_dynamic_python_lab(st.session_state.lab_data.get("python_code", ""))
            else: 
                render_smart_lab(st.session_state.lab_data)

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

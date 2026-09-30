import streamlit as st
import google.generativeai as genai
import re
import time

# ============================================================
# 1. CẤU HÌNH GIAO DIỆN TRANG
# ============================================================
def setup_page_config():
    st.set_page_config(
        page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
        page_icon="📚",
        layout="wide"
    )
    # Tùy chỉnh CSS để làm nổi bật tiêu đề, hộp nội dung và hiệu ứng tương tác trắc nghiệm
    st.markdown("""
        <style>
        .main-title {
            color: #0d6efd;
            font-weight: 800;
            border-bottom: 3px solid #0d6efd;
            padding-bottom: 10px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .sub-section {
            background-color: #f8f9fa;
            border-left: 5px solid #0d6efd;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #212529;
        }
        .quiz-box {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. XỬ LÝ VÀ LỌC SẠCH PHẢN HỒI TỪ AI
# ============================================================
def clean_ai_response(text: str) -> str:
    """Lọc bỏ suy luận tiếng Anh, echo prompt, và rác đầu ra của AI."""
    if not text:
        return ""

    pattern = re.compile(
        r"(#{1,3}\s*)?📌?\s*1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI",
        re.IGNORECASE | re.UNICODE
    )
    match = pattern.search(text)
    if match:
        text = text[match.start():]

    text = re.sub(r'(#+ [^\n]*?)"\s*$', r'\1', text, flags=re.MULTILINE)

    lines = text.split('\n')
    filtered = []

    draft_patterns = re.compile(
        r"^\s*[\*\-\s]*("
        r"note\s*:|section\s+[ivx]+|theory|concepts|formulas|"
        r"common mistakes|interactive exercises|multiple choice\s*:|"
        r"short answer\s*:|refining|final polish|wait,|drafting|"
        r"check against|role\s*:|curriculum\s*:|topic\s*:|"
        r"no internal|let'?s go|thinking|reasoning|analysis\s*:|"
        r"step\s+\d+\s*:|here'?s|let me|i will|i'?ll"
        r")",
        re.IGNORECASE
    )

    english_paren = re.compile(r"\([A-Za-z][A-Za-z\s,;:\-]{4,}\)")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append(line)
            continue

        if draft_patterns.match(stripped):
            continue

        if english_paren.search(stripped) and len(stripped) < 200:
            cleaned = english_paren.sub("", stripped).rstrip(".,;: ")
            if cleaned:
                filtered.append(cleaned)
            continue

        if len(stripped) > 15:
            has_vietnamese = bool(re.search(
                r"[àáảãạăâđêôơưèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]",
                stripped, re.IGNORECASE
            ))
            latin_ratio = sum(
                c.isascii() and c.isalpha() for c in stripped
            ) / max(len(stripped), 1)
            if not has_vietnamese and latin_ratio > 0.5:
                continue

        filtered.append(line)

    result = '\n'.join(filtered).strip()
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result

# ============================================================
# 3. GỌI API GEMINI (QUÉT TOÀN BỘ HỌ HÀNG FLASH MIỄN PHÍ)
# ============================================================
def call_gemini(prompt: str, api_key: str) -> tuple:
    genai.configure(api_key=api_key)
    
    model_candidates = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b"
    ]

    generation_config = genai.types.GenerationConfig(
        temperature=0.0,
        top_p=0.85,
        max_output_tokens=8192,
    )

    last_error = ""
    for model_name in model_candidates:
        retries = 2
        for i in range(retries):
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text, model_name, ""
            except Exception as err:
                err_str = str(err)
                last_error = err_str
                if "429" in err_str and i < retries - 1:
                    time.sleep(2)
                    continue
                if "404" in err_str or "not found" in err_str.lower():
                    break
                break

    return None, "", last_error

# ============================================================
# 4. XÂY DỰNG PROMPT CHUẨN KẾT NỐI TRI THỨC MỚI NHẤT
# ============================================================
def build_lesson_prompt(lesson_input: str, subject: str, grade: str) -> str:
    return f"""Bạn là giáo viên chuyên môn cao, soạn tài liệu theo chuẩn chương trình giáo dục phổ thông mới nhất bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

NHIỆM VỤ: Soạn nội dung chi tiết bài học "{lesson_input}" môn {subject} lớp {grade}.

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung hoàn toàn bằng TIẾNG VIỆT chuẩn xác. Không chứa từ tiếng Anh, không suy luận nội tâm, không bản nháp.
2. KHÔNG DÙNG DẤU #. Chỉ dùng định dạng đánh số thứ tự cho các phần lớn (1. KIẾN THỨC CỐT LÕI, 2. CÁC LỖI SAI THƯỜNG GẶP, 3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ).
3. Kiến thức phải cực kỳ chính xác, khoa học, sư phạm theo đúng sách Kết Nối Tri Thức.

CẤU TRÚC ĐẦU RA BẮT BUỘC:

1. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
[Viết thành các đoạn văn chi tiết, rõ ràng, giải thích sâu sắc bản chất, định lý, công thức trọng tâm của bài học.]

2. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
[Liệt kê từ 4 đến 5 lỗi sai học sinh hay mắc phải và hướng khắc phục chi tiết bằng tiếng Việt.]

3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
(Hãy tạo ra chính xác 3 câu hỏi trắc nghiệm khách quan 4 lựa chọn A, B, C, D kiểm tra từ mức độ nhận biết đến vận dụng của bài học này).

Cấu trúc mỗi câu trắc nghiệm bắt buộc phải tuân theo định dạng sau để hệ thống tự động nhận diện:
---
[CÂU HỎI 1]
Nội dung câu hỏi cụ thể...
A. Đáp án A
B. Đáp án B
C. Đáp án C
D. Đáp án D
ĐÁP ÁN ĐÚNG: [Chỉ ghi đúng một chữ cái A, B, C hoặc D]
GỢI Ý TƯ DUY: [Gợi ý định hướng cách giải hoặc bản chất kiến thức giúp học sinh tự tư duy, tuyệt đối không tiết lộ trực tiếp đáp án]
---
(Lặp lại đúng định dạng trên cho Câu hỏi 2 và Câu hỏi 3).
"""

# ============================================================
# 5. GIAO DIỆN THANH BÊN (SIDEBAR)
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.header("THIẾT LẬP HỌC TẬP")

        with st.expander("Quét mã QR vào ứng dụng"):
            app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
            st.image(qr_api_url, caption="Quét mã mở trên điện thoại", width=200)
            st.markdown(f"🔗 **Đường dẫn:** [{app_url}]({app_url})")

        st.markdown("---")
        st.subheader("THÔNG TIN HỌC SINH")
        name = st.text_input("Họ và tên:", placeholder="Ví dụ: Nguyễn Minh Nhật")

        st.markdown("---")
        st.subheader("ĐƯỜNG TRUYỀN AI CÁ NHÂN")
        st.link_button(
            "Lấy Mã Miễn Phí (15 giây)",
            "https://aistudio.google.com/app/apikey",
            use_container_width=True
        )

        user_api_key = st.text_input(
            "Dán Mã Kết Nối (API Key):",
            type="password",
            placeholder="Nhập mã bí mật tại đây..."
        )

        if user_api_key:
            st.success("Đang sử dụng đường truyền AI Cá nhân")
            api_key_to_use = user_api_key
        else:
            st.info("Đang sử dụng đường truyền chung")
            try:
                api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
            except Exception:
                api_key_to_use = ""

        st.markdown("<br>", unsafe_allow_html=True)

        grade = st.selectbox(
            "Chọn khối lớp",
            ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
            index=5
        )

        subject = st.selectbox(
            "Môn học cần hỗ trợ",
            ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học",
             "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
            index=0
        )

        st.markdown("---")
        st.info("Triết lý: Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")
        return grade, subject, api_key_to_use

# ============================================================
# 6. XỬ LÝ VÀ HIỂN THỊ CÂU HỎI TRẮC NGHIỆM TƯƠNG TÁC
# ============================================================
def render_interactive_quizzes(raw_text: str):
    """Bóc tách phần câu hỏi trắc nghiệm từ AI và tạo giao diện tương tác màu sắc trực tiếp."""
    # Tìm phần bắt đầu của câu hỏi trắc nghiệm
    parts = re.split(r"3\.\s*HỆ\s*THỐNG\s*CÂU\s*HỎI\s*TRẮC\s*NGHIỆM\s*ĐÁNH\s*GIÁ", raw_text, flags=re.IGNORECASE)
    
    if len(parts) < 2:
        return # Không tìm thấy cấu trúc trắc nghiệm chuẩn

    theory_part = parts[0]
    quiz_part = parts[1]

    # Hiển thị phần lý thuyết và lỗi thường gặp đã được làm sạch
    st.markdown(theory_part)

    st.markdown("<h2 class='main-title'>3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ</h2>", unsafe_allow_html=True)
    st.markdown("Hãy tự lực suy nghĩ và chọn đáp án đúng nhất cho các câu hỏi dưới đây:")

    # Tách các câu hỏi dựa trên pattern [CÂU HỎI x]
    raw_questions = re.split(r"\[CÂU\s*HỎI\s*\d+\]", quiz_part)
    
    q_index = 1
    for q_block in raw_questions:
        if not q_block.strip():
            continue
        
        # Trích xuất đáp án đúng
        ans_match = re.search(r"ĐÁP\s*ÁN\s*ĐÚNG:\s*([A-Da-d])", q_block, re.IGNORECASE)
        correct_ans = ans_match.group(1).strip().upper() if ans_match else "A"

        # Trích xuất gợi ý
        hint_match = re.search(r"GỢI\s*Ý\s*TƯ\s*DUY:\s*(.*?)(?=\n-{2,}|\n\[|$)", q_block, re.DOTALL | re.IGNORECASE)
        hint_text = hint_match.group(1).strip() if hint_match else "Hãy đọc kỹ lại phần lý thuyết cốt lõi ở trên để tìm ra hướng giải quyết."

        # Trích xuất nội dung câu hỏi và các lựa chọn
        clean_q_block = re.sub(r"ĐÁP\s*ÁN\s*ĐÚNG:.*", "", q_block, flags=re.IGNORECASE)
        clean_q_block = re.sub(r"GỢI\s*Ý\s*TƯ\s*DUY:.*", "", clean_q_block, flags=re.DOTALL | re.IGNORECASE)

        lines = [line.strip() for line in clean_q_block.split('\n') if line.strip()]
        
        question_text = ""
        options = []
        for line in lines:
            if re.match(r"^[A-Da-d][\.\)]", line):
                options.append(line)
            elif not options:
                question_text += line + " "

        if not options or len(options) < 4:
            continue

        st.markdown(f"<div class='quiz-box'>", unsafe_allow_html=True)
        st.markdown(f"**Câu {q_index}:** {question_text.strip()}")

        # Tạo Radio Button cho học sinh chọn đáp án
        choice_key = f"q_choice_{q_index}"
        
        # Chuẩn bị danh sách lựa chọn sạch sẽ
        option_labels = []
        option_map = {}
        for opt in options:
            opt_letter = opt[0].upper()
            option_labels.append(opt)
            option_map[opt_letter] = opt

        user_choice = st.radio(
            f"Chọn đáp án cho câu {q_index}:",
            options=option_labels,
            key=choice_key,
            label_visibility="collapsed"
        )

        if user_choice:
            selected_letter = user_choice[0].upper()
            if selected_letter == correct_ans:
                st.markdown(f"<p style='color: #198754; font-weight: bold; margin-top: 10px;'>Chính xác! Bạn đã chọn đúng đáp án {correct_ans}.</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: #dc3545; font-weight: bold; margin-top: 10px;'>Chưa chính xác. Hãy suy nghĩ kỹ lại hoặc xem gợi ý bên dưới.</p>", unsafe_allow_html=True)

        # Nút bấm xem gợi ý (giúp học sinh khi quá bí, tuyệt đối không lộ đáp án)
        with st.expander(f"Gợi ý tư duy cho câu {q_index} (Nhấp để xem khi quá bí)"):
            st.info(hint_text)

        st.markdown(f"</div>", unsafe_allow_html=True)
        q_index += 1

# ============================================================
# 7. GIAO DIỆN CHÍNH VÀ LUỒNG XỬ LÝ TRẠM 1
# ============================================================
def render_main_interface(grade, subject, api_key_to_use):
    st.markdown(
        "<h1 style='text-align: center; color: #0d6efd;'>"
        "GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 18px; font-weight: bold; color: #495057;'>"
        "Trường THPT Tân Hiệp</p>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Học Tập & Phòng Thí Nghiệm",
        "Gia Sư Tương Tác",
        "Khảo Thí Tự Do",
        "Nhật Ký Nghiên Cứu",
        "Thống Kê & Đánh Giá"
    ])

    with tab1:
        st.markdown(f"<h2 class='main-title'>TỰ HỌC & CHIẾM LĨNH KIẾN THỨC: MÔN {subject.upper()} - {grade.upper()}</h2>", unsafe_allow_html=True)
        st.markdown("### Nhập tên bài học em muốn tổng hợp:")
        
        lesson_input = st.text_input(
            "Nhập bài học cần chiếm lĩnh kiến thức:",
            placeholder="Ví dụ: Đồ thị hàm số bậc hai...",
            label_visibility="collapsed"
        )

        btn_soan_bai = st.button("Tổng Hợp Kiến Thức Cốt Lõi", type="primary")

        if btn_soan_bai:
            if not lesson_input.strip():
                st.warning("Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
            elif not api_key_to_use:
                st.error("Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
            else:
                with st.spinner(f"AI đang phân tích bài học: **{lesson_input}** theo chuẩn Kết Nối Tri Thức..."):
                    full_prompt = build_lesson_prompt(lesson_input, subject, grade)
                    response_text, model_used, error = call_gemini(full_prompt, api_key_to_use)

                    if response_text:
                        final_text = clean_ai_response(response_text)
                        st.success(f"Đã hoàn thành tổng hợp kiến thức bài: **{lesson_input}**")
                        st.caption(f"Model kết nối thành công: `{model_used}`")
                        st.markdown("---")
                        
                        # Hiển thị nội dung có phân tích trắc nghiệm tương tác màu sắc
                        render_interactive_quizzes(final_text)
                    else:
                        st.error(f"Không thể kết nối AI. Lỗi chi tiết: `{error}`")

# ============================================================
# 8. KHỞI CHẠY ỨNG DỤNG CHÍNH
# ============================================================
def main():
    setup_page_config()
    grade, subject, api_key_to_use = render_sidebar()
    render_main_interface(grade, subject, api_key_to_use)

if __name__ == "__main__":
    main()

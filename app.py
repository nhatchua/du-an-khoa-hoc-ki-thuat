import re
import streamlit as st
import google.generativeai as genai

# Hàm lọc bỏ hoàn toàn văn bản Tiếng Anh hoặc suy luận nội bộ nếu AI vô tình sinh ra
def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    
    # 1. Bỏ các dòng gạch đầu dòng chứa tiếng Anh dạng "Role:", "Task:", "Curriculum:", "Rule...", "Subject:"
    english_patterns = [
        r'^\s*[\-\*]?\s*Role\s*:.*$',
        r'^\s*[\-\*]?\s*Task\s*:.*$',
        r'^\s*[\-\*]?\s*Curriculum\s*:.*$',
        r'^\s*[\-\*]?\s*Subject\s*:.*$',
        r'^\s*[\-\*]?\s*Grade\s*:.*$',
        r'^\s*[\-\*]?\s*Topic\s*:.*$',
        r'^\s*[\-\*]?\s*Rule\s*\d+\s*:.*$',
        r'^\s*[\-\*]?\s*Strict Rules\s*:.*$',
        r'^\s*[\-\*]?\s*Function\s*:.*$',
        r'^\s*[\-\*]?\s*Graph shape\s*:.*$',
        r'^\s*[\-\*]?\s*Vertex\s*:.*$'
    ]
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Kiểm tra xem dòng đó có khớp với các mẫu tiếng Anh suy luận hay không
        is_english_line = any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in english_patterns)
        if not is_english_line:
            filtered_lines.append(line)
            
    cleaned_text = '\n'.join(filtered_lines).strip()
    return cleaned_text


# --- ĐOẠN XỬ LÝ TRONG TAB 1 ---
if btn_soan_bai:
    if not lesson_input.strip():
        st.warning("⚠️ Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
    elif not api_key_to_use:
        st.error("🔑 Chưa phát hiện Mã Kết Nối! Vui lòng dán Mã Kết Nối (API Key) ở thanh bên trái.")
    else:
        with st.spinner(f"⏳ AI đang phân tích dữ liệu chuẩn SGK Kết Nối Tri Thức cho bài: **{lesson_input}**..."):
            genai.configure(api_key=api_key_to_use)
            
            # Khởi tạo mô hình với System Instruction ép cứng ngôn ngữ
            system_instruction = """
            BẠN LA GIÁO VIÊN NÒNG CỐT CHƯƠNG TRÌNH GDPT 2018 - BỘ SÁCH KẾT NỐI TRI THỨC VỚI CUỘC SỐNG.
            
            QUY TẮC TỐI CẠO (BẮT BUỘC):
            1. CHỈ XUẤT XUẤT NỘI DUNG BẰNG TIẾNG VIỆT 100%. TUYỆT ĐỐI KHÔNG ĐƯỢC XUẤT BẤT KỲ CÂU TỪ, BẢN DỊCH HAY SUY LUẬN BẰNG TIẾNG ANH.
            2. KHÔNG XUẤT "Role:", "Task:", "Curriculum:", "Rule 1:", "Subject:". VÀO THẲNG BÀI VIẾT.
            3. TRÌNH BÀY DƯỚI DẠNG "SỔ TAY KIẾN THỨC CỐT LÕI" (Không trình bày dạng giáo án).
            4. BÀI TẬP BẮT BUỘC CÓ 2 DẠNG: TRẮC NGHIỆM VÀ TỰ LUẬN TRẢ LỜI NGẮN.
            5. PHẦN HƯỚNG DẪN GIẢI ĐẶT TRONG KHỐI <details><summary>...</summary></details> VÀ KHÔNG ĐƯỢC CHO ĐÁP SỐ CUỐI CÙNG.
            """
            
            # Cấu hình giảm độ sáng tạo để tránh ảo giác
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Đặt mức cực thấp để AI bám sát dữ liệu chuẩn SGK
                top_p=0.8
            )
            
            user_prompt = f"""
            Yêu cầu tổng hợp kiến thức bài học:
            - Môn học: {subject}
            - Khối lớp: {grade}
            - Tên bài học: {lesson_input}
            - Bộ sách: Kết nối tri thức với cuộc sống (Chương trình GDPT 2018)

            CẤU TRÚC BẮT BUỘC VIẾT BẰNG TIẾNG VIỆT:

            # 📌 I. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
            (Trình bày khái niệm, định lý, công thức LaTeX chuẩn xác theo SGK)

            # ⚠️ II. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
            (Cảnh báo các sai lầm học sinh hay mắc phải)

            # ✍️ III. BÀI TẬP TƯƠNG TÁC & THỬ THÁCH

            ## 1. Dạng Trắc Nghiệm Tương Tác
            **Câu 1:** (Đề bài)
            A. ...
            B. ...
            C. ...
            D. ...

            <details>
            <summary>🔍 <b>Ấn vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

            - **Bước 1:** ...
            - **Bước 2:** ...
            - **Gợi ý:** (Áp dụng công thức để tự tìm đáp án, TUYỆT ĐỐI KHÔNG GHI ĐÁP ÁN ĐÚNG LÀ A, B, C hay D)
            </details>

            <br>

            ## 2. Dạng Tự Luận Trả Lời Ngắn
            **Câu 2:** (Đề bài tự luận)

            <details>
            <summary>🔍 <b>Ấn vào đây để xem hướng dẫn từng bước (Khi bí quá)</b></summary>

            - **Gợi ý bước 1:** ...
            - **Gợi ý bước 2:** ...
            - **Thử thách:** Học sinh tự tính toán ra kết quả cuối cùng = ...?
            </details>
            """
            
            try:
                # Gọi mô hình với system_instruction
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    user_prompt,
                    generation_config=generation_config
                )
                
                raw_text = response.text if response else ""
                
                # Làm sạch văn bản thông qua hàm xử lý Python
                final_text = clean_ai_response(raw_text)
                
                if final_text:
                    st.success(f"✅ Đã tổng hợp kiến thức bài: **{lesson_input}** ({subject} - {grade})")
                    st.markdown("---")
                    st.markdown(final_text, unsafe_allow_html=True)
                else:
                    st.error("❌ Dữ liệu trả về không hợp lệ, vui lòng thử lại.")
                    
            except Exception as e:
                st.error(f"❌ Lỗi kết nối AI: `{str(e)}`")

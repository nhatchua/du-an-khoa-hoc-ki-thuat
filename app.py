import streamlit as str_app
import google.generativeai as genai
import re
import time
import json
import requests
from datetime import datetime
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# 0. PHÂN LOẠI MÔN HỌC THEO HÌNH THỨC ĐÁNH GIÁ
# ============================================================
# Môn tự luận → sinh đề luyện viết (không có đáp án)
# Môn trắc nghiệm → sinh câu hỏi A/B/C/D
# Muốn thêm/bớt môn tự luận → sửa set dưới đây
ESSAY_SUBJECTS = {"Ngữ văn", "Lịch sử & Địa lý"}

# ============================================================
# 1. CẤU HÌNH GIAO DIỆN TRANG & CSS TƯƠNG THÍCH CHUẨN SÁNG/TỐI
# ============================================================
def setup_page_config():
    str_app.set_page_config(
        page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
        page_icon="📚",
        layout="wide"
    )
    str_app.markdown("""
        <style>
        /* Tiêu đề chính cực kỳ nổi bật */
        .main-heading {
            background: linear-gradient(135deg, #0d6efd 0%, #0dcaf0 100%);
            color: white;
            padding: 14px 22px;
            border-radius: 10px;
            font-weight: 800;
            font-size: 1.3rem;
            margin-top: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(13, 110, 253, 0.2);
        }
        
        /* Khung nội dung cốt lõi: Sử dụng cấu trúc màu sắc an toàn tương thích tốt mọi theme */
        .content-box {
            border-left: 6px solid #0d6efd;
            border-top: 1px solid rgba(128, 128, 128, 0.2);
            border-right: 1px solid rgba(128, 128, 128, 0.2);
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
            line-height: 1.6;
        }

        /* ===== DÀN ĐỀU 5 TAB TRẠM 1-5 ===== */
        /* Khung chứa danh sách tab */
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            width: 100% !important;
            gap: 6px !important;
            justify-content: space-between !important;
        }
        /* Từng tab riêng lẻ */
        .stTabs [data-baseweb="tab-list"] > button {
            flex: 1 1 0 !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: nowrap !important;
            padding: 10px 8px !important;
            border-radius: 8px 8px 0 0 !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            transition: all 0.2s ease !important;
        }
        /* Hover: nền xanh nhạt */
        .stTabs [data-baseweb="tab-list"] > button:hover {
            background-color: rgba(13, 110, 253, 0.08) !important;
        }
        /* Tab đang chọn: nền xanh nhạt đậm hơn */
        .stTabs [data-baseweb="tab-list"] > button[aria-selected="true"] {
            background-color: rgba(13, 110, 253, 0.12) !important;
        }

        /* ===== GIẢM FONT CHỮ TRONG KHUNG CÂU HỎI / ĐỀ BÀI ===== */
        /* Áp dụng cho mọi nội dung nằm trong container có viền (border=True) */
        [data-testid="stVerticalBlockBorderWrapper"] p {
            font-size: 0.92rem !important;
            line-height: 1.55 !important;
            margin-bottom: 6px !important;
        }
        /* Tiêu đề "Câu X:" hoặc "Đề X" bên trong khung — nhỏ hơn mặc định 1 chút */
        [data-testid="stVerticalBlockBorderWrapper"] h3 {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            margin-bottom: 10px !important;
        }
        /* Radio A/B/C/D và expander bên trong khung cũng thu nhỏ tương ứng */
        [data-testid="stVerticalBlockBorderWrapper"] .stRadio label,
        [data-testid="stVerticalBlockBorderWrapper"] .stExpander summary {
            font-size: 0.9rem !important;
        }
        </style>
        
        <!-- Thư viện MathJax hỗ trợ render kí hiệu toán học chuẩn LaTeX -->
        <script type="text/javascript" async
          src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
        </script>
    """, unsafe_allow_html=True)
# ============================================================
# 2. XỬ LÝ VÀ LỌC SẠCH PHẢN HỒI TỪ AI
# ============================================================
def clean_ai_response(text: str) -> str:
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
# 3B. GỌI API GEMINI — HỖ TRỢ ẢNH + SYSTEM INSTRUCTION
# ============================================================
def call_gemini_with_fallback(prompt, api_key: str, system_instruction: str = "") -> str:
    """
    Hỗ trợ prompt dạng str HOẶC list [text, PIL.Image].
    Hỗ trợ system_instruction (dặn dò nhân vật AI).
    Trả về chuỗi text phản hồi, hoặc chuỗi rỗng "" nếu lỗi toàn bộ.
    """
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

    for model_name in model_candidates:
        try:
            kwargs = {
                "model_name": model_name,
                "generation_config": generation_config,
            }
            if system_instruction:
                kwargs["system_instruction"] = system_instruction
            
            model = genai.GenerativeModel(**kwargs)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as err:
            err_str = str(err)
            if "429" in err_str:
                time.sleep(2)
                continue
            continue

    return ""

# ============================================================
# 4. XÂY DỰNG PROMPT CHUẨN KẾT NỐI TRI THỨC + HỖ TRỢ LATEX
# ============================================================
def build_lesson_prompt(lesson_input: str, subject: str, grade: str) -> str:
    is_essay = subject in ESSAY_SUBJECTS

    common_head = f"""Bạn là giáo viên chuyên môn cao, soạn tài liệu theo chuẩn chương trình giáo dục phổ thông mới nhất bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

NHIỆM VỤ: Soạn nội dung chi tiết bài học "{lesson_input}" môn {subject} lớp {grade}.

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung hoàn toàn bằng TIẾNG VIỆT chuẩn xác. Không chứa từ tiếng Anh, không suy luận nội tâm, không bản nháp.
2. KHÔNG DÙNG DẤU #. Chỉ dùng định dạng đánh số thứ tự cho các phần lớn.
3. ĐỐI VỚI CÔNG THỨC TOÁN HỌC/KÍ HIỆU KHOA HỌC: Bắt buộc sử dụng kí hiệu LaTeX đặt trong cặp dấu đô la (ví dụ: $x^2 + y^2 = R^2$, $\\frac{{a}}{{b}}$, $\\sqrt{{x}}$) để hiển thị chuẩn xác, đẹp mắt.
4. Kiến thức phải cực kỳ chính xác, khoa học, sư phạm theo đúng sách Kết Nối Tri Thức.

CẤU TRÚC ĐẦU RA BẮT BUỘC:

1. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
[Viết thành các đoạn văn chi tiết, rõ ràng, giải thích sâu sắc bản chất, định lý, công thức trọng tâm của bài học. Sử dụng LaTeX cho mọi công thức toán học.]

2. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
[Liệt kê từ 4 đến 5 lỗi sai học sinh hay mắc phải và hướng khắc phục chi tiết bằng tiếng Việt.]

"""

    if is_essay:
        tail = """3. HỆ THỐNG ĐỀ LUYỆN VIẾT
(Hãy tạo ra chính xác 3 đề luyện viết theo cấu trúc đề kiểm tra/đề thi thật, độ khó tăng dần từ nhận biết đến vận dụng cao. KHÔNG đưa đáp án hay bài văn mẫu, chỉ đưa đề bài và gợi ý dàn ý.)

Cấu trúc mỗi đề bắt buộc phải tuân theo định dạng sau để hệ thống tự động nhận diện:
---
[ĐỀ 1]
Loại đề: [Ví dụ: Nghị luận văn học / Nghị luận xã hội / Phân tích nhân vật / Cảm nhận đoạn thơ...]
Đề bài: [Nội dung đề bài đầy đủ, rõ ràng, giống đề kiểm tra thật — có thể trích dẫn ngữ liệu nếu cần]
Yêu cầu: [Yêu cầu cụ thể về hình thức, dung lượng, thao tác lập luận...]
Thang điểm: [Thang điểm tham khảo, ví dụ 2.0 / 3.0 / 5.0 điểm]
GỢI Ý DÀN Ý: [Dàn ý gợi ý ngắn gọn theo các ý chính — chỉ để học sinh định hướng, KHÔNG viết thành bài văn hoàn chỉnh]
---
(Lặp lại đúng định dạng trên cho ĐỀ 2 và ĐỀ 3)."""
    else:
        tail = """3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
(Hãy tạo ra chính xác 3 câu hỏi trắc nghiệm khách quan 4 lựa chọn A, B, C, D kiểm tra từ mức độ nhận biết đến vận dụng của bài học này).

Cấu trúc mỗi câu trắc nghiệm bắt buộc phải tuân theo định dạng sau để hệ thống tự động nhận diện:
---
[CÂU HỎI 1]
Nội dung câu hỏi cụ thể (có chứa công thức LaTeX nếu cần)...
A. Đáp án A
B. Đáp án B
C. Đáp án C
D. Đáp án D
ĐÁP ÁN ĐÚNG: [Chỉ ghi đúng một chữ cái A, B, C hoặc D]
GỢI Ý TƯ DUY: [Gợi ý định hướng cách giải hoặc bản chất kiến thức giúp học sinh tự tư duy, tuyệt đối không tiết lộ trực tiếp đáp án]
---
(Lặp lại đúng định dạng trên cho Câu hỏi 2 và Câu hỏi 3)."""

    return common_head + tail

# ============================================================
# 4B. XÂY DỰNG PROMPT PHÒNG THÍ NGHIỆM ẢO
# ============================================================
def build_virtual_lab_prompt(lab_request: str, subject: str, grade: str) -> str:
    template = """Bạn là chuyên gia mô phỏng thí nghiệm giáo dục, phục vụ học sinh __GRADE__ môn __SUBJECT__ theo chương trình GDPT 2018 bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

YÊU CẦU CỦA HỌC SINH: __LAB_REQUEST__

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung bằng TIẾNG VIỆT chuẩn xác, không suy luận nội tâm, không bản nháp.
2. Sử dụng LaTeX đặt trong cặp dấu đô la cho mọi công thức (ví dụ: $v = v_0 + at$, $H_2SO_4$, $\\vec{AB} = (x, y, z)$).
3. KHÔNG DÙNG DẤU #.
4. Kiến thức phải cực kỳ chính xác theo chuẩn SGK Kết Nối Tri Thức.

CẤU TRÚC ĐẦU RA BẮT BUỘC:

1. MÔ TẢ THÍ NGHIỆM / HIỆN TƯỢNG
[Mô tả chi tiết thí nghiệm, hiện tượng, quá trình, dụng cụ (nếu có) — phù hợp với môn học.]

2. NGUYÊN LÝ / PHƯƠNG TRÌNH / HIỆN TƯỢNG XẢY RA
[Giải thích bản chất khoa học, phương trình phản ứng hóa học, phương trình chuyển động, định lý toán học... Sử dụng LaTeX đầy đủ.]

3. KẾT QUẢ / QUAN SÁT ĐƯỢC
[Mô tả kết quả, số liệu, hiện tượng quan sát được, kết luận rút ra.]

4. MÃ VẼ ĐỒ THỊ MINH HỌA (chỉ khi phù hợp — nếu không phù hợp, ghi rõ "Không cần vẽ đồ thị")

QUY TẮC CHỌN LOẠI ĐỒ THỊ:
- ĐỒ THỊ 2D (matplotlib): hàm số, dao động, parabol, hypebol, phản ứng hóa học dạng đường, biểu đồ cột → đặt trong thẻ <PLOT_2D>...</PLOT_2D>
- ĐỒ THỊ 3D (plotly): hệ trục Oxyz, hình học không gian, mặt phẳng, mặt cầu, vector 3 chiều, khối đa diện → đặt trong thẻ <PLOT_3D>...</PLOT_3D>

=== PHONG CÁCH VẼ ĐỒ THỊ 2D THEO CHUẨN SGK VIỆT NAM (BẮT BUỘC TUÂN THEO) ===
Đồ thị 2D phải giống hình vẽ trong SGK Toán/Lý/Hóa Việt Nam:
- Trục Ox nằm ngang, trục Oy thẳng đứng, GIAO NHAU tại gốc O
- Đầu trục Ox có MŨI TÊN chỉ sang phải, đầu trục Oy có MŨI TÊN chỉ lên trên
- KHÔNG có khung viền hình chữ nhật quanh đồ thị
- CÓ LƯỚI Ô VUÔNG mảnh, màu xám nhạt, nét liền mảnh
- Nhãn "O" ở gốc tọa độ, nhãn "x" ở đầu trục Ox, nhãn "y" ở đầu trục Oy
- Vạch chia đơn vị rõ ràng trên cả 2 trục
- Điểm đặc biệt (cực trị, giao điểm, đỉnh) phải:
  + Đánh dấu bằng chấm tròn đỏ
  + Kẻ NÉT ĐỨT (màu đỏ, mảnh) từ điểm xuống 2 trục
  + Ghi tọa độ dạng "(x; y)" bên cạnh điểm
- Đường cong chính vẽ màu xanh đậm, nét liền, đậm
- Tiêu đề đặt phía dưới đồ thị, có tiền tố "Hình:" (ví dụ: "Hình 1. Đồ thị hàm số y = x² - 2x - 1")
- Font chữ hỗ trợ tiếng Việt

=== MẪU ĐỒ THỊ 2D CHUẨN SGK (có lưới ô vuông) ===
<PLOT_2D>
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))

# Vẽ đường cong hàm số
x = np.linspace(-2, 4, 400)
y = x**2 - 2*x - 1
ax.plot(x, y, color='#1f4e9c', linewidth=2, label='y = x² - 2x - 1')

# TRỤC TỌA ĐỘ KIỂU SGK
ax.spines['left'].set_position('zero')
ax.spines['bottom'].set_position('zero')
ax.spines['right'].set_color('none')
ax.spines['top'].set_color('none')
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

# Mũi tên ở đầu trục Ox và Oy
ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False, markersize=8)
ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False, markersize=8)

# Nhãn O, x, y
ax.text(-0.15, -0.3, 'O', fontsize=14, fontweight='bold')
ax.text(4.15, -0.3, 'x', fontsize=14, fontweight='bold', style='italic')
ax.text(-0.3, 5.5, 'y', fontsize=14, fontweight='bold', style='italic')

# LƯỚI Ô VUÔNG
ax.set_xticks(np.arange(-3, 6, 1))
ax.set_yticks(np.arange(-4, 7, 1))
ax.grid(True, which='both', color='gray', linestyle='-', linewidth=0.5, alpha=0.4)
ax.set_axisbelow(True)

# Điểm cực trị (đỉnh parabol)
vertex_x, vertex_y = 1, -2

# Nét đứt từ đỉnh xuống 2 trục
ax.plot([vertex_x, vertex_x], [0, vertex_y], color='red', linestyle='--', linewidth=1.2)
ax.plot([0, vertex_x], [vertex_y, vertex_y], color='red', linestyle='--', linewidth=1.2)

# Chấm tròn đỏ tại đỉnh
ax.plot(vertex_x, vertex_y, 'o', color='red', markersize=8, zorder=5)

# Ghi tọa độ đỉnh
label_text = "(" + str(vertex_x) + "; " + str(vertex_y) + ")"
ax.text(vertex_x + 0.15, vertex_y - 0.4, label_text,
        fontsize=11, color='red', fontweight='bold')

# Đặt giới hạn trục
ax.set_xlim(-2.5, 4.5)
ax.set_ylim(-3, 6)

# Tick nhỏ
ax.tick_params(axis='both', labelsize=10)

# Tiêu đề dưới đồ thị
plt.figtext(0.5, 0.02, 'Hình 1. Đồ thị hàm số y = x² - 2x - 1',
            ha='center', fontsize=11, style='italic')

plt.tight_layout(rect=[0, 0.05, 1, 1])
fig.savefig("/tmp/lab_plot.png", dpi=120, bbox_inches="tight")
</PLOT_2D>

=== PHONG CÁCH VẼ HÌNH KHÔNG GIAN 3D (BẮT BUỘC TUÂN THEO) ===
Áp dụng đồng thời cả 3 yếu tố sau để hình vừa giống SGK, vừa đúng khi học sinh xoay:

a) CẠNH NHÌN THẤY (nét liền): dùng line=dict(color='#1f77b4', width=6)
   Áp dụng cho cạnh đáy, cạnh bên ở mặt trước (không bị che khuất).

b) CẠNH BỊ KHUẤT (nét đứt): dùng line=dict(color='#1f77b4', width=4, dash='dash')
   Áp dụng cho cạnh bị che khuất ở góc nhìn mặc định.

c) MẶT PHẲNG (nếu có): vẽ dạng go.Mesh3d với opacity=0.25-0.35, màu nhạt.

d) ĐỈNH: hiển thị tên đỉnh (A, B, C, S...) bằng Scatter3d mode='text', font size 14, màu đen.

e) HỆ TRỤC Oxyz (nếu cần): vẽ 3 mũi tên bằng Scatter3d mode='lines', màu đỏ (x), xanh lá (y), xanh dương (z).

=== MẪU ĐỒ THỊ 3D — HÌNH CHÓP S.ABC ===
<PLOT_3D>
import plotly.graph_objects as go

fig = go.Figure()

S = [0, 0, 4]
A = [3, 0, 0]
B = [0, 4, 0]
C = [-2, -2, 0]

visible_edges = [(A, B), (B, C), (C, A), (S, A), (S, B)]
for p1, p2 in visible_edges:
    fig.add_trace(go.Scatter3d(
        x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=6), showlegend=False
    ))

hidden_edges = [(S, C)]
for p1, p2 in hidden_edges:
    fig.add_trace(go.Scatter3d(
        x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=4, dash='dash'), showlegend=False
    ))

fig.add_trace(go.Mesh3d(
    x=[A[0], B[0], C[0]], y=[A[1], B[1], C[1]], z=[A[2], B[2], C[2]],
    color='lightblue', opacity=0.3, showlegend=False, hoverinfo='skip'
))

for name, p in [('S', S), ('A', A), ('B', B), ('C', C)]:
    fig.add_trace(go.Scatter3d(
        x=[p[0]], y=[p[1]], z=[p[2]], mode='text',
        text=[name], textfont=dict(size=14, color='black'), showlegend=False
    ))

fig.update_layout(
    title='Hình chóp S.ABC',
    scene=dict(
        xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube',
        camera=dict(eye=dict(x=1.25, y=1.25, z=1.25))
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    height=600
)
</PLOT_3D>

=== MẪU ĐỒ THỊ 3D — HỆ TRỤC Oxyz ===
<PLOT_3D>
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Scatter3d(x=[0, 5], y=[0, 0], z=[0, 0], mode='lines+text',
    line=dict(color='red', width=8), text=['', 'x'], textposition='top center',
    textfont=dict(size=14, color='red'), showlegend=False))
fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 5], z=[0, 0], mode='lines+text',
    line=dict(color='green', width=8), text=['', 'y'], textposition='top center',
    textfont=dict(size=14, color='green'), showlegend=False))
fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[0, 5], mode='lines+text',
    line=dict(color='blue', width=8), text=['', 'z'], textposition='top center',
    textfont=dict(size=14, color='blue'), showlegend=False))

fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode='text',
    text=['O'], textfont=dict(size=14, color='black'), showlegend=False))

fig.update_layout(
    title='Hệ trục tọa độ Oxyz',
    scene=dict(
        xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube'
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    height=600
)
</PLOT_3D>

LƯU Ý QUAN TRỌNG:
- 2D: PHẢI vẽ theo phong cách SGK (trục có mũi tên, lưới ô vuông mảnh, nét đứt đánh dấu điểm đặc biệt)
- 2D: BẮT BUỘC đặt ax.set_xticks() và ax.set_yticks() với khoảng cách đều để lưới thành ô vuông
- 2D: KẾT THÚC bằng fig.savefig("/tmp/lab_plot.png", dpi=120, bbox_inches="tight")
- 3D: dùng plotly, KẾT THÚC bằng việc tạo biến fig (KHÔNG gọi fig.show())
- CHỈ dùng: matplotlib.pyplot, numpy, math, plotly.graph_objects, plotly.express
- KHÔNG đọc file ngoài, KHÔNG gọi plt.show()
- Nhãn trục, tiêu đề bằng tiếng Việt có dấu
- Với 2D: LUÔN ghi tiêu đề dạng "Hình N. Mô tả ngắn" phía dưới đồ thị
- Với 3D: LUÔN dùng go.Mesh3d với opacity thấp cho các mặt phẳng cần hiển thị
- Nếu môn không cần đồ thị, bỏ qua phần 4 hoàn toàn."""

    return template.replace("__LAB_REQUEST__", lab_request).replace("__SUBJECT__", subject).replace("__GRADE__", grade)

# ============================================================
# 4C. CHẠY CODE VẼ ĐỒ THỊ AN TOÀN
# ============================================================
def run_plot_code(code_str: str):
    """
    Chạy code vẽ đồ thị an toàn.
    Trả về tuple (kind, data):
      - ("png", "/tmp/lab_plot.png") nếu matplotlib
      - ("plotly", fig_object) nếu plotly
      - (None, None) nếu lỗi
    """
    import os

    plot_path = "/tmp/lab_plot.png"
    if os.path.exists(plot_path):
        try:
            os.remove(plot_path)
        except Exception:
            pass

    safe_builtins = {
        "range": range, "len": len, "min": min, "max": max,
        "abs": abs, "round": round, "sum": sum, "float": float,
        "int": int, "str": str, "list": list, "tuple": tuple,
        "dict": dict, "print": print, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter, "pow": pow,
        "divmod": divmod, "sorted": sorted, "reversed": reversed,
        "bool": bool, "set": set, "frozenset": frozenset,
        "type": type, "isinstance": isinstance, "hasattr": hasattr,
        "getattr": getattr, "setattr": setattr,
        "__import__": __import__,
    }

    # Pre-import plotly (nếu có)
    try:
        import plotly.graph_objects as go
        import plotly.express as px
    except ImportError:
        go = None
        px = None

    namespace = {
        "plt": plt,
        "np": np,
        "math": __import__("math"),
        "__builtins__": safe_builtins,
    }
    if go is not None:
        namespace["go"] = go
        namespace["px"] = px

    try:
        exec(code_str, namespace)

        # Ưu tiên Plotly nếu fig có method to_plotly_json
        fig_var = namespace.get("fig")
        if fig_var is not None and hasattr(fig_var, "to_plotly_json"):
            return ("plotly", fig_var)

        # Fallback matplotlib: nếu chưa save, tự save
        if not os.path.exists(plot_path):
            try:
                plt.savefig(plot_path, dpi=100, bbox_inches="tight")
            except Exception:
                pass

        if os.path.exists(plot_path):
            return ("png", plot_path)
        return (None, None)
    finally:
        plt.close('all')


# ============================================================
# 4D. TRIGGER RENDER LẠI MATHJAX
# ============================================================
def trigger_mathjax():
    """Buộc MathJax typeset lại nội dung — fix lỗi LaTeX thỉnh thoảng không render."""
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        try {
            var pw = window.parent;
            if (pw && pw.MathJax && pw.MathJax.Hub) {
                pw.MathJax.Hub.Queue(["Typeset", pw.MathJax.Hub]);
            }
        } catch(e) {}
    })();
    </script>
    """, height=0)

# ============================================================
# 5. GIAO DIỆN THANH BÊN (SIDEBAR)
# ============================================================
def render_sidebar():
    with str_app.sidebar:
        str_app.header("THIẾT LẬP HỌC TẬP")

        with str_app.expander("Quét mã QR vào ứng dụng"):
            app_url = "https://du-an-khoa-hoc-ki-thuat-2026.streamlit.app/"
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
            str_app.image(qr_api_url, caption="Quét mã mở trên điện thoại", width=200)
            str_app.markdown(f"🔗 **Đường dẫn:** [{app_url}]({app_url})")

        str_app.markdown("---")
        str_app.subheader("THÔNG TIN HỌC SINH")
        name = str_app.text_input("Họ và tên:", placeholder="Ví dụ: Nguyễn Minh Nhật")

        str_app.markdown("---")
        str_app.subheader("ĐƯỜNG TRUYỀN AI CÁ NHÂN")
        str_app.link_button(
            "Lấy Mã Miễn Phí (15 giây)",
            "https://aistudio.google.com/app/apikey",
            use_container_width=True
        )

        user_api_key = str_app.text_input(
            "Dán Mã Kết Nối (API Key):",
            type="password",
            placeholder="Nhập mã bí mật tại đây..."
        )

        if user_api_key:
            str_app.success("Đang sử dụng đường truyền AI Cá nhân")
            api_key_to_use = user_api_key
        else:
            str_app.info("Đang sử dụng đường truyền chung")
            try:
                api_key_to_use = str_app.secrets.get("GEMINI_API_KEY", "")
            except Exception:
                api_key_to_use = ""

        str_app.markdown("<br>", unsafe_allow_html=True)

        grade = str_app.selectbox(
            "Chọn khối lớp",
            ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12"],
            index=5
        )

        subject = str_app.selectbox(
            "Môn học cần hỗ trợ",
            ["Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học",
             "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lý"],
            index=0
        )

        str_app.markdown("---")
        str_app.info("Triết lý: Dưỡng thiện tâm - Ươm nhân tài • Dẫn dắt tư duy tự học!")
        return grade, subject, api_key_to_use

# ============================================================
# 6. HIỂN THỊ NỘI DUNG VÀ TRẮC NGHIỆM TƯƠNG TÁC
# ============================================================
def render_interactive_quizzes(raw_text: str, subject: str):
    is_essay = subject in ESSAY_SUBJECTS

    if is_essay:
        section_regex = r"3\.\s*HỆ\s*THỐNG\s*ĐỀ\s*LUYỆN\s*VIẾT"
        display_header = "3. HỆ THỐNG ĐỀ LUYỆN VIẾT"
        sub_title = "Hãy tự lực viết vào tập. Không có đáp án mẫu — hãy viết bằng chính tư duy của em."
    else:
        section_regex = r"3\.\s*HỆ\s*THỐNG\s*CÂU\s*HỎI\s*TRẮC\s*NGHIỆM\s*ĐÁNH\s*GIÁ"
        display_header = "3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ"
        sub_title = "Hãy tự lực suy nghĩ và chọn đáp án đúng nhất cho các câu hỏi dưới đây:"

    parts = re.split(section_regex, raw_text, flags=re.IGNORECASE)

    if len(parts) < 2:
        str_app.markdown(f"<div class='content-box'>{raw_text}</div>", unsafe_allow_html=True)
        return

    theory_part = parts[0]
    exercise_part = parts[1]

    theory_part = re.sub(
        r"(1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI\s*CẦN\s*GHI\s*NHỚ)",
        r"<div class='main-heading'>\1</div>",
        theory_part, flags=re.IGNORECASE
    )
    theory_part = re.sub(
        r"(2\.\s*CÁC\s*LỖI\s*SAI\s*THƯỜNG\s*GẶP\s*KHI\s*LÀM\s*BÀI)",
        r"<div class='main-heading'>\1</div>",
        theory_part, flags=re.IGNORECASE
    )

    str_app.markdown(f"<div class='content-box'>{theory_part}</div>", unsafe_allow_html=True)
    str_app.markdown(f"<div class='main-heading'>{display_header}</div>", unsafe_allow_html=True)
    str_app.markdown(f"<p style='font-weight: 500; margin-bottom: 20px;'>{sub_title}</p>", unsafe_allow_html=True)

    # ==================== NHÁNH TỰ LUẬN ====================
    if is_essay:
        essay_blocks = re.findall(r"\[ĐỀ\s*\d+\](.*?)(?=\[ĐỀ\s*\d+\]|\Z)", exercise_part, re.DOTALL | re.IGNORECASE)

        d_index = 1
        for e_block in essay_blocks:
            if not e_block.strip():
                continue

            e_block = e_block.strip()
            e_block = re.sub(r"\n?-{2,}\s*$", "", e_block).strip()

            hint_match = re.search(r"GỢI\s*Ý\s*DÀN\s*Ý\s*:\s*(.*)", e_block, re.DOTALL | re.IGNORECASE)
            if hint_match:
                main_content = e_block[:hint_match.start()].strip()
                hint_content = hint_match.group(1).strip()
            else:
                main_content = e_block
                hint_content = ""

            with str_app.container(border=True):
                str_app.markdown(f"### 📝 Đề {d_index}")
                str_app.markdown(main_content)

                if hint_content:
                    with str_app.expander(f"Gợi ý dàn ý cho đề {d_index} (Nhấp để xem khi cần định hướng)"):
                        str_app.info(hint_content)

            d_index += 1
        return

    # ==================== NHÁNH TRẮC NGHIỆM ====================
    question_blocks = re.findall(r"\[CÂU\s*HỎI\s*\d+\](.*?)(?=\[CÂU\s*HỎI|\Z)", exercise_part, re.DOTALL | re.IGNORECASE)

    q_index = 1
    for q_block in question_blocks:
        if not q_block.strip():
            continue

        ans_match = re.search(r"ĐÁP\s*ÁN\s*ĐÚNG:\s*([A-Da-d])", q_block, re.IGNORECASE)
        correct_ans = ans_match.group(1).strip().upper() if ans_match else "A"

        hint_match = re.search(r"GỢI\s*Ý\s*TƯ\s*DUY:\s*(.*?)(?=\n-{2,}|\n\[|$)", q_block, re.DOTALL | re.IGNORECASE)
        hint_text = hint_match.group(1).strip() if hint_match else "Hãy đọc kỹ lại phần lý thuyết cốt lõi ở trên để tìm ra hướng giải quyết."

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

        with str_app.container(border=True):
            str_app.markdown(f"**Câu {q_index}:** {question_text.strip()}")

            for opt in options:
                str_app.markdown(f"{opt}")

            choice_key = f"q_choice_{q_index}"
            checked_key = f"q_checked_{q_index}"

            if checked_key not in str_app.session_state:
                str_app.session_state[checked_key] = False

            user_choice = str_app.radio(
                f"Chọn đáp án cho câu {q_index}:",
                options=["A", "B", "C", "D"],
                index=None,
                key=choice_key,
                horizontal=True,
                label_visibility="collapsed"
            )

            btn_clicked = str_app.button(
                "✅ Kiểm tra kết quả",
                key=f"check_btn_{q_index}",
                type="primary"
            )

            if btn_clicked:
                if not user_choice:
                    str_app.warning("Em chưa chọn đáp án. Hãy chọn A, B, C hoặc D trước khi kiểm tra!")
                else:
                    str_app.session_state[checked_key] = True

            # Chỉ hiển thị kết quả khi đã bấm "Kiểm tra kết quả"
            if str_app.session_state[checked_key] and user_choice:
                if user_choice == correct_ans:
                    str_app.markdown(
                        "<p style='color: #28a745; font-weight: bold; margin-top: 10px;'>"
                        "Chính xác! Em đã chọn đúng đáp án.</p>",
                        unsafe_allow_html=True
                    )
                else:
                    str_app.markdown(
                        "<p style='color: #dc3545; font-weight: bold; margin-top: 10px;'>"
                        "Chưa chính xác. Hãy xem gợi ý tư duy bên dưới để tự tìm ra lỗi sai.</p>",
                        unsafe_allow_html=True
                    )

                with str_app.expander(f"💡 Gợi ý tư duy cho câu {q_index}", expanded=True):
                    str_app.info(hint_text)
            else:
                with str_app.expander(f"Gợi ý tư duy cho câu {q_index} (Nhấp để xem khi quá bí)", expanded=False):
                    str_app.info(hint_text)

        q_index += 1

# ============================================================
# 7. GIAO DIỆN CHÍNH VÀ LUỒNG XỬ LÝ TRẠM 1
# ============================================================
def render_main_interface(grade, subject, api_key_to_use):
    str_app.markdown(
        "<h1 style='text-align: center; color: #0d6efd;'>"
        "GIA SƯ AI - HỆ SINH THÁI LỚP HỌC ĐẢO NGƯỢC</h1>",
        unsafe_allow_html=True
    )
    str_app.markdown(
        "<p style='text-align: center; font-size: 18px; font-weight: bold;'>"
        "Trường THPT Tân Hiệp</p>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4, tab5 = str_app.tabs([
        "📚 Học Tập & Phòng Thí Nghiệm",
        "💬 Gia Sư Tương Tác",
        "📝 Khảo Thí Tự Do",
        "📖 Nhật Ký Nghiên Cứu",
        "📊 Thống Kê & Đánh Giá"
    ])

    # ==================== TAB 1 ====================
    with tab1:
        str_app.markdown(f"<div class='main-heading' style='text-align: center;'>TỰ HỌC & CHIẾM LĨNH KIẾN THỨC: MÔN {subject.upper()} - {grade.upper()}</div>", unsafe_allow_html=True)
        str_app.markdown("### Nhập tên bài học em muốn tổng hợp:")

        lesson_input = str_app.text_input(
            "Nhập bài học cần chiếm lĩnh kiến thức:",
            placeholder="Ví dụ: Đồ thị hàm số bậc hai...",
            label_visibility="collapsed",
            key="lesson_input_tab1"
        )

        btn_soan_bai = str_app.button("Tổng Hợp Kiến Thức Cốt Lõi", type="primary", key="btn_soan_bai_tab1")

        if btn_soan_bai:
            if not lesson_input.strip():
                str_app.warning("Vui lòng nhập tên bài học trước khi bấm tổng hợp!")
            elif not api_key_to_use:
                str_app.error("Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
            else:
                with str_app.spinner(f"AI đang phân tích bài học: **{lesson_input}** theo chuẩn Kết Nối Tri Thức..."):
                    full_prompt = build_lesson_prompt(lesson_input, subject, grade)
                    response_text, model_used, error = call_gemini(full_prompt, api_key_to_use)

                    if response_text:
                        final_text = clean_ai_response(response_text)
                        str_app.session_state["cached_lesson_result"] = final_text
                        str_app.session_state["cached_model_used"] = model_used
                        str_app.session_state["cached_lesson_name"] = lesson_input
                    else:
                        str_app.error(f"Không thể kết nối AI. Lỗi chi tiết: `{error}`")

        if "cached_lesson_result" in str_app.session_state:
            str_app.success(f"Đã hoàn thành tổng hợp kiến thức bài: **{str_app.session_state.get('cached_lesson_name', '')}**")
            str_app.caption(f"Model kết nối thành công: `{str_app.session_state.get('cached_model_used', '')}`")
            str_app.markdown("---")
            render_interactive_quizzes(str_app.session_state["cached_lesson_result"], subject)
            trigger_mathjax()

        # ========== PHÒNG THÍ NGHIỆM ẢO ==========
        str_app.markdown("---")
        str_app.markdown(
            "<div class='main-heading' style='text-align: center;'>"
            "🔬 PHÒNG THÍ NGHIỆM ẢO THEO YÊU CẦU</div>",
            unsafe_allow_html=True
        )
        str_app.markdown(
            f"Hệ thống AI đang liên kết trực tiếp với môn **{subject} - {grade}**. "
            "Hãy nhập yêu cầu mô phỏng thí nghiệm, hiện tượng, đồ thị hoặc quá trình em muốn quan sát:"
        )

        lab_request = str_app.text_input(
            "Nhập yêu cầu thí nghiệm:",
            placeholder="Ví dụ: Đồ thị hàm số y = x² - 2x + 1... / Phản ứng H₂ + O₂... / Hình chóp S.ABC...",
            label_visibility="collapsed",
            key="lab_request_input"
        )

        btn_lab = str_app.button("🚀 Khởi chạy Phòng Lab", type="primary", key="btn_run_lab")

        if btn_lab:
            if not lab_request.strip():
                str_app.warning("Vui lòng nhập yêu cầu thí nghiệm trước khi khởi chạy!")
            elif not api_key_to_use:
                str_app.error("Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
            else:
                with str_app.spinner(f"AI đang mô phỏng: **{lab_request}**..."):
                    lab_prompt = build_virtual_lab_prompt(lab_request, subject, grade)
                    lab_response, _, lab_error = call_gemini(lab_prompt, api_key_to_use)

                    if lab_response:
                        str_app.session_state["lab_result"] = lab_response
                        str_app.session_state["lab_request_name"] = lab_request
                    else:
                        str_app.error(f"Không thể kết nối AI. Lỗi chi tiết: `{lab_error}`")

        if "lab_result" in str_app.session_state:
            raw_lab = str_app.session_state["lab_result"]

            # Tách khối PLOT_2D / PLOT_3D / PLOT (fallback) ra khỏi phần mô tả
            plot_2d_match = re.search(r"<PLOT_2D>(.*?)</PLOT_2D>", raw_lab, re.DOTALL | re.IGNORECASE)
            plot_3d_match = re.search(r"<PLOT_3D>(.*?)</PLOT_3D>", raw_lab, re.DOTALL | re.IGNORECASE)
            plot_old_match = re.search(r"<PLOT>(.*?)</PLOT>", raw_lab, re.DOTALL | re.IGNORECASE)

            text_part = re.sub(r"<PLOT_2D>.*?</PLOT_2D>", "", raw_lab, flags=re.DOTALL | re.IGNORECASE)
            text_part = re.sub(r"<PLOT_3D>.*?</PLOT_3D>", "", text_part, flags=re.DOTALL | re.IGNORECASE)
            text_part = re.sub(r"<PLOT>.*?</PLOT>", "", text_part, flags=re.DOTALL | re.IGNORECASE).strip()

            # Hiển thị mô tả (dùng content-box)
            clean_text = clean_ai_response(text_part)
            str_app.markdown(
                f"<div class='content-box'>{clean_text}</div>",
                unsafe_allow_html=True
            )

            # Xác định code plot và nhãn hiển thị
            plot_code = None
            plot_label = ""
            if plot_3d_match:
                plot_code = plot_3d_match.group(1).strip()
                plot_label = "#### 🌐 Đồ thị 3D tương tác (giữ chuột trái để xoay, cuộn để zoom)"
            elif plot_2d_match:
                plot_code = plot_2d_match.group(1).strip()
                plot_label = "#### 📈 Đồ thị minh họa"
            elif plot_old_match:
                plot_code = plot_old_match.group(1).strip()
                plot_label = "#### 📈 Đồ thị minh họa"

            if plot_code:
                try:
                    kind, data = run_plot_code(plot_code)
                    if kind == "png" and data:
                        str_app.markdown(plot_label)
                        str_app.image(data, use_container_width=True)
                    elif kind == "plotly" and data is not None:
                        str_app.markdown(plot_label)
                        str_app.plotly_chart(data, use_container_width=True)
                    else:
                        str_app.warning("AI đã sinh code vẽ nhưng không tạo được đồ thị.")
                except Exception as plot_err:
                    str_app.warning(f"Không vẽ được đồ thị: `{plot_err}`")

            # Buộc MathJax render lại sau khi thêm nội dung mới
            trigger_mathjax()

    # ==================== TAB 2 — GIA SƯ SOCRATIC ====================
    with tab2:
        str_app.markdown("<br>", unsafe_allow_html=True)

        if "socratic_messages" not in str_app.session_state:
            str_app.session_state.socratic_messages = []
        if "socratic_uploader_key" not in str_app.session_state:
            str_app.session_state.socratic_uploader_key = 0
        if "analytics_logs" not in str_app.session_state:
            str_app.session_state.analytics_logs = []

        grade_num = grade.replace("Lớp ", "").strip()

        try:
            sheet_webhook_url = str_app.secrets.get("SHEET_WEBHOOK", "")
        except Exception:
            sheet_webhook_url = ""

        str_app.subheader(f"💬 Gia Sư Socratic môn: {subject} - Lớp {grade_num}")
        str_app.caption("Chụp ảnh bài làm của em gửi lên đây. Gia Sư AI sẽ chẩn đoán lỗi sai và gợi mở phương pháp để em tự hoàn thiện!")

        if str_app.button("🔄 Làm bài mới / Xóa đối thoại cũ"):
            str_app.session_state.socratic_messages = []
            str_app.session_state.socratic_uploader_key += 1
            str_app.rerun()

        uploaded_file = str_app.file_uploader(
            "📸 Tải ảnh bài làm của em (JPG, PNG)",
            type=["jpg", "png", "jpeg"],
            key=f"socratic_uploader_{str_app.session_state.socratic_uploader_key}"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            str_app.image(image, caption="Bài làm của em", use_container_width=True)

            if str_app.button("🚀 Bắt đầu nhận xét bài làm"):
                if not api_key_to_use:
                    str_app.error("Chưa phát hiện Mã Kết Nối! Vui lòng dán API Key ở thanh bên trái.")
                else:
                    with str_app.spinner("Gia Sư AI đang đối chiếu chuẩn kiến thức GDPT 2018 (SGK KNTT)..."):
                        try:
                            sys_prompt = f"""Bạn là 'Gia Sư AI' trường THPT Tân Hiệp.
Đối tượng: Học sinh Lớp {grade_num}, môn {subject} (SGK Kết nối tri thức).
Phương pháp: Vấn đáp Socratic.
NGUYÊN TẮC: Tuyệt đối không giải hộ, khen ngợi bước đúng, đặt câu hỏi gợi mở bước sai.
Cuối bài chèn khối: <DIAGNOSTIC>{{"topic":"...","error_type":"...","evaluation":"..."}}</DIAGNOSTIC>"""

                            full_res = call_gemini_with_fallback(
                                [f"Nhận xét bài làm môn {subject} Lớp {grade_num}:", image],
                                api_key=api_key_to_use,
                                system_instruction=sys_prompt
                            )

                            if not full_res:
                                str_app.error("Không thể kết nối AI. Vui lòng thử lại sau.")
                            else:
                                student_fb = full_res.split("<DIAGNOSTIC>")[0].strip() if "<DIAGNOSTIC>" in full_res else full_res

                                if "<DIAGNOSTIC>" in full_res:
                                    try:
                                        diag_raw = full_res.split("<DIAGNOSTIC>")[1].split("</DIAGNOSTIC>")[0].strip()
                                        diag = json.loads(diag_raw)
                                        entry = {
                                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            "grade": grade,
                                            "subject": subject,
                                            "topic": diag.get("topic", "Chung"),
                                            "error_type": diag.get("error_type", "Chưa rõ"),
                                            "evaluation": diag.get("evaluation", "")
                                        }
                                        str_app.session_state.analytics_logs.append(entry)

                                        if sheet_webhook_url:
                                            try:
                                                requests.post(sheet_webhook_url, json=entry, timeout=5)
                                            except Exception:
                                                pass
                                    except Exception as parse_err:
                                        str_app.warning(f"Không parse được DIAGNOSTIC: {parse_err}")

                                str_app.session_state.socratic_messages = [
                                    {"role": "user", "content": "*(Em đã nộp ảnh bài làm)*"},
                                    {"role": "assistant", "content": student_fb}
                                ]
                                str_app.rerun()
                        except Exception as e:
                            str_app.error(f"Lỗi: {e}")

        for m in str_app.session_state.get("socratic_messages", []):
            with str_app.chat_message(m["role"]):
                str_app.markdown(m["content"])

        if len(str_app.session_state.get("socratic_messages", [])) > 0:
            if q := str_app.chat_input("Em muốn hỏi thêm điều gì về bài làm này?...", key="socratic_chat_input"):
                str_app.session_state.socratic_messages.append({"role": "user", "content": q})
                with str_app.chat_message("user"):
                    str_app.markdown(q)
                with str_app.chat_message("assistant"):
                    try:
                        history = str_app.session_state.socratic_messages[-4:]
                        dialogue_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
                        prompt_chat = f"Ngữ cảnh hội thoại trước:\n{dialogue_context}\n\nHọc sinh hỏi tiếp: {q}\nHãy tiếp tục phương pháp gợi mở Socratic, giải thích bình dân học vụ, không giải hộ:"

                        rep = call_gemini_with_fallback(prompt_chat, api_key=api_key_to_use)
                        rep_clean = rep.split("<DIAGNOSTIC>")[0].strip() if "<DIAGNOSTIC>" in rep else rep

                        if not rep_clean:
                            str_app.error("Không nhận được phản hồi. Vui lòng thử lại.")
                        else:
                            str_app.markdown(rep_clean)
                            str_app.session_state.socratic_messages.append({"role": "assistant", "content": rep_clean})
                    except Exception as e:
                        str_app.error(f"Lỗi phản hồi: {e}")
# ============================================================
# 8. KHỞI CHẠY ỨNG DỤNG CHÍNH
# ============================================================
def main():
    setup_page_config()
    grade, subject, api_key_to_use = render_sidebar()
    render_main_interface(grade, subject, api_key_to_use)

if __name__ == "__main__":
    main()

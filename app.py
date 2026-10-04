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
# CẤU HÌNH TOÀN CỤC MATPLOTLIB — HÌNH ĐẸP, MỊN, SẮC NÉT
# ============================================================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 130,
    "savefig.dpi": 130,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
    "lines.linewidth": 2,
    "lines.antialiased": True,
    "axes.linewidth": 1.2,
    "axes.unicode_minus": False,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.4,
    "figure.autolayout": False,
})

# ============================================================
# 0. PHÂN LOẠI MÔN HỌC THEO HÌNH THỨC ĐÁNH GIÁ
# ============================================================
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
        
        /* Khung nội dung cốt lõi */
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

        /* ===== DÀN ĐỀU 5 TAB ===== */
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            width: 100% !important;
            gap: 6px !important;
            justify-content: space-between !important;
        }
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
        .stTabs [data-baseweb="tab-list"] > button:hover {
            background-color: rgba(13, 110, 253, 0.08) !important;
        }
        .stTabs [data-baseweb="tab-list"] > button[aria-selected="true"] {
            background-color: rgba(13, 110, 253, 0.12) !important;
        }

        /* ===== GIẢM FONT TRONG KHUNG CÂU HỎI / ĐỀ BÀI ===== */
        [data-testid="stVerticalBlockBorderWrapper"] p {
            font-size: 0.92rem !important;
            line-height: 1.55 !important;
            margin-bottom: 6px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] h3 {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            margin-bottom: 10px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] .stRadio label,
        [data-testid="stVerticalBlockBorderWrapper"] .stExpander summary {
            font-size: 0.9rem !important;
        }
        </style>
        
        <!-- Thư viện MathJax -->
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
# 3. GỌI API GEMINI
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
# 4. XÂY DỰNG PROMPT BÀI HỌC
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
    template = """Bạn là chuyên gia mô phỏng thí nghiệm giáo dục cho học sinh __GRADE__ môn __SUBJECT__ theo chương trình GDPT 2018 bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

YÊU CẦU CỦA HỌC SINH: __LAB_REQUEST__

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung bằng TIẾNG VIỆT.
2. LaTeX đặt trong cặp dấu đô la cho mọi công thức.
3. KHÔNG DÙNG DẤU #.
4. Code Python vẽ đồ thị PHẢI ngắn gọn, tối ưu.

=== ⚠️ CẢNH BÁO QUAN TRỌNG VỀ PLOTLY (BẮT BUỘC ĐỌC) ===
Plotly KHÁC matplotlib. Các lỗi thường gặp PHẢI TRÁNH:

1. Font bold: DÙNG `weight='bold'` (KHÔNG dùng `bold=True`)
   ĐÚNG: font=dict(size=14, color='#333', weight='bold')
   SAI:  font=dict(size=14, color='#333', bold=True)

2. Title: DÙNG `title=dict(text='...', font=dict(...))` (KHÔNG dùng `title='...', title_font=dict(...)`)
   ĐÚNG: title=dict(text='Đồ thị', x=0.5, font=dict(size=14, weight='bold'))
   SAI:  title='Đồ thị', title_font=dict(bold=True)

3. Marker: DÙNG `marker=dict(size=12, color='#d62728')` (KHÔNG dùng `marker_size=12`)
   ĐÚNG: marker=dict(size=12, color='#d62728', line=dict(color='white', width=1.5))
   SAI:  marker_size=12, marker_color='#d62728'

4. Line: DÙNG `line=dict(color='#1f4e9c', width=3)` (KHÔNG dùng `line_color`, `line_width`)

5. Annotation: DÙNG `showarrow=False` (KHÔNG dùng `show_arrow=False`, `arrow=False`)

6. KHÔNG dùng `axref="paper"` hoặc `ayref="paper"` cho mũi tên annotation.

=== CẤU TRÚC ĐẦU RA BẮT BUỘC ===

1. MÔ TẢ THÍ NGHIỆM / HIỆN TƯỢNG
[Mô tả chi tiết.]

2. NGUYÊN LÝ / PHƯƠNG TRÌNH / HIỆN TƯỢNG XẢY RA
[Giải thích bản chất, dùng LaTeX đầy đủ.]

3. KẾT QUẢ / QUAN SÁT ĐƯỢC
[Mô tả kết quả, kết luận.]

4. MÃ VẼ ĐỒ THỊ (nếu không cần, ghi "Không cần vẽ đồ thị")

QUY TẮC CHỌN LOẠI ĐỒ THỊ:
- 2D hàm số → thẻ <PLOT_2D>...</PLOT_2D> (PLOTLY)
- 3D hình học → thẻ <PLOT_3D>...</PLOT_3D> (PLOTLY)

=== QUY TẮC KHAI BÁO HỆ SỐ (BẮT BUỘC) ===
Với hàm số y = ax² + bx + c (hoặc bậc 3, 4):
- Khai báo hệ số ở ĐẦU CODE (TRƯỚC cả import), MỖI HỆ SỐ MỘT DÒNG RIÊNG
- Định dạng CHÍNH XÁC: `a = 1` (có khoảng trắng quanh dấu =)

Ví dụ ĐÚNG:
a = 1
b = -4
c = 3
import plotly.graph_objects as go
import numpy as np

Ví dụ SAI: `coeffs = [1, -4, 3]` HOẶC `a, b, c = 1, -4, 3` HOẶC `a=1`

=== ⚠️ QUY TẮC VỀ RANGE VÀ MŨI TÊN TRỤC ===
1. KHÔNG dùng `axref="paper"` hoặc `ayref="paper"` cho annotation mũi tên.
2. PHẢI set range cho CẢ xaxis và yaxis. Tính y_range từ dữ liệu y:
   y_pad = (max(y) - min(y)) * 0.1 + 1
   y_range = [min(y) - y_pad, max(y) + y_pad]
3. Mũi tên trục đặt ở cuối data range (không dùng paper coords).

=== ⚠️ QUY TẮC ĐẶT TÊN ĐỒ THỊ VÀ TIỆM CẬN (BẮT BUỘC) ===

A) TÊN ĐỒ THỊ — Đặt ở GÓC DƯỚI PHẢI (vùng paper 0.98, 0.02):
   fig.add_annotation(
       x=0.98, y=0.02, xref="paper", yref="paper",
       text="<công thức tổng quát>",
       showarrow=False,
       xanchor='right', yanchor='bottom',
       font=dict(size=13, color='#1f4e9c'),
       bgcolor='rgba(255,255,255,0.85)',
       bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6
   )

   Quy tắc viết tên:
   - Hàm bậc 2: "y = ax² + bx + c"
   - Hàm bậc 3: "y = ax³ + bx² + cx + d"
   - Hàm phân thức: "y = (ax + b)/(cx + d)"
   → LUÔN ghi dạng TỔNG QUÁT (có a, b, c), KHÔNG ghi số cụ thể.

B) TIỆM CẬN — Mỗi tiệm cận phải có NHÃN TÊN:
   - Tiệm cận ĐỨNG x = a: đường dọc dash, nhãn "x = a" đặt gần đường
   - Tiệm cận NGANG y = a: đường ngang dash, nhãn "y = a" ở đầu phải
   - Tiệm cận XIÊN y = ax + b: đường chéo dash, nhãn "y = ax + b" ở đầu phải

=== STYLE 2D PLOTLY (BẮT BUỘC) ===
- Lưới mịn màu #e0e0e0
- Đường cong xanh đậm #1f4e9c, width 3
- Nền trắng (plot_bgcolor='white')
- Điểm đặc biệt: chấm tròn + nhãn tọa độ

=== MẪU 2D PLOTLY CHUẨN ===
<PLOT_2D>
a = 1
b = -4
c = 3
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

x = np.linspace(-1.5, 5.5, 400)
y = a*x**2 + b*x + c
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# Điểm cực trị
if a != 0:
    vx = -b / (2*a)
    vy = a*vx**2 + b*vx + c
    fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
        marker=dict(color='#d62728', size=12, line=dict(color='white', width=1.5)),
        showlegend=False,
        hovertemplate='Đỉnh I(' + str(round(vx,2)) + '; ' + str(round(vy,2)) + ')<extra></extra>'))
    fig.add_annotation(x=vx, y=vy,
        text="I(" + str(round(vx,2)) + "; " + str(round(vy,2)) + ")",
        showarrow=False, yshift=-25, font=dict(color='#d62728', size=12, weight='bold'))

# Giao Oy
fig.add_trace(go.Scatter(x=[0], y=[c], mode='markers',
    marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=1.5)),
    showlegend=False,
    hovertemplate='(0; ' + str(round(c,2)) + ')<extra></extra>'))
fig.add_annotation(x=0, y=c,
    text="(0; " + str(round(c,2)) + ")",
    showarrow=False, xshift=35, font=dict(color='#2ca02c', size=12, weight='bold'))

# Giao Ox
if a != 0:
    roots = np.roots([a, b, c])
    for r in roots:
        if abs(r.imag) < 1e-6:
            xr = r.real
            fig.add_trace(go.Scatter(x=[xr], y=[0], mode='markers',
                marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=1.5)),
                showlegend=False,
                hovertemplate='(' + str(round(xr,2)) + '; 0)<extra></extra>'))
            fig.add_annotation(x=xr, y=0,
                text="(" + str(round(xr,2)) + "; 0)",
                showarrow=False, yshift=20, font=dict(color='#2ca02c', size=11, weight='bold'))

# TÍNH RANGE ĐỘNG
x_range = [-1.8, 6.8]
y_min_d = float(np.min(y))
y_max_d = float(np.max(y))
y_pad = (y_max_d - y_min_d) * 0.1 + 1
y_range = [y_min_d - y_pad, y_max_d + y_pad]

# MŨI TÊN TRỤC
fig.add_annotation(
    x=x_range[1], y=0,
    ax=x_range[1] - 0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8,
    arrowwidth=2.5, arrowcolor='#333'
)
fig.add_annotation(
    x=0, y=y_range[1],
    ax=0, ay=y_range[1] * 0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8,
    arrowwidth=2.5, arrowcolor='#333'
)

# Nhãn O, x, y
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

# TÊN ĐỒ THỊ Ở GÓC DƯỚI PHẢI
fig.add_annotation(
    x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = ax² + bx + c",
    showarrow=False,
    xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6
)

fig.update_layout(
    title=dict(text='Đồ thị hàm số bậc hai y = ax² + bx + c', x=0.5,
        font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
        showline=False, ticks='outside', tickfont=dict(size=11)),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
        showline=False, ticks='outside', tickfont=dict(size=11)),
    plot_bgcolor='white',
    height=520,
    margin=dict(l=20, r=20, t=50, b=30)
)
</PLOT_2D>

=== MẪU HÀM PHÂN THỨC CÓ TIỆM CẬN ===
<PLOT_2D>
a = 1
b = 1
c = 1
d = 1
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

x = np.linspace(-5, 5, 1000)
x = x[np.abs(c*x + d) > 0.01]
y = (a*x + b) / (c*x + d)

fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-6, 6]
y_range = [-10, 10]

# TIỆM CẬN ĐỨNG x = -d/c
if c != 0:
    x_tcd = -d / c
    fig.add_trace(go.Scatter(x=[x_tcd, x_tcd], y=y_range,
        mode='lines', line=dict(color='#999', width=1.5, dash='dash'),
        showlegend=False, hoverinfo='skip'))
    fig.add_annotation(x=x_tcd, y=y_range[1]*0.85,
        text="x = " + str(round(x_tcd, 2)),
        showarrow=False, xshift=8, font=dict(color='#666', size=12))

# TIỆM CẬN NGANG y = a/c
if c != 0:
    y_tcn = a / c
    fig.add_trace(go.Scatter(x=x_range, y=[y_tcn, y_tcn],
        mode='lines', line=dict(color='#999', width=1.5, dash='dash'),
        showlegend=False, hoverinfo='skip'))
    fig.add_annotation(x=x_range[1]*0.95, y=y_tcn,
        text="y = " + str(round(y_tcn, 2)),
        showarrow=False, yshift=8, xanchor='right', font=dict(color='#666', size=12))

# Mũi tên trục
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

# Nhãn O, x, y
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

# TÊN ĐỒ THỊ GÓC DƯỚI PHẢI
fig.add_annotation(
    x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = (ax + b)/(cx + d)",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6
)

fig.update_layout(
    title=dict(text='Đồ thị hàm phân thức', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30)
)
</PLOT_2D>

=== MẪU 3D PLOTLY ===
<PLOT_3D>
import plotly.graph_objects as go

fig = go.Figure()
S, A, B, C = [0,0,4], [3,0,0], [0,4,0], [-2,-2,0]

for p1, p2 in [(A,B),(B,C),(C,A),(S,A),(S,B)]:
    fig.add_trace(go.Scatter3d(x=[p1[0],p2[0]], y=[p1[1],p2[1]], z=[p1[2],p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=6), showlegend=False))

for p1, p2 in [(S,C)]:
    fig.add_trace(go.Scatter3d(x=[p1[0],p2[0]], y=[p1[1],p2[1]], z=[p1[2],p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=4, dash='dash'), showlegend=False))

fig.add_trace(go.Mesh3d(x=[A[0],B[0],C[0]], y=[A[1],B[1],C[1]], z=[A[2],B[2],C[2]],
    color='lightblue', opacity=0.3, showlegend=False, hoverinfo='skip'))

for name, p in [('S',S),('A',A),('B',B),('C',C)]:
    fig.add_trace(go.Scatter3d(x=[p[0]], y=[p[1]], z=[p[2]], mode='text',
        text=[name], textfont=dict(size=14, color='black'), showlegend=False))

fig.update_layout(
    title='Hình chóp S.ABC',
    scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube', camera=dict(eye=dict(x=1.25, y=1.25, z=1.25))),
    margin=dict(l=0, r=0, t=40, b=0), height=520)
</PLOT_3D>

LƯU Ý CUỐI:
- 2D: dùng PLOTLY
- 2D: KHÔNG dùng `bold=True` — DÙNG `weight='bold'`
- 2D: KHÔNG dùng `title_font=`, `marker_size=`, `line_color=`, `show_arrow=`
- 2D: BẮT BUỘC đặt TÊN ĐỒ THỊ ở góc dưới phải (paper 0.98, 0.02)
- 2D: Mỗi tiệm cận PHẢI có nhãn tên
- KHÔNG gọi fig.show(), KHÔNG savefig"""

    return template.replace("__LAB_REQUEST__", lab_request).replace("__SUBJECT__", subject).replace("__GRADE__", grade)

# ============================================================
# 4B2. TRÍCH XUẤT HỆ SỐ TỪ CODE AI SINH
# ============================================================
def extract_coefficients(code_str: str) -> dict:
    """
    Trích xuất các hệ số dạng 'a = 1.5' ở đầu code.
    Chỉ lấy dòng khớp chính xác: tên_biến = giá_trị_số (có thể có comment cuối).
    Trả về dict {tên: giá_trị}.
    """
    coeffs = {}
    pattern = re.compile(
        r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:#.*)?$"
    )
    for line in code_str.split("\n"):
        m = pattern.match(line.strip())
        if m:
            name = m.group(1)
            # Bỏ qua các biến đặc biệt không phải hệ số
            if name in ("dpi", "height", "width", "size", "n"):
                continue
            try:
                coeffs[name] = float(m.group(2))
            except ValueError:
                continue
    return coeffs

# ============================================================
# 4B3. THAY THẾ HỆ SỐ TRONG CODE
# ============================================================
def substitute_coefficients(code_str: str, coeff_values: dict) -> str:
    """Thay giá trị hệ số trong code bằng giá trị mới từ slider."""
    for name, value in coeff_values.items():
        # Format gọn: bỏ .0 nếu là số nguyên
        val_str = str(int(value)) if value == int(value) else str(round(value, 4))
        pattern = re.compile(
            rf"^(\s*{re.escape(name)}\s*=\s*)(-?\d+(?:\.\d+)?)(\s*(?:#.*)?)$",
            re.MULTILINE
        )
        code_str = pattern.sub(rf"\g<1>{val_str}\g<3>", code_str)
    return code_str

# ============================================================
# 4B4. FORMAT CÔNG THỨC ĐẸP — BỎ NGOẶC, GỘP DẤU, BỎ SỐ 1
# ============================================================
def format_formula(user_coeffs: dict, plot_code: str = "") -> str:
    """Trả về chuỗi công thức đẹp: bỏ ngoặc thừa, gộp dấu, bỏ số 1 trước biến."""

    def fmt_num(v, suffix=""):
        v_abs = abs(v)
        if v_abs == 1 and suffix:
            return suffix
        if v_abs == int(v_abs):
            return f"{int(v_abs)}{suffix}"
        return f"{v_abs:.1f}{suffix}"

    is_fractional = (
        "d" in user_coeffs and "e" in user_coeffs
        and "/" in plot_code
    )

    if is_fractional:
        num_parts = []
        for name, suffix in [("a", "x²"), ("b", "x"), ("c", "")]:
            if name not in user_coeffs:
                continue
            v = user_coeffs[name]
            v_str = fmt_num(v, suffix)
            if not num_parts:
                num_parts.append(f"-{v_str}" if v < 0 else v_str)
            else:
                num_parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")

        den_parts = []
        for name, suffix in [("d", "x"), ("e", "")]:
            if name not in user_coeffs:
                continue
            v = user_coeffs[name]
            v_str = fmt_num(v, suffix)
            if not den_parts:
                den_parts.append(f"-{v_str}" if v < 0 else v_str)
            else:
                den_parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")

        num_str = " ".join(num_parts) if num_parts else "0"
        den_str = " ".join(den_parts) if den_parts else "1"
        return f"y = ({num_str}) / ({den_str})"

    else:
        if "e" in user_coeffs:
            order = [("a", "x⁴"), ("b", "x³"), ("c", "x²"), ("d", "x"), ("e", "")]
        elif "d" in user_coeffs:
            order = [("a", "x³"), ("b", "x²"), ("c", "x"), ("d", "")]
        else:
            order = [("a", "x²"), ("b", "x"), ("c", "")]

        parts = []
        for name, suffix in order:
            if name not in user_coeffs:
                continue
            v = user_coeffs[name]
            v_str = fmt_num(v, suffix)
            if not parts:
                parts.append(f"-{v_str}" if v < 0 else v_str)
            else:
                parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")

        if not parts:
            return "y = 0"
        return "y = " + " ".join(parts)

# ============================================================
# 4C. CHẠY CODE VẼ ĐỒ THỊ AN TOÀN
# ============================================================
def run_plot_code(code_str: str):
    """
    Chạy code vẽ đồ thị an toàn với validation 3 lớp.
    Trả về (kind, data):
      - ("png", path) nếu matplotlib
      - ("plotly", fig) nếu plotly
      - (None, None) nếu lỗi
    """
    import os

    plot_path = "/tmp/lab_plot.png"
    if os.path.exists(plot_path):
        try:
            os.remove(plot_path)
        except Exception:
            pass

    # ---- LỚP 1: Chặn từ khóa nguy hiểm ----
    forbidden = [
        "os.system", "subprocess", "shutil", "socket",
        "open(", "eval(", "compile(",
        "requests.", "urllib", "pathlib",
    ]
    code_lower = code_str.lower()
    for kw in forbidden:
        if kw.lower() in code_lower:
            raise ValueError(f"Code chứa từ khóa không được phép: {kw}")

    # ---- LỚP 2: Tự thêm savefig nếu AI quên ----
    has_savefig = "savefig" in code_lower
    has_plotly = "plotly" in code_lower or "go.figure" in code_lower

    if not has_savefig and not has_plotly:
        code_str = code_str.rstrip() + '\nfig.savefig("/tmp/lab_plot.png", dpi=130, bbox_inches="tight")'

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

        # Ưu tiên Plotly
        fig_var = namespace.get("fig")
        if fig_var is not None and hasattr(fig_var, "to_plotly_json"):
            return ("plotly", fig_var)

        # Fallback matplotlib: nếu chưa save, tự save
        if not os.path.exists(plot_path):
            try:
                plt.savefig(plot_path, dpi=130, bbox_inches="tight", pad_inches=0.15)
            except Exception:
                pass

        # ---- LỚP 3: Verify file output ----
        if os.path.exists(plot_path) and os.path.getsize(plot_path) > 1000:
            return ("png", plot_path)
        return (None, None)
    finally:
        plt.close('all')

# ============================================================
# 4D. TRIGGER RENDER LẠI MATHJAX
# ============================================================
def trigger_mathjax():
    """Buộc MathJax typeset lại nội dung."""
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
# 7. GIAO DIỆN CHÍNH VÀ LUỒNG XỬ LÝ
# ============================================================
                            # ===== CÔNG THỨC ĐỘNG =====
                            formula_parts = []
                            if "a" in user_coeffs:
                                formula_parts.append(f"{user_coeffs['a']:.1f}x²")
                            if "b" in user_coeffs:
                                formula_parts.append(f"({user_coeffs['b']:.1f})x")
                            if "c" in user_coeffs:
                                formula_parts.append(f"({user_coeffs['c']:.1f})")

                            if formula_parts:
                                formula_text = "y = " + " + ".join(formula_parts).replace("+ (-", "- (").replace("+ (-", "- (")
                                str_app.markdown(
                                    f"<div style='background: linear-gradient(135deg, #4a90e2, #357abd); color: white; "
                                    f"padding: 14px 18px; border-radius: 10px; font-size: 1.05rem; "
                                    f"font-weight: 600; margin: 20px 0; text-align: center;'>"
                                    f"<i>{formula_text}</i></div>",
                                    unsafe_allow_html=True
                                )

# ============================================================
# 8. KHỞI CHẠY ỨNG DỤNG CHÍNH
# ============================================================
def main():
    setup_page_config()
    grade, subject, api_key_to_use = render_sidebar()
    render_main_interface(grade, subject, api_key_to_use)

if __name__ == "__main__":
    main()

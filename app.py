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

QUY TẮC CHUNG:
1. TOÀN BỘ nội dung bằng TIẾNG VIỆT.
2. LaTeX đặt trong cặp dấu đô la cho mọi công thức.
3. KHÔNG DÙNG DẤU #.
4. Code Python vẽ đồ thị PHẢI ngắn gọn, tối ưu.

=== ⚠️ CẢNH BÁO PLOTLY ===
1. Font bold: DÙNG `weight='bold'` (KHÔNG `bold=True`)
2. Title: `title=dict(text='...', font=dict(...))`
3. Marker: `marker=dict(size=12, color='#d62728')`
4. Line: `line=dict(color='#1f4e9c', width=3)`
5. Annotation: `showarrow=False`
6. KHÔNG dùng `axref="paper"` cho MŨI TÊN annotation.

=== 📋 CẤU TRÚC ĐẦU RA ===
1. MÔ TẢ THÍ NGHIỆM / HIỆN TƯỢNG
2. NGUYÊN LÝ / PHƯƠNG TRÌNH
3. KẾT QUẢ / QUAN SÁT ĐƯỢC
4. MÃ VẼ ĐỒ THỊ (bọc trong <PLOT_2D>...</PLOT_2D> hoặc <PLOT_3D>...</PLOT_3D>)

=== 🎯 QUY TẮC CHỌN TEMPLATE ===
Đọc yêu cầu học sinh, chọn ĐÚNG 1 trong các template sau:
- Hàm y = ax² + bx + c → TEMPLATE 1
- Hàm y = ax³ + bx² + cx + d → TEMPLATE 1 (biến thể bậc 3)
- Hàm y = (ax+b)/(cx+d) hoặc (ax²+bx+c)/(dx+e) → TEMPLATE 2
- Hàm y = sin/cos/tan/cot → TEMPLATE 3
- Hàm y = a^x, e^x, ln(x), log_a(x) → TEMPLATE 4
- Hàm y = √(ax+b), y = x^n → TEMPLATE 5
- Đường tròn, elip, hyperbol, parabol ngang → TEMPLATE 6
- Hình học phẳng (tam giác, tứ giác, đa giác) → TEMPLATE 7
- Hình học 3D (chóp, lăng trụ, hộp, cầu, nón, trụ) → TEMPLATE 8

=== ⚠️ QUY TẮC KHAI BÁO HỆ SỐ (BẮT BUỘC VỚI 2D) ===
- Khai báo hệ số ở ĐẦU CODE (TRƯỚC import), MỖI HỆ SỐ 1 DÒNG
- Format: `a = 1` (có khoảng trắng quanh dấu =)
- KHÔNG dùng list `coeffs = [...]`, KHÔNG gộp `a, b, c = 1, 2, 3`

=== ⚠️ QUY TẮC CỰC TRỊ (CHỈ VỚI ĐA THỨC) ===
- CHỈ vẽ cực trị khi hàm là ĐA THỨC (bậc 2, 3, 4)
- KHÔNG vẽ cực trị cho hàm phân thức, lượng giác, mũ, log
- Parabol: LUÔN nhãn "I(x; y)" — KHÔNG ghi "Cực đại"/"Cực tiểu"
- KHÔNG nhầm giao Oy (xanh lá) với cực trị (đỏ)

=== ⚠️ QUY TẮC NHÃN ===
MỌI nhãn điểm PHẢI CÓ:
- `bgcolor='rgba(255,255,255,0.9)'`
- `borderwidth=1, borderpad=4`
- Khoảng cách tối thiểu 35px

Màu mặc định:
- Đường cong: #1f4e9c (xanh đậm)
- Điểm cực trị: #d62728 (đỏ)
- Giao điểm: #2ca02c (xanh lá)
- Tiệm cận: #999 (xám đứt)

=== 📌 TEMPLATE 1 — HÀM ĐA THỨC ===
<PLOT_2D>
a = 1
b = -4
c = 3
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

x = np.linspace(-2, 6, 1000)
y = a*x**2 + b*x + c
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# ĐIỂM CỰC TRỊ
if a != 0:
    vx = -b / (2*a)
    vy = a*vx**2 + b*vx + c
    fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
        marker=dict(color='#d62728', size=12, line=dict(color='white', width=2)),
        showlegend=False))
    fig.add_annotation(x=vx, y=vy,
        text="I(" + str(round(vx,2)) + "; " + str(round(vy,2)) + ")",
        showarrow=False, xshift=20, yshift=-40,
        xanchor='left', yanchor='top',
        font=dict(color='#d62728', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='#d62728', borderwidth=1, borderpad=4)

# GIAO Oy
fig.add_trace(go.Scatter(x=[0], y=[c], mode='markers',
    marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
    showlegend=False))
fig.add_annotation(x=0, y=c,
    text="(0; " + str(round(c,2)) + ")",
    showarrow=False, xshift=50, yshift=5,
    xanchor='left', yanchor='middle',
    font=dict(color='#2ca02c', size=12, weight='bold'),
    bgcolor='rgba(255,255,255,0.9)',
    bordercolor='#2ca02c', borderwidth=1, borderpad=4)

# GIAO Ox
if a != 0:
    roots = np.roots([a, b, c])
    for r in roots:
        if abs(r.imag) < 1e-6:
            xr = r.real
            fig.add_trace(go.Scatter(x=[xr], y=[0], mode='markers',
                marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
                showlegend=False))
            fig.add_annotation(x=xr, y=0,
                text="(" + str(round(xr,2)) + "; 0)",
                showarrow=False, yshift=35,
                xanchor='center', yanchor='bottom',
                font=dict(color='#2ca02c', size=11, weight='bold'),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#2ca02c', borderwidth=1, borderpad=4)

# TÍNH RANGE
x_range = [-2.5, 6.5]
y_min_d = float(np.min(y))
y_max_d = float(np.max(y))
y_pad = (y_max_d - y_min_d) * 0.1 + 1
y_range = [y_min_d - y_pad, y_max_d + y_pad]

# MŨI TÊN TRỤC
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

# NHÃN O, x, y
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

# TÊN CÔNG THỨC GÓC DƯỚI PHẢI
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = ax² + bx + c",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đồ thị hàm số bậc hai', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

=== 📌 TEMPLATE 2 — HÀM PHÂN THỨC ===
<PLOT_2D>
a = 1
b = 1
c = 1
d = 1
e = 1
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

x = np.linspace(-20, 20, 5000)
y = (a*x**2 + b*x + c) / (d*x + e)
mask = np.abs(d*x + e) < 0.05
y[mask] = np.nan

fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3),
    showlegend=False, hoverinfo='skip', connectgaps=False))

x_range = [-10, 10]
y_range = [-30, 30]

# GIAO Oy
if e != 0:
    y_giao_oy = c / e
    fig.add_trace(go.Scatter(x=[0], y=[y_giao_oy], mode='markers',
        marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
        showlegend=False))
    fig.add_annotation(x=0, y=y_giao_oy,
        text="(0; " + str(round(y_giao_oy, 2)) + ")",
        showarrow=False, xshift=50, yshift=5,
        xanchor='left', yanchor='middle',
        font=dict(color='#2ca02c', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='#2ca02c', borderwidth=1, borderpad=4)

# GIAO Ox
if a != 0:
    roots = np.roots([a, b, c])
    for r in roots:
        if abs(r.imag) < 1e-6:
            xr = r.real
            if d != 0 and abs(xr - (-e/d)) < 0.1:
                continue
            fig.add_trace(go.Scatter(x=[xr], y=[0], mode='markers',
                marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
                showlegend=False))
            fig.add_annotation(x=xr, y=0,
                text="(" + str(round(xr,2)) + "; 0)",
                showarrow=False, yshift=35,
                xanchor='center', yanchor='bottom',
                font=dict(color='#2ca02c', size=11, weight='bold'),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#2ca02c', borderwidth=1, borderpad=4)

# TIỆM CẬN ĐỨNG x = -e/d
if d != 0:
    x_tcd = -e / d
    fig.add_shape(type="line", x0=x_tcd, x1=x_tcd, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="#999", width=1.5, dash="dash"))
    x_tcd_str = str(int(x_tcd)) if x_tcd == int(x_tcd) else str(round(x_tcd, 2))
    fig.add_annotation(x=x_tcd, y=0.85, xref="x", yref="paper",
        text="x = " + x_tcd_str, showarrow=False, xshift=15,
        xanchor='left', yanchor='middle',
        font=dict(color='#666', size=12),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#999',
        borderwidth=1, borderpad=4)

# TIỆM CẬN XIÊN y = (a/d)x + (b/d - ae/d²)
if d != 0:
    m = a / d
    n = (b*d - a*e) / (d*d)
    fig.add_shape(type="line",
        x0=-1000, y0=m*(-1000) + n,
        x1=1000, y1=m*1000 + n,
        xref="x", yref="y",
        line=dict(color="#999", width=1.5, dash="dash"))
    m_part = "x" if m == 1 else ("-x" if m == -1 else ("" if m == 0 else str(int(m) if m == int(m) else round(m, 2)) + "x"))
    if n > 0:
        n_part = " + " + (str(int(n)) if n == int(n) else str(round(n, 2)))
    elif n < 0:
        n_abs = abs(n)
        n_part = " - " + (str(int(n_abs)) if n_abs == int(n_abs) else str(round(n_abs, 2)))
    else:
        n_part = ""
    fig.add_annotation(x=5, y=m*5 + n, xref="x", yref="y",
        text="y = " + m_part + n_part, showarrow=False, xshift=-10, yshift=15,
        xanchor='right', yanchor='bottom',
        font=dict(color='#666', size=12),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#999',
        borderwidth=1, borderpad=4)

# MŨI TÊN TRỤC
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

# NHÃN O, x, y
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

# TÊN CÔNG THỨC
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = (ax² + bx + c)/(dx + e)",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đồ thị hàm phân thức', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

=== 📌 TEMPLATE 3 — HÀM LƯỢNG GIÁC ===
<PLOT_2D>
a = 1
b = 1
c = 0
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

x = np.linspace(-2*np.pi, 2*np.pi, 2000)
y = a*np.sin(b*x + c)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-2*np.pi - 0.5, 2*np.pi + 0.5]
y_range = [-abs(a) - 0.5, abs(a) + 0.5]

# Đánh dấu chu kỳ T = 2π/|b|
if b != 0:
    T = 2*np.pi / abs(b)
    if abs(T) > 0.5:
        # Vẽ 2 đường đứt tại các điểm đặc biệt của sin
        fig.add_shape(type="line", x0=T, x1=T, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#999", width=1, dash="dot"))

# MŨI TÊN TRỤC
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

# NHÃN O, x, y + π labels
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

# Đánh dấu điểm đặc biệt của sin: -π, -π/2, π/2, π
for mark in [-np.pi, -np.pi/2, np.pi/2, np.pi]:
    fig.add_annotation(x=mark, y=0, text=str(round(mark/np.pi, 2)) + "π",
        showarrow=False, yshift=-20, font=dict(size=11, color='#666'))

# TÊN CÔNG THỨC
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = a·sin(bx + c)",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đồ thị hàm số lượng giác', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

Với tan, cot: PHẢI dùng mask tại tiệm cận (cos=0 cho tan, sin=0 cho cot):
y[np.abs(np.cos(b*x + c)) < 0.05] = np.nan
Và vẽ tiệm cận đứng bằng add_shape tại các điểm cos(bx+c)=0.

=== 📌 TEMPLATE 4 — HÀM MŨ VÀ LOGARIT ===
<PLOT_2D>
a = 2
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# HÀM MŨ y = a^x (a > 0)
x = np.linspace(-3, 3, 1000)
y = a**x
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-3.5, 3.5]
y_range = [-1, 12]

# TIỆM CẬN NGANG y = 0
fig.add_shape(type="line", x0=0, x1=1, y0=0, y1=0,
    xref="paper", yref="y",
    line=dict(color="#999", width=1.5, dash="dash"))
fig.add_annotation(x=0.9, y=0, xref="paper", yref="y",
    text="y = 0", showarrow=False, xshift=-10, yshift=15,
    xanchor='right', yanchor='bottom',
    font=dict(color='#666', size=12),
    bgcolor='rgba(255,255,255,0.9)', bordercolor='#999',
    borderwidth=1, borderpad=4)

# GIAO Oy
fig.add_trace(go.Scatter(x=[0], y=[1], mode='markers',
    marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
    showlegend=False))
fig.add_annotation(x=0, y=1,
    text="(0; 1)", showarrow=False, xshift=50, yshift=5,
    xanchor='left', yanchor='middle',
    font=dict(color='#2ca02c', size=12, weight='bold'),
    bgcolor='rgba(255,255,255,0.9)',
    bordercolor='#2ca02c', borderwidth=1, borderpad=4)

# MŨI TÊN TRỤC
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = a^x", showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đồ thị hàm số mũ', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

Với ln(x): chỉ vẽ x > 0, có tiệm cận đứng x = 0.
Với log_a(x): tương tự ln, chỉ vẽ x > 0.

=== 📌 TEMPLATE 5 — HÀM CĂN THỨC ===
<PLOT_2D>
a = 1
b = 0
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# Miền xác định: ax + b ≥ 0
if a > 0:
    x_min = -b/a
    x = np.linspace(x_min, x_min + 10, 1000)
elif a < 0:
    x_max = -b/a
    x = np.linspace(x_max - 10, x_max, 1000)
else:
    x = np.linspace(0, 10, 1000)

y = np.sqrt(np.maximum(a*x + b, 0))
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [float(np.min(x)) - 0.5, float(np.max(x)) + 0.5]
y_range = [-0.5, float(np.max(y)) + 1]

# GIAO Ox: điểm bắt đầu miền xác định
if a != 0:
    x0 = -b/a
    fig.add_trace(go.Scatter(x=[x0], y=[0], mode='markers',
        marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)),
        showlegend=False))
    fig.add_annotation(x=x0, y=0,
        text="(" + str(round(x0, 2)) + "; 0)", showarrow=False,
        xshift=-30, yshift=20,
        xanchor='right', yanchor='bottom',
        font=dict(color='#2ca02c', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='#2ca02c', borderwidth=1, borderpad=4)

fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="y = √(ax + b)", showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đồ thị hàm căn thức', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

=== 📌 TEMPLATE 6 — ĐƯỜNG TRÒN / ELIP / HYPERBOL ===
<PLOT_2D>
a = 3
b = 2
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# ĐƯỜNG TRÒN tâm O bán kính R = a: x = a·cos(t), y = a·sin(t)
t = np.linspace(0, 2*np.pi, 500)
x = a*np.cos(t)
y = a*np.sin(t)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# ELIP x = a·cos(t), y = b·sin(t)
# x = a*np.cos(t); y = b*np.sin(t)

x_range = [-a - 2, a + 2]
y_range = [-a - 2, a + 2]

# TÂM O — chấm đỏ
fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers',
    marker=dict(color='#d62728', size=12, line=dict(color='white', width=2)),
    showlegend=False))
fig.add_annotation(x=0, y=0, text="O", showarrow=False,
    xshift=-18, yshift=-18, font=dict(size=14, weight='bold', color='#333'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)

# MŨI TÊN TRỤC
fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="x² + y² = R²", showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Đường tròn tâm O bán kính R', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0',
        scaleanchor="y", scaleratio=1),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

Với ELIP: x = a·cos(t), y = b·sin(t).
Với HYPERBOL: x = ±a·cosh(t), y = b·sinh(t) (dùng 2 nhánh riêng).

=== 📌 TEMPLATE 7 — HÌNH HỌC PHẲNG ===
<PLOT_2D>
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# TAM GIÁC ABC với tọa độ đỉnh
A = (0, 0)
B = (4, 0)
C = (1, 3)

# Vẽ các cạnh
fig.add_trace(go.Scatter(x=[A[0], B[0], C[0], A[0]],
    y=[A[1], B[1], C[1], A[1]],
    mode='lines', line=dict(color='#1f4e9c', width=3),
    showlegend=False, hoverinfo='skip'))

# Tô màu nhẹ bên trong
fig.add_trace(go.Scatter(x=[A[0], B[0], C[0], A[0]],
    y=[A[1], B[1], C[1], A[1]],
    mode='none', fill='toself',
    fillcolor='rgba(31, 78, 156, 0.1)',
    showlegend=False, hoverinfo='skip'))

# Nhãn đỉnh
fig.add_annotation(x=A[0], y=A[1], text='A', showarrow=False,
    xshift=-18, yshift=-12, font=dict(size=16, weight='bold', color='#d62728'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)
fig.add_annotation(x=B[0], y=B[1], text='B', showarrow=False,
    xshift=12, yshift=-12, font=dict(size=16, weight='bold', color='#d62728'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)
fig.add_annotation(x=C[0], y=C[1], text='C', showarrow=False,
    xshift=-12, yshift=12, font=dict(size=16, weight='bold', color='#d62728'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)

x_range = [-1, 5]
y_range = [-1, 4]

fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2.5, arrowcolor='#333')

fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper",
    text="Tam giác ABC", showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Hình tam giác ABC', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0',
        scaleanchor="y", scaleratio=1),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
</PLOT_2D>

=== 📌 TEMPLATE 8 — HÌNH HỌC 3D ===
<PLOT_3D>
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# VÍ DỤ HÌNH CHÓP S.ABC
S = [0, 0, 4]
A = [3, 0, 0]
B = [0, 4, 0]
C = [-2, -2, 0]

# CẠNH NHÌN THẤY (nét liền)
visible_edges = [(A, B), (B, C), (C, A), (S, A), (S, B)]
for p1, p2 in visible_edges:
    fig.add_trace(go.Scatter3d(
        x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=6), showlegend=False))

# CẠNH KHUẤT (nét đứt)
hidden_edges = [(S, C)]
for p1, p2 in hidden_edges:
    fig.add_trace(go.Scatter3d(
        x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
        mode='lines', line=dict(color='#1f77b4', width=4, dash='dash'),
        showlegend=False))

# MẶT ĐÁY BÁN TRONG SUỐT
fig.add_trace(go.Mesh3d(
    x=[A[0], B[0], C[0]], y=[A[1], B[1], C[1]], z=[A[2], B[2], C[2]],
    color='lightblue', opacity=0.3, showlegend=False, hoverinfo='skip'))

# NHÃN ĐỈNH
for name, p in [('S', S), ('A', A), ('B', B), ('C', C)]:
    fig.add_trace(go.Scatter3d(
        x=[p[0]], y=[p[1]], z=[p[2]], mode='text',
        text=[name], textfont=dict(size=14, color='black', weight='bold'),
        showlegend=False))

# TRỤC Oxyz (nếu cần)
fig.add_trace(go.Scatter3d(x=[0, 5], y=[0, 0], z=[0, 0],
    mode='lines', line=dict(color='red', width=4), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 5], z=[0, 0],
    mode='lines', line=dict(color='green', width=4), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[0, 5],
    mode='lines', line=dict(color='blue', width=4), showlegend=False, hoverinfo='skip'))

fig.update_layout(
    title='Hình chóp S.ABC',
    scene=dict(
        xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
    margin=dict(l=0, r=0, t=40, b=0), height=520)
</PLOT_3D>

Các biến thể khác:
- HÌNH LĂNG TRỤ: 2 mặt đáy song song, cạnh bên thẳng đứng
- HÌNH HỘP: 8 đỉnh, 12 cạnh
- MẶT CẦU: dùng go.Surface với tham số (u, v) như hướng dẫn
- HÌNH NÓN: đỉnh trên + đường tròn đáy
- HÌNH TRỤ: 2 đường tròn song song + cạnh nối

LƯU Ý CUỐI:
- Chọn ĐÚNG 1 template phù hợp với yêu cầu
- KHÔNG gọi fig.show(), KHÔNG savefig
- CHỈ dùng: plotly.graph_objects, numpy, math
- 2D: PHẢI có đầy đủ mũi tên trục, nhãn O/x/y, đường cong, điểm đặc biệt, tên công thức
- 3D: PHẢI có nét liền cho cạnh nhìn thấy, nét đứt cho cạnh khuất, mặt bán trong suốt
- MỌI nhãn điểm PHẢI CÓ bgcolor='rgba(255,255,255,0.9)' + borderpad=4"""

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

    PLOTLY_CONFIG = {
        "scrollZoom": False,
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "pan2d", "select2d", "lasso2d", "zoom2d",
            "autoScale2d", "toggleSpikelines",
            "hoverCompareCartesian", "hoverClosestCartesian"
        ],
        "doubleClick": "reset",
    }

    # ===== KHỞI TẠO SESSION STATE MỘT LẦN =====
    if "cached_lesson_result" not in str_app.session_state:
        str_app.session_state.cached_lesson_result = None
    if "lab_result" not in str_app.session_state:
        str_app.session_state.lab_result = None
    if "lab_version" not in str_app.session_state:
        str_app.session_state.lab_version = 0
    if "lab_request_name" not in str_app.session_state:
        str_app.session_state.lab_request_name = ""

    def _fmt_num(v, suffix=""):
        v_abs = abs(v)
        if v_abs == 1 and suffix:
            return suffix
        if v_abs == int(v_abs):
            return f"{int(v_abs)}{suffix}"
        return f"{v_abs:.1f}{suffix}"

    def _format_formula(coeffs_dict, code_str=""):
        is_frac = ("d" in coeffs_dict and "e" in coeffs_dict and "/" in code_str)
        if is_frac:
            num_parts = []
            for name, suffix in [("a", "x²"), ("b", "x"), ("c", "")]:
                if name not in coeffs_dict:
                    continue
                v = coeffs_dict[name]
                v_str = _fmt_num(v, suffix)
                if not num_parts:
                    num_parts.append(f"-{v_str}" if v < 0 else v_str)
                else:
                    num_parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")
            den_parts = []
            for name, suffix in [("d", "x"), ("e", "")]:
                if name not in coeffs_dict:
                    continue
                v = coeffs_dict[name]
                v_str = _fmt_num(v, suffix)
                if not den_parts:
                    den_parts.append(f"-{v_str}" if v < 0 else v_str)
                else:
                    den_parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")
            num_str = " ".join(num_parts) if num_parts else "0"
            den_str = " ".join(den_parts) if den_parts else "1"
            return f"y = ({num_str}) / ({den_str})"
        else:
            if "e" in coeffs_dict:
                order = [("a", "x⁴"), ("b", "x³"), ("c", "x²"), ("d", "x"), ("e", "")]
            elif "d" in coeffs_dict:
                order = [("a", "x³"), ("b", "x²"), ("c", "x"), ("d", "")]
            else:
                order = [("a", "x²"), ("b", "x"), ("c", "")]
            parts = []
            for name, suffix in order:
                if name not in coeffs_dict:
                    continue
                v = coeffs_dict[name]
                v_str = _fmt_num(v, suffix)
                if not parts:
                    parts.append(f"-{v_str}" if v < 0 else v_str)
                else:
                    parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")
            if not parts:
                return "y = 0"
            return "y = " + " ".join(parts)

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
                        str_app.session_state.cached_lesson_result = final_text
                        str_app.session_state.cached_model_used = model_used
                        str_app.session_state.cached_lesson_name = lesson_input
                    else:
                        str_app.error(f"Không thể kết nối AI. Lỗi chi tiết: `{error}`")

        if str_app.session_state.cached_lesson_result:
            str_app.success(f"Đã hoàn thành tổng hợp kiến thức bài: **{str_app.session_state.get('cached_lesson_name', '')}**")
            str_app.caption(f"Model kết nối thành công: `{str_app.session_state.get('cached_model_used', '')}`")
            str_app.markdown("---")
            render_interactive_quizzes(str_app.session_state.cached_lesson_result, subject)
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
            placeholder="Ví dụ: Đồ thị hàm số y = ax² + bx + c... / Phản ứng H₂ + O₂... / Hình chóp S.ABC...",
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
                        str_app.session_state.lab_result = lab_response
                        str_app.session_state.lab_request_name = lab_request
                        str_app.session_state.lab_version = str_app.session_state.lab_version + 1
                    else:
                        str_app.error(f"Không thể kết nối AI. Lỗi chi tiết: `{lab_error}`")

        # ===== RENDER KẾT QUẢ LAB (dùng session_state, KHÔNG phụ thuộc btn_lab) =====
        if str_app.session_state.lab_result:
            raw_lab = str_app.session_state.lab_result

            plot_2d_match = re.search(r"<PLOT_2D>(.*?)</PLOT_2D>", raw_lab, re.DOTALL | re.IGNORECASE)
            plot_3d_match = re.search(r"<PLOT_3D>(.*?)</PLOT_3D>", raw_lab, re.DOTALL | re.IGNORECASE)
            plot_old_match = re.search(r"<PLOT>(.*?)</PLOT>", raw_lab, re.DOTALL | re.IGNORECASE)

            text_part = re.sub(r"<PLOT_2D>.*?</PLOT_2D>", "", raw_lab, flags=re.DOTALL | re.IGNORECASE)
            text_part = re.sub(r"<PLOT_3D>.*?</PLOT_3D>", "", text_part, flags=re.DOTALL | re.IGNORECASE)
            text_part = re.sub(r"<PLOT>.*?</PLOT>", "", text_part, flags=re.DOTALL | re.IGNORECASE).strip()

            clean_text = clean_ai_response(text_part)
            str_app.markdown(
                f"<div class='content-box'>{clean_text}</div>",
                unsafe_allow_html=True
            )

            plot_code = None
            plot_label = ""
            is_2d = False
            if plot_3d_match:
                plot_code = plot_3d_match.group(1).strip()
                plot_label = "#### 🌐 Đồ thị 3D tương tác (giữ chuột trái để xoay, cuộn để zoom)"
            elif plot_2d_match:
                plot_code = plot_2d_match.group(1).strip()
                plot_label = "#### 📈 Đồ thị minh họa"
                is_2d = True
            elif plot_old_match:
                plot_code = plot_old_match.group(1).strip()
                plot_label = "#### 📈 Đồ thị minh họa"
                is_2d = True

            if plot_code:
                try:
                    if is_2d:
                        coeffs = extract_coefficients(plot_code)
                    else:
                        coeffs = {}

                    if coeffs and 1 <= len(coeffs) <= 5:
                        col_left, col_right = str_app.columns([1, 2.5])

                        with col_left:
                            coeff_names = ", ".join(coeffs.keys())
                            str_app.markdown(
                                f"<h4 style='color:#4a90e2; margin-bottom: 20px;'>⚙️ Hệ số hàm số (theo {coeff_names}):</h4>",
                                unsafe_allow_html=True
                            )

                            lab_id_safe = re.sub(r"[^a-zA-Z0-9_]", "_", str_app.session_state.lab_request_name)[:30]
                            lab_version = str_app.session_state.lab_version

                            user_coeffs = {}
                            for name, init_val in coeffs.items():
                                slider_key = f"coeff_v{lab_version}_{lab_id_safe}_{name}"

                                # Đảm bảo giá trị khởi tạo nằm trong range
                                min_v = min(-10.0, init_val - 5.0)
                                max_v = max(10.0, init_val + 5.0)

                                # Nếu đã có giá trị trong session_state, dùng nó
                                if slider_key in str_app.session_state:
                                    current_val = str_app.session_state[slider_key]
                                    if current_val < min_v:
                                        min_v = current_val - 1.0
                                    if current_val > max_v:
                                        max_v = current_val + 1.0
                                    init_val = current_val

                                str_app.markdown(f"**Hệ số {name}:**")
                                user_coeffs[name] = str_app.slider(
                                    f"Chọn {name}",
                                    min_value=float(min_v),
                                    max_value=float(max_v),
                                    value=float(init_val),
                                    step=0.1,
                                    key=slider_key,
                                    label_visibility="collapsed"
                                )

                            # Công thức động
                            formula_text = _format_formula(user_coeffs, plot_code)
                            str_app.markdown(
                                f"<div style='background: linear-gradient(135deg, #4a90e2, #357abd); color: white; "
                                f"padding: 14px 18px; border-radius: 10px; font-size: 1.05rem; "
                                f"font-weight: 600; margin: 20px 0; text-align: center;'>"
                                f"<i>{formula_text}</i></div>",
                                unsafe_allow_html=True
                            )

                            # Đỉnh + Trục đối xứng (chỉ khi parabol)
                            is_quadratic = (
                                "a" in user_coeffs
                                and "b" in user_coeffs
                                and "d" not in user_coeffs
                                and "e" not in user_coeffs
                            )

                            if is_quadratic and user_coeffs["a"] != 0:
                                a_v = user_coeffs["a"]
                                b_v = user_coeffs["b"]
                                c_v = user_coeffs.get("c", 0)

                                vx = -b_v / (2 * a_v)
                                vy = a_v * vx ** 2 + b_v * vx + c_v

                                str_app.markdown(
                                    f"<p style='color: #d62728; font-weight: 600; margin: 10px 0;'>"
                                    f"📐 <b>Đỉnh:</b> I({vx:.2f}; {vy:.2f})</p>",
                                    unsafe_allow_html=True
                                )
                                str_app.markdown(
                                    f"<p style='color: #d62728; font-weight: 600; margin: 10px 0;'>"
                                    f"📏 <b>Trục đối xứng:</b> x = {vx:.2f}</p>",
                                    unsafe_allow_html=True
                                )

                        with col_right:
                            new_plot_code = substitute_coefficients(plot_code, user_coeffs)
                            kind, data = run_plot_code(new_plot_code)
                            if kind == "plotly" and data is not None:
                                str_app.plotly_chart(data, use_container_width=True, config=PLOTLY_CONFIG)
                            elif kind == "png" and data:
                                str_app.image(data, use_container_width=True)
                            else:
                                str_app.warning("AI đã sinh code vẽ nhưng không tạo được đồ thị.")
                    else:
                        kind, data = run_plot_code(plot_code)
                        if kind == "png" and data:
                            str_app.markdown(plot_label)
                            str_app.image(data, use_container_width=True)
                        elif kind == "plotly" and data is not None:
                            str_app.markdown(plot_label)
                            str_app.plotly_chart(data, use_container_width=True, config=PLOTLY_CONFIG)
                        else:
                            str_app.warning("AI đã sinh code vẽ nhưng không tạo được đồ thị.")
                except Exception as plot_err:
                    str_app.warning(f"Không vẽ được đồ thị: `{plot_err}`")

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

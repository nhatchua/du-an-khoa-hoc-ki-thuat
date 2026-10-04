# ============================================================
# SECTION 1: IMPORTS & CONFIG
# ============================================================
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

ESSAY_SUBJECTS = {"Ngữ văn", "Lịch sử & Địa lý"}
LAB_SUPPORTED_SUBJECTS = {"Toán học", "Vật lý", "Hóa học", "Sinh học", "Tin học", "Lịch sử & Địa lý"}

# ============================================================
# SECTION 2: UTILITIES
# ============================================================
def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(r"(#{1,3}\s*)?📌?\s*1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI", re.IGNORECASE | re.UNICODE)
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
            has_vietnamese = bool(re.search(r"[àáảãạăâđêôơưèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", stripped, re.IGNORECASE))
            latin_ratio = sum(c.isascii() and c.isalpha() for c in stripped) / max(len(stripped), 1)
            if not has_vietnamese and latin_ratio > 0.5:
                continue
        filtered.append(line)
    result = '\n'.join(filtered).strip()
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def trigger_mathjax():
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


def extract_coefficients(code_str: str) -> dict:
    coeffs = {}
    pattern = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:#.*)?$")
    blacklist = {"dpi", "height", "width", "size", "n", "x", "y", "t", "i", "j", "k"}
    for line in code_str.split("\n"):
        m = pattern.match(line.strip())
        if m:
            name = m.group(1)
            if name in blacklist:
                continue
            try:
                coeffs[name] = float(m.group(2))
            except ValueError:
                continue
    return coeffs


def substitute_coefficients(code_str: str, coeff_values: dict) -> str:
    for name, value in coeff_values.items():
        val_str = str(int(value)) if value == int(value) else str(round(value, 4))
        pattern = re.compile(
            rf"^(\s*{re.escape(name)}\s*=\s*)(-?\d+(?:\.\d+)?)(\s*(?:#.*)?)$",
            re.MULTILINE
        )
        code_str = pattern.sub(rf"\g<1>{val_str}\g<3>", code_str)
    return code_str


def run_plot_code(code_str: str):
    import os
    plot_path = "/tmp/lab_plot.png"
    if os.path.exists(plot_path):
        try:
            os.remove(plot_path)
        except Exception:
            pass

    forbidden = ["os.system", "subprocess", "shutil", "socket", "open(", "eval(", "compile(", "requests.", "urllib", "pathlib"]
    code_lower = code_str.lower()
    for kw in forbidden:
        if kw.lower() in code_lower:
            raise ValueError(f"Code chứa từ khóa không được phép: {kw}")

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
        "getattr": getattr, "setattr": setattr, "__import__": __import__,
    }

    try:
        import plotly.graph_objects as go
        import plotly.express as px
    except ImportError:
        go = None
        px = None

    namespace = {"plt": plt, "np": np, "math": __import__("math"), "__builtins__": safe_builtins}
    if go is not None:
        namespace["go"] = go
        namespace["px"] = px

    try:
        exec(code_str, namespace)
        fig_var = namespace.get("fig")
        if fig_var is not None and hasattr(fig_var, "to_plotly_json"):
            return ("plotly", fig_var)
        if not os.path.exists(plot_path):
            try:
                plt.savefig(plot_path, dpi=130, bbox_inches="tight", pad_inches=0.15)
            except Exception:
                pass
        if os.path.exists(plot_path) and os.path.getsize(plot_path) > 1000:
            return ("png", plot_path)
        return (None, None)
    finally:
        plt.close('all')


def call_gemini(prompt: str, api_key: str) -> tuple:
    genai.configure(api_key=api_key)
    model_candidates = [
        "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash",
        "gemini-2.5-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-8b"
    ]
    generation_config = genai.types.GenerationConfig(temperature=0.0, top_p=0.85, max_output_tokens=8192)
    last_error = ""
    for model_name in model_candidates:
        retries = 2
        for i in range(retries):
            try:
                model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
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


def call_gemini_with_fallback(prompt, api_key: str, system_instruction: str = "") -> str:
    genai.configure(api_key=api_key)
    model_candidates = [
        "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash",
        "gemini-2.5-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-8b"
    ]
    generation_config = genai.types.GenerationConfig(temperature=0.0, top_p=0.85, max_output_tokens=8192)
    for model_name in model_candidates:
        try:
            kwargs = {"model_name": model_name, "generation_config": generation_config}
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
# SECTION 3: PLOT TEMPLATES THEO MÔN
# ============================================================

# ---- Khối chung 2D (mũi tên trục, nhãn O/x/y, tên công thức) ----
_PLOT_BASE_2D = """
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
    text=__FORMULA__,
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)',
    bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text=__TITLE__, x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520,
    margin=dict(l=20, r=20, t=50, b=30))
"""


# ---- Helper: ghép base vào template ----
def _build_2d_template(body: str, formula: str, title: str) -> str:
    base = _PLOT_BASE_2D.replace("__FORMULA__", f'"{formula}"').replace("__TITLE__", f'"{title}"')
    return f"""import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

{body}

{base}"""


# ---- TOÁN HỌC ----
_TOAN_TEMPLATES = {
    "đa thức": _build_2d_template(
        body="""x = np.linspace(-2, 6, 1000)
y = a*x**2 + b*x + c
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

if a != 0:
    vx = -b / (2*a); vy = a*vx**2 + b*vx + c
    fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
        marker=dict(color='#d62728', size=12, line=dict(color='white', width=2)), showlegend=False))
    fig.add_annotation(x=vx, y=vy, text="I(" + str(round(vx,2)) + "; " + str(round(vy,2)) + ")",
        showarrow=False, xshift=20, yshift=-40, xanchor='left', yanchor='top',
        font=dict(color='#d62728', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#d62728', borderwidth=1, borderpad=4)

fig.add_trace(go.Scatter(x=[0], y=[c], mode='markers',
    marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
fig.add_annotation(x=0, y=c, text="(0; " + str(round(c,2)) + ")",
    showarrow=False, xshift=50, yshift=5, xanchor='left', yanchor='middle',
    font=dict(color='#2ca02c', size=12, weight='bold'),
    bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)

if a != 0:
    for r in np.roots([a, b, c]):
        if abs(r.imag) < 1e-6:
            xr = r.real
            fig.add_trace(go.Scatter(x=[xr], y=[0], mode='markers',
                marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
            fig.add_annotation(x=xr, y=0, text="(" + str(round(xr,2)) + "; 0)",
                showarrow=False, yshift=35, xanchor='center', yanchor='bottom',
                font=dict(color='#2ca02c', size=11, weight='bold'),
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)

x_range = [-2.5, 6.5]
ymin = float(np.min(y)); ymax = float(np.max(y))
pad = (ymax - ymin) * 0.1 + 1
y_range = [ymin - pad, ymax + pad]""",
        formula="y = ax² + bx + c", title="Đồ thị hàm số bậc hai"
    ),

    "phân thức": _build_2d_template(
        body="""x = np.linspace(-20, 20, 5000)
y = (a*x**2 + b*x + c) / (d*x + e)
mask = np.abs(d*x + e) < 0.05
y[mask] = np.nan
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip', connectgaps=False))

x_range = [-10, 10]; y_range = [-30, 30]

if e != 0:
    y0 = c / e
    fig.add_trace(go.Scatter(x=[0], y=[y0], mode='markers',
        marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
    fig.add_annotation(x=0, y=y0, text="(0; " + str(round(y0, 2)) + ")",
        showarrow=False, xshift=50, yshift=5, xanchor='left', yanchor='middle',
        font=dict(color='#2ca02c', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)

if a != 0:
    for r in np.roots([a, b, c]):
        if abs(r.imag) < 1e-6:
            xr = r.real
            if d != 0 and abs(xr - (-e/d)) < 0.1: continue
            fig.add_trace(go.Scatter(x=[xr], y=[0], mode='markers',
                marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
            fig.add_annotation(x=xr, y=0, text="(" + str(round(xr,2)) + "; 0)",
                showarrow=False, yshift=35, xanchor='center', yanchor='bottom',
                font=dict(color='#2ca02c', size=11, weight='bold'),
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)

if d != 0:
    x_tcd = -e / d
    fig.add_shape(type="line", x0=x_tcd, x1=x_tcd, y0=0, y1=1,
        xref="x", yref="paper", line=dict(color="#999", width=1.5, dash="dash"))
    x_str = str(int(x_tcd)) if x_tcd == int(x_tcd) else str(round(x_tcd, 2))
    fig.add_annotation(x=x_tcd, y=0.85, xref="x", yref="paper", text="x = " + x_str,
        showarrow=False, xshift=15, xanchor='left', yanchor='middle',
        font=dict(color='#666', size=12),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#999', borderwidth=1, borderpad=4)
    m = a / d; n = (b*d - a*e) / (d*d)
    fig.add_shape(type="line", x0=-1000, y0=m*(-1000) + n, x1=1000, y1=m*1000 + n,
        xref="x", yref="y", line=dict(color="#999", width=1.5, dash="dash"))
    m_part = "x" if m == 1 else ("-x" if m == -1 else ("" if m == 0 else str(int(m) if m == int(m) else round(m, 2)) + "x"))
    if n > 0: n_part = " + " + (str(int(n)) if n == int(n) else str(round(n, 2)))
    elif n < 0:
        na = abs(n); n_part = " - " + (str(int(na)) if na == int(na) else str(round(na, 2)))
    else: n_part = ""
    fig.add_annotation(x=5, y=m*5 + n, xref="x", yref="y", text="y = " + m_part + n_part,
        showarrow=False, xshift=-10, yshift=15, xanchor='right', yanchor='bottom',
        font=dict(color='#666', size=12),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#999', borderwidth=1, borderpad=4)""",
        formula="y = (ax² + bx + c)/(dx + e)", title="Đồ thị hàm phân thức"
    ),

    "lượng giác": _build_2d_template(
        body="""x = np.linspace(-2*np.pi, 2*np.pi, 2000)
y = a*np.sin(b*x + c)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-2*np.pi - 0.5, 2*np.pi + 0.5]
y_range = [-abs(a) - 0.5, abs(a) + 0.5]

if b != 0:
    T = 2*np.pi / abs(b)
    if abs(T) > 0.5:
        fig.add_shape(type="line", x0=T, x1=T, y0=0, y1=1,
            xref="x", yref="paper", line=dict(color="#999", width=1, dash="dot"))

for mark in [-np.pi, -np.pi/2, np.pi/2, np.pi]:
    fig.add_annotation(x=mark, y=0, text=str(round(mark/np.pi, 2)) + "π",
        showarrow=False, yshift=-20, font=dict(size=11, color='#666'))""",
        formula="y = a·sin(bx + c)", title="Đồ thị hàm số lượng giác"
    ),

    "mũ và logarit": _build_2d_template(
        body="""x = np.linspace(-3, 3, 1000)
y = a**x
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-3.5, 3.5]; y_range = [-1, 12]

fig.add_shape(type="line", x0=0, x1=1, y0=0, y1=0,
    xref="paper", yref="y", line=dict(color="#999", width=1.5, dash="dash"))
fig.add_annotation(x=0.9, y=0, xref="paper", yref="y", text="y = 0",
    showarrow=False, xshift=-10, yshift=15, xanchor='right', yanchor='bottom',
    font=dict(color='#666', size=12),
    bgcolor='rgba(255,255,255,0.9)', bordercolor='#999', borderwidth=1, borderpad=4)

fig.add_trace(go.Scatter(x=[0], y=[1], mode='markers',
    marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
fig.add_annotation(x=0, y=1, text="(0; 1)", showarrow=False, xshift=50, yshift=5,
    xanchor='left', yanchor='middle', font=dict(color='#2ca02c', size=12, weight='bold'),
    bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)""",
        formula="y = a^x", title="Đồ thị hàm số mũ"
    ),

    "căn thức": _build_2d_template(
        body="""if a > 0:
    x0 = -b/a; x = np.linspace(x0, x0 + 10, 1000)
elif a < 0:
    x0 = -b/a; x = np.linspace(x0 - 10, x0, 1000)
else:
    x = np.linspace(0, 10, 1000)
y = np.sqrt(np.maximum(a*x + b, 0))
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [float(np.min(x)) - 0.5, float(np.max(x)) + 0.5]
y_range = [-0.5, float(np.max(y)) + 1]

if a != 0:
    x0 = -b/a
    fig.add_trace(go.Scatter(x=[x0], y=[0], mode='markers',
        marker=dict(color='#2ca02c', size=10, line=dict(color='white', width=2)), showlegend=False))
    fig.add_annotation(x=x0, y=0, text="(" + str(round(x0, 2)) + "; 0)",
        showarrow=False, xshift=-30, yshift=20, xanchor='right', yanchor='bottom',
        font=dict(color='#2ca02c', size=12, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#2ca02c', borderwidth=1, borderpad=4)""",
        formula="y = √(ax + b)", title="Đồ thị hàm căn thức"
    ),

    "đường tròn / elip": _build_2d_template(
        body="""t = np.linspace(0, 2*np.pi, 500)
x = a*np.cos(t); y = a*np.sin(t)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-a - 2, a + 2]; y_range = [-a - 2, a + 2]

fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers',
    marker=dict(color='#d62728', size=12, line=dict(color='white', width=2)), showlegend=False))
fig.add_annotation(x=0, y=0, text="O", showarrow=False,
    xshift=-18, yshift=-18, font=dict(size=14, weight='bold', color='#333'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)""",
        formula="x² + y² = R²", title="Đường tròn tâm O bán kính R"
    ),

    "hình học phẳng": _build_2d_template(
        body="""A = (0, 0); B = (4, 0); C = (1, 3)
fig.add_trace(go.Scatter(x=[A[0], B[0], C[0], A[0]], y=[A[1], B[1], C[1], A[1]],
    mode='lines', line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=[A[0], B[0], C[0], A[0]], y=[A[1], B[1], C[1], A[1]],
    mode='none', fill='toself', fillcolor='rgba(31, 78, 156, 0.1)', showlegend=False, hoverinfo='skip'))

for pt, name, xs, ys in [(A,'A',-18,-12), (B,'B',12,-12), (C,'C',-12,12)]:
    fig.add_annotation(x=pt[0], y=pt[1], text=name, showarrow=False,
        xshift=xs, yshift=ys, font=dict(size=16, weight='bold', color='#d62728'),
        bgcolor='rgba(255,255,255,0.9)', borderpad=3)

x_range = [-1, 5]; y_range = [-1, 4]""",
        formula="Tam giác ABC", title="Hình tam giác ABC"
    ),
}


# ---- VẬT LÝ ----
_LY_TEMPLATES = {
    "dao động điều hòa": _build_2d_template(
        body="""t = np.linspace(0, 4*np.pi, 2000)
y = A*np.cos(omega*t + phi)
fig.add_trace(go.Scatter(x=t, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [0, 4*np.pi + 0.5]
y_range = [-abs(A) - 0.5, abs(A) + 0.5]

if omega != 0:
    T = 2*np.pi / abs(omega)
    fig.add_annotation(x=T, y=0, text="T", showarrow=False, yshift=-25,
        font=dict(size=12, weight='bold', color='#d62728'))

fig.add_annotation(x=0, y=A, text="A", showarrow=False, xshift=-25,
    font=dict(size=12, weight='bold', color='#2ca02c'))
fig.add_annotation(x=0, y=-A, text="-A", showarrow=False, xshift=-30,
    font=dict(size=12, weight='bold', color='#2ca02c'))""",
        formula="x = A·cos(ωt + φ)", title="Dao động điều hòa x-t"
    ),

    "sóng hình sin": _build_2d_template(
        body="""x = np.linspace(0, 4*np.pi, 2000)
y = A*np.sin(k*x - omega*t)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [0, 4*np.pi + 0.5]
y_range = [-abs(A) - 0.5, abs(A) + 0.5]

if k != 0:
    lam = 2*np.pi / abs(k)
    fig.add_annotation(x=lam, y=0, text="λ", showarrow=False, yshift=-25,
        font=dict(size=12, weight='bold', color='#d62728'))""",
        formula="u = A·sin(kx - ωt)", title="Sóng hình sin"
    ),

    "đồ thị vận tốc - thời gian": _build_2d_template(
        body="""t = np.linspace(0, 10, 500)
v = v0 + a*t
fig.add_trace(go.Scatter(x=t, y=v, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [-0.5, 10.5]
vmin = float(np.min(v)); vmax = float(np.max(v))
pad = (vmax - vmin) * 0.1 + 1
y_range = [vmin - pad, vmax + pad]

fig.add_annotation(x=0, y=v0, text="v₀", showarrow=False, xshift=-25,
    font=dict(size=12, weight='bold', color='#2ca02c'),
    bgcolor='rgba(255,255,255,0.9)', borderpad=3)""",
        formula="v = v₀ + at", title="Đồ thị vận tốc - thời gian"
    ),

    "sơ đồ mạch điện": """
import plotly.graph_objects as go

fig = go.Figure()

# Khung mạch chữ nhật
fig.add_trace(go.Scatter(x=[0, 4, 4, 0, 0], y=[0, 0, 3, 3, 0],
    mode='lines', line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# Điện trở R (hình zigzag tại cạnh trên)
fig.add_trace(go.Scatter(x=[1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2], y=[3, 3.2, 2.8, 3.2, 2.8, 3.2, 3],
    mode='lines', line=dict(color='#d62728', width=3), showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=1.6, y=3.5, text="R", showarrow=False,
    font=dict(size=16, weight='bold', color='#d62728'))

# Nguồn điện (cạnh trái)
fig.add_trace(go.Scatter(x=[0, 0], y=[1.3, 1.7], mode='lines',
    line=dict(color='#2ca02c', width=4), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=[-0.1, 0.1], y=[1.5, 1.5], mode='lines',
    line=dict(color='#2ca02c', width=4), showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=-0.4, y=1.5, text="E", showarrow=False,
    font=dict(size=16, weight='bold', color='#2ca02c'))

x_range = [-1, 5]; y_range = [-0.5, 4]

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="Mạch điện R",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)', bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Sơ đồ mạch điện', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=False, showgrid=False, showticklabels=False, visible=False),
    yaxis=dict(range=y_range, zeroline=False, showgrid=False, showticklabels=False, visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "vector lực": """
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# Vector lực F1 (từ gốc O)
fig.add_annotation(x=3, y=2, ax=0, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=4, arrowcolor='#d62728')
fig.add_annotation(x=3.2, y=2.2, text="F₁", showarrow=False,
    font=dict(size=14, weight='bold', color='#d62728'))

# Vector lực F2
fig.add_annotation(x=-2, y=3, ax=0, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=4, arrowcolor='#2ca02c')
fig.add_annotation(x=-2.3, y=3.2, text="F₂", showarrow=False,
    font=dict(size=14, weight='bold', color='#2ca02c'))

# Vector tổng hợp
fig.add_annotation(x=1, y=5, ax=0, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=4, arrowcolor='#1f4e9c')
fig.add_annotation(x=1.2, y=5.2, text="F", showarrow=False,
    font=dict(size=14, weight='bold', color='#1f4e9c'))

x_range = [-3, 4]; y_range = [-1, 6]

fig.add_annotation(x=x_range[1], y=0, ax=x_range[1]-0.5, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2, arrowcolor='#333')
fig.add_annotation(x=0, y=y_range[1], ax=0, ay=y_range[1]*0.92,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.8, arrowwidth=2, arrowcolor='#333')
fig.add_annotation(x=0, y=0, text='O', showarrow=False,
    xshift=-14, yshift=-14, font=dict(size=15, color='#333'))
fig.add_annotation(x=x_range[1], y=0, text='x', showarrow=False,
    xshift=-6, yshift=-18, font=dict(size=15, color='#333'))
fig.add_annotation(x=0, y=y_range[1], text='y', showarrow=False,
    xshift=-18, yshift=-8, font=dict(size=15, color='#333'))

fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="Tổng hợp lực",
    showarrow=False, xanchor='right', yanchor='bottom',
    font=dict(size=13, color='#1f4e9c'),
    bgcolor='rgba(255,255,255,0.85)', bordercolor='#1f4e9c', borderwidth=1.5, borderpad=6)

fig.update_layout(
    title=dict(text='Vector lực và tổng hợp lực', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=x_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0', scaleanchor="y", scaleratio=1),
    yaxis=dict(range=y_range, zeroline=True, zerolinewidth=1.5, zerolinecolor='#333',
        showgrid=True, gridcolor='#e0e0e0'),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",
}


# ---- HÓA HỌC ----
_HOA_TEMPLATES = {
    "sơ đồ phản ứng": """
import plotly.graph_objects as go

fig = go.Figure()

# Chất tham gia (bên trái)
fig.add_annotation(x=0.15, y=0.5, xref="paper", yref="paper",
    text="<b>2H₂</b>", showarrow=False,
    font=dict(size=18, color='#1f4e9c'))
fig.add_annotation(x=0.30, y=0.5, xref="paper", yref="paper",
    text="+", showarrow=False,
    font=dict(size=20, color='#333'))
fig.add_annotation(x=0.42, y=0.5, xref="paper", yref="paper",
    text="<b>O₂</b>", showarrow=False,
    font=dict(size=18, color='#1f4e9c'))

# Mũi tên phản ứng
fig.add_annotation(x=0.65, y=0.5, ax=0.48, ay=0.5,
    xref="paper", yref="paper", axref="paper", ayref="paper",
    showarrow=True, arrowhead=3, arrowsize=2.5, arrowwidth=3, arrowcolor='#d62728')
fig.add_annotation(x=0.565, y=0.57, xref="paper", yref="paper",
    text="t°", showarrow=False,
    font=dict(size=14, color='#d62728', weight='bold'))

# Sản phẩm (bên phải)
fig.add_annotation(x=0.80, y=0.5, xref="paper", yref="paper",
    text="<b>2H₂O</b>", showarrow=False,
    font=dict(size=18, color='#2ca02c'))

fig.update_layout(
    title=dict(text='Sơ đồ phản ứng hóa học', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(visible=False, range=[0, 1]),
    yaxis=dict(visible=False, range=[0, 1]),
    plot_bgcolor='white', height=300, margin=dict(l=20, r=20, t=50, b=30))
""",

    "đồ thị nồng độ": _build_2d_template(
        body="""t = np.linspace(0, 10, 500)
C_A = C0 * np.exp(-k*t)
C_B = C0 * (1 - np.exp(-k*t))
fig.add_trace(go.Scatter(x=t, y=C_A, mode='lines',
    line=dict(color='#d62728', width=3), name='Chất A', showlegend=True, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=t, y=C_B, mode='lines',
    line=dict(color='#2ca02c', width=3), name='Chất B', showlegend=True, hoverinfo='skip'))

x_range = [0, 10.5]
cmax = float(max(np.max(C_A), np.max(C_B)))
y_range = [-cmax*0.1, cmax*1.2]

fig.update_layout(legend=dict(x=0.75, y=0.95, bgcolor='rgba(255,255,255,0.9)',
    bordercolor='#999', borderwidth=1))""",
        formula="[A] = C₀·e^(-kt)", title="Đồ thị nồng độ theo thời gian"
    ),

    "sơ đồ thí nghiệm": """
import plotly.graph_objects as go

fig = go.Figure()

# Ống nghiệm (hình chữ nhật đứng)
fig.add_trace(go.Scatter(x=[0.3, 0.5, 0.5, 0.3, 0.3], y=[0.1, 0.1, 0.7, 0.7, 0.1],
    mode='lines', line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# Chất lỏng (tô màu)
fig.add_trace(go.Scatter(x=[0.32, 0.48, 0.48, 0.32, 0.32], y=[0.1, 0.1, 0.4, 0.4, 0.1],
    mode='none', fill='toself', fillcolor='rgba(31, 78, 156, 0.4)',
    showlegend=False, hoverinfo='skip'))

# Ống dẫn khí
fig.add_trace(go.Scatter(x=[0.4, 0.4, 0.7, 0.7], y=[0.7, 0.9, 0.9, 0.75],
    mode='lines', line=dict(color='#333', width=3), showlegend=False, hoverinfo='skip'))

# Bình thu khí
fig.add_trace(go.Scatter(x=[0.7, 0.9, 0.9, 0.7, 0.7], y=[0.2, 0.2, 0.75, 0.75, 0.2],
    mode='lines', line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# Nhãn
fig.add_annotation(x=0.4, y=0.85, text="Khí thoát ra", showarrow=False,
    font=dict(size=12, color='#666'))
fig.add_annotation(x=0.8, y=0.5, text="Thu khí", showarrow=False,
    font=dict(size=12, color='#666'))

fig.update_layout(
    title=dict(text='Sơ đồ thí nghiệm', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(visible=False, range=[0, 1]),
    yaxis=dict(visible=False, range=[0, 1]),
    plot_bgcolor='white', height=400, margin=dict(l=20, r=20, t=50, b=30))
""",

    "bảng tuần hoàn mini": """
import plotly.graph_objects as go

fig = go.Figure()

# Ô nguyên tố (dạng lưới 3x3 mẫu)
elements = [
    (0, 2, "H", "#d62728"), (1, 2, "", "#fff"), (2, 2, "", "#fff"),
    (0, 1, "Li", "#1f4e9c"), (1, 1, "Be", "#2ca02c"), (2, 1, "B", "#666"),
    (0, 0, "Na", "#1f4e9c"), (1, 0, "Mg", "#2ca02c"), (2, 0, "Al", "#666"),
]

for x, y, symbol, color in elements:
    fig.add_shape(type="rect", x0=x, x1=x+0.9, y0=y, y1=y+0.9,
        line=dict(color='#999', width=2),
        fillcolor='rgba(240, 240, 240, 0.5)')
    if symbol:
        fig.add_annotation(x=x+0.45, y=y+0.45, text="<b>" + symbol + "</b>",
            showarrow=False, font=dict(size=18, color=color))

fig.update_layout(
    title=dict(text='Bảng tuần hoàn mini', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(visible=False, range=[-0.5, 3.5]),
    yaxis=dict(visible=False, range=[-0.5, 3.5]),
    plot_bgcolor='white', height=400, margin=dict(l=20, r=20, t=50, b=30))
""",
}
# ---- SINH HỌC ----
_SINH_TEMPLATES = {
    "sơ đồ tế bào": """
import plotly.graph_objects as go

fig = go.Figure()

# Màng tế bào (hình elip)
t = __import__("numpy").linspace(0, 2*__import__("numpy").pi, 200)
x_out = 3*__import__("numpy").cos(t)
y_out = 2*__import__("numpy").sin(t)
fig.add_trace(go.Scatter(x=x_out, y=y_out, mode='lines',
    line=dict(color='#1f4e9c', width=4), showlegend=False, hoverinfo='skip'))

# Nhân tế bào
x_n = 0.8*__import__("numpy").cos(t)
y_n = 0.8*__import__("numpy").sin(t)
fig.add_trace(go.Scatter(x=x_n, y=y_n, mode='lines',
    line=dict(color='#d62728', width=3), showlegend=False, hoverinfo='skip',
    fill='toself', fillcolor='rgba(214, 39, 40, 0.2)'))
fig.add_annotation(x=0, y=0, text="<b>Nhân</b>", showarrow=False,
    font=dict(size=13, color='#d62728'))

# Ti thể (2 hình bầu dục nhỏ)
fig.add_shape(type="ellipse", x0=-2, y0=0.8, x1=-1, y1=1.3,
    line=dict(color='#2ca02c', width=3), fillcolor='rgba(44, 160, 44, 0.2)')
fig.add_annotation(x=-1.5, y=1.05, text="Ti thể", showarrow=False,
    font=dict(size=11, color='#2ca02c'))

fig.add_shape(type="ellipse", x0=1.5, y0=-0.5, x1=2.5, y1=0,
    line=dict(color='#2ca02c', width=3), fillcolor='rgba(44, 160, 44, 0.2)')
fig.add_annotation(x=2, y=-0.25, text="Ti thể", showarrow=False,
    font=dict(size=11, color='#2ca02c'))

fig.update_layout(
    title=dict(text='Sơ đồ tế bào', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[-4, 4], visible=False),
    yaxis=dict(range=[-3, 3], visible=False),
    plot_bgcolor='white', height=500, margin=dict(l=20, r=20, t=50, b=30))
""",

    "chu trình quang hợp": """
import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# Vòng tròn chu trình
t = np.linspace(0, 2*np.pi, 100)
x = 3*np.cos(t); y = 3*np.sin(t)
fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
    line=dict(color='#2ca02c', width=4), showlegend=False, hoverinfo='skip'))

# Mũi tên chỉ hướng
fig.add_annotation(x=2.12, y=2.12, ax=3, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor='#2ca02c')

# Các giai đoạn
labels = [
    (3.5, 0, "Ánh sáng<br>(Pha sáng)"),
    (0, 3.5, "H₂O + CO₂"),
    (-3.5, 0, "Chu trình<br>Calvin"),
    (0, -3.5, "C₆H₁₂O₆ + O₂"),
]
for xl, yl, txt in labels:
    fig.add_annotation(x=xl, y=yl, text="<b>" + txt + "</b>", showarrow=False,
        font=dict(size=12, color='#1f4e9c'),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#1f4e9c',
        borderwidth=1, borderpad=4)

fig.update_layout(
    title=dict(text='Chu trình quang hợp', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[-5, 5], visible=False, scaleanchor="y", scaleratio=1),
    yaxis=dict(range=[-5, 5], visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "phả hệ di truyền": """
import plotly.graph_objects as go

fig = go.Figure()

# Thế hệ I
fig.add_shape(type="rect", x0=0.2, y0=0.7, x1=0.5, y1=0.9,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(31, 78, 156, 0.2)')
fig.add_annotation(x=0.35, y=0.8, text="<b>Ông</b>", showarrow=False,
    font=dict(size=13, color='#1f4e9c'))

fig.add_shape(type="circle", x0=0.6, y0=0.7, x1=0.9, y1=0.9,
    line=dict(color='#d62728', width=3), fillcolor='rgba(214, 39, 40, 0.2)')
fig.add_annotation(x=0.75, y=0.8, text="<b>Bà</b>", showarrow=False,
    font=dict(size=13, color='#d62728'))

# Đường hôn nhân
fig.add_trace(go.Scatter(x=[0.5, 0.6], y=[0.8, 0.8], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))

# Đường xuống thế hệ II
fig.add_trace(go.Scatter(x=[0.55, 0.55], y=[0.7, 0.5], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=[0.3, 0.8], y=[0.5, 0.5], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=[0.3, 0.3], y=[0.5, 0.35], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))
fig.add_trace(go.Scatter(x=[0.8, 0.8], y=[0.5, 0.35], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))

# Thế hệ II
fig.add_shape(type="rect", x0=0.15, y0=0.15, x1=0.45, y1=0.35,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(31, 78, 156, 0.2)')
fig.add_annotation(x=0.3, y=0.25, text="<b>Con trai</b>", showarrow=False,
    font=dict(size=12, color='#1f4e9c'))

fig.add_shape(type="circle", x0=0.65, y0=0.15, x1=0.95, y1=0.35,
    line=dict(color='#d62728', width=3), fillcolor='rgba(214, 39, 40, 0.4)')
fig.add_annotation(x=0.8, y=0.25, text="<b>Con gái</b><br>(bị bệnh)", showarrow=False,
    font=dict(size=11, color='#d62728'))

fig.update_layout(
    title=dict(text='Phả hệ di truyền', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1.1], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    plot_bgcolor='white', height=500, margin=dict(l=20, r=20, t=50, b=30))
""",

    "biểu đồ tăng trưởng quần thể": _build_2d_template(
        body="""t = np.linspace(0, 20, 500)
N = K / (1 + ((K - N0) / N0) * np.exp(-r*t))
fig.add_trace(go.Scatter(x=t, y=N, mode='lines',
    line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

x_range = [0, 20.5]; y_range = [-K*0.1, K*1.15]

fig.add_shape(type="line", x0=0, x1=1, y0=K, y1=K,
    xref="paper", yref="y", line=dict(color="#d62728", width=1.5, dash="dash"))
fig.add_annotation(x=0.95, y=K, xref="paper", yref="y", text="K (sức chứa)",
    showarrow=False, xshift=-10, yshift=15, xanchor='right', yanchor='bottom',
    font=dict(color='#d62728', size=12),
    bgcolor='rgba(255,255,255,0.9)', bordercolor='#d62728',
    borderwidth=1, borderpad=4)""",
        formula="N(t) = K / (1 + Ce^(-rt))", title="Tăng trưởng quần thể (logistic)"
    ),
}


# ---- TIN HỌC ----
_TIN_TEMPLATES = {
    "flowchart thuật toán": """
import plotly.graph_objects as go

fig = go.Figure()

# Hình bầu dục: Bắt đầu
fig.add_shape(type="circle", x0=0.4, y0=0.85, x1=0.6, y1=0.95,
    line=dict(color='#2ca02c', width=3), fillcolor='rgba(44, 160, 44, 0.2)')
fig.add_annotation(x=0.5, y=0.9, text="Bắt đầu", showarrow=False,
    font=dict(size=12, color='#2ca02c'))

# Mũi tên xuống
fig.add_trace(go.Scatter(x=[0.5, 0.5], y=[0.85, 0.78], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))

# Hình chữ nhật: Nhập
fig.add_shape(type="rect", x0=0.35, y0=0.68, x1=0.65, y1=0.78,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(31, 78, 156, 0.2)')
fig.add_annotation(x=0.5, y=0.73, text="Nhập n", showarrow=False,
    font=dict(size=12, color='#1f4e9c'))

# Mũi tên
fig.add_trace(go.Scatter(x=[0.5, 0.5], y=[0.68, 0.6], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))

# Hình thoi: Điều kiện
fig.add_shape(type="path", path="M 0.5 0.6 L 0.65 0.5 L 0.5 0.4 L 0.35 0.5 Z",
    line=dict(color='#d62728', width=3), fillcolor='rgba(214, 39, 40, 0.2)')
fig.add_annotation(x=0.5, y=0.5, text="n > 0?", showarrow=False,
    font=dict(size=12, color='#d62728'))

# Nhánh Đúng
fig.add_trace(go.Scatter(x=[0.65, 0.75, 0.75], y=[0.5, 0.5, 0.3], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.73, y=0.53, text="Đúng", showarrow=False,
    font=dict(size=11, color='#2ca02c'))

# Nhánh Sai
fig.add_trace(go.Scatter(x=[0.35, 0.25, 0.25], y=[0.5, 0.5, 0.3], mode='lines',
    line=dict(color='#333', width=2), showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.27, y=0.53, text="Sai", showarrow=False,
    font=dict(size=11, color='#d62728'))

# Hình chữ nhật: Xử lý
fig.add_shape(type="rect", x0=0.65, y0=0.2, x1=0.85, y1=0.3,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(31, 78, 156, 0.2)')
fig.add_annotation(x=0.75, y=0.25, text="Xử lý", showarrow=False,
    font=dict(size=12, color='#1f4e9c'))

# Kết thúc
fig.add_shape(type="circle", x0=0.15, y0=0.2, x1=0.35, y1=0.3,
    line=dict(color='#2ca02c', width=3), fillcolor='rgba(44, 160, 44, 0.2)')
fig.add_annotation(x=0.25, y=0.25, text="Kết thúc", showarrow=False,
    font=dict(size=11, color='#2ca02c'))

fig.update_layout(
    title=dict(text='Flowchart thuật toán', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "cây nhị phân": """
import plotly.graph_objects as go

fig = go.Figure()

# Đỉnh
nodes = {
    1: (0.5, 0.85, "A"),
    2: (0.3, 0.6, "B"),
    3: (0.7, 0.6, "C"),
    4: (0.2, 0.35, "D"),
    5: (0.4, 0.35, "E"),
    6: (0.6, 0.35, "F"),
    7: (0.8, 0.35, "G"),
}

# Cạnh
edges = [(1,2), (1,3), (2,4), (2,5), (3,6), (3,7)]
for p1, p2 in edges:
    x1, y1, _ = nodes[p1]; x2, y2, _ = nodes[p2]
    fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode='lines',
        line=dict(color='#1f4e9c', width=3), showlegend=False, hoverinfo='skip'))

# Nút
for nid, (x, y, label) in nodes.items():
    fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers+text',
        marker=dict(color='#2ca02c', size=35, line=dict(color='white', width=2)),
        text=[label], textposition='middle center',
        textfont=dict(size=14, color='white', weight='bold'),
        showlegend=False, hoverinfo='skip'))

fig.update_layout(
    title=dict(text='Cây nhị phân', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0.2, 1], visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "đồ thị mạng": """
import plotly.graph_objects as go

fig = go.Figure()

# Nút
nodes = {
    "A": (0.2, 0.7), "B": (0.5, 0.85), "C": (0.8, 0.7),
    "D": (0.2, 0.3), "E": (0.5, 0.15), "F": (0.8, 0.3),
}

# Cạnh
edges = [("A","B"), ("B","C"), ("A","D"), ("B","E"), ("C","F"), ("D","E"), ("E","F")]
for p1, p2 in edges:
    x1, y1 = nodes[p1]; x2, y2 = nodes[p2]
    fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode='lines',
        line=dict(color='#999', width=2), showlegend=False, hoverinfo='skip'))

# Nút
for name, (x, y) in nodes.items():
    fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers+text',
        marker=dict(color='#1f4e9c', size=40, line=dict(color='white', width=2)),
        text=[name], textposition='middle center',
        textfont=dict(size=14, color='white', weight='bold'),
        showlegend=False, hoverinfo='skip'))

fig.update_layout(
    title=dict(text='Đồ thị mạng', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "sơ đồ CSDL quan hệ": """
import plotly.graph_objects as go

fig = go.Figure()

# Bảng SinhVien
fig.add_shape(type="rect", x0=0.1, y0=0.55, x1=0.4, y1=0.9,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(31, 78, 156, 0.15)')
fig.add_annotation(x=0.25, y=0.85, text="<b>SinhVien</b>", showarrow=False,
    font=dict(size=13, color='#1f4e9c'))
fig.add_annotation(x=0.25, y=0.77, text="🔑 MaSV", showarrow=False,
    font=dict(size=11, color='#333'))
fig.add_annotation(x=0.25, y=0.7, text="HoTen", showarrow=False,
    font=dict(size=11, color='#333'))
fig.add_annotation(x=0.25, y=0.63, text="NgaySinh", showarrow=False,
    font=dict(size=11, color='#333'))

# Bảng Lop
fig.add_shape(type="rect", x0=0.6, y0=0.55, x1=0.9, y1=0.9,
    line=dict(color='#2ca02c', width=3), fillcolor='rgba(44, 160, 44, 0.15)')
fig.add_annotation(x=0.75, y=0.85, text="<b>Lop</b>", showarrow=False,
    font=dict(size=13, color='#2ca02c'))
fig.add_annotation(x=0.75, y=0.77, text="🔑 MaLop", showarrow=False,
    font=dict(size=11, color='#333'))
fig.add_annotation(x=0.75, y=0.7, text="TenLop", showarrow=False,
    font=dict(size=11, color='#333'))

# Quan hệ
fig.add_trace(go.Scatter(x=[0.4, 0.6], y=[0.72, 0.72], mode='lines',
    line=dict(color='#d62728', width=3, dash='dash'), showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.5, y=0.77, text="MaSV", showarrow=False,
    font=dict(size=10, color='#d62728', weight='bold'))

fig.update_layout(
    title=dict(text='Sơ đồ CSDL quan hệ', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0.4, 1], visible=False),
    plot_bgcolor='white', height=450, margin=dict(l=20, r=20, t=50, b=30))
""",
}


# ---- SỬ & ĐỊA ----
_SUDIA_TEMPLATES = {
    "timeline sự kiện": """
import plotly.graph_objects as go

fig = go.Figure()

# Trục thời gian
fig.add_trace(go.Scatter(x=[0, 1], y=[0.5, 0.5], mode='lines',
    line=dict(color='#1f4e9c', width=4), showlegend=False, hoverinfo='skip'))

# Mốc sự kiện
events = [
    (0.1, "1945", "Cách mạng<br>tháng Tám", 1),
    (0.35, "1954", "Chiến thắng<br>Điện Biên Phủ", -1),
    (0.6, "1975", "Giải phóng<br>miền Nam", 1),
    (0.85, "1986", "Đổi mới", -1),
]

for x, year, event, direction in events:
    # Chấm mốc
    fig.add_trace(go.Scatter(x=[x], y=[0.5], mode='markers',
        marker=dict(color='#d62728', size=15, line=dict(color='white', width=2)),
        showlegend=False, hoverinfo='skip'))
    # Đường chỉ
    y_end = 0.5 + 0.25*direction
    fig.add_trace(go.Scatter(x=[x, x], y=[0.5, y_end], mode='lines',
        line=dict(color='#999', width=1.5, dash='dot'),
        showlegend=False, hoverinfo='skip'))
    # Nhãn năm
    fig.add_annotation(x=x, y=0.5, text="<b>" + year + "</b>", showarrow=False,
        yshift=25 if direction > 0 else -25,
        font=dict(size=14, color='#1f4e9c'))
    # Nhãn sự kiện
    fig.add_annotation(x=x, y=y_end, text=event, showarrow=False,
        yshift=25 if direction > 0 else -45,
        font=dict(size=11, color='#333'),
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#1f4e9c',
        borderwidth=1, borderpad=4)

fig.update_layout(
    title=dict(text='Timeline sự kiện lịch sử', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[-0.05, 1.05], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    plot_bgcolor='white', height=450, margin=dict(l=20, r=20, t=50, b=30))
""",

    "sơ đồ tư duy": """
import plotly.graph_objects as go

fig = go.Figure()

# Trung tâm
fig.add_shape(type="circle", x0=0.4, y0=0.4, x1=0.6, y1=0.6,
    line=dict(color='#1f4e9c', width=4), fillcolor='rgba(31, 78, 156, 0.3)')
fig.add_annotation(x=0.5, y=0.5, text="<b>Chủ đề</b>", showarrow=False,
    font=dict(size=14, color='#1f4e9c', weight='bold'))

# Nhánh
branches = [
    (0.15, 0.85, "Nhánh 1", '#d62728'),
    (0.85, 0.85, "Nhánh 2", '#2ca02c'),
    (0.15, 0.15, "Nhánh 3", '#f39c12'),
    (0.85, 0.15, "Nhánh 4", '#9b59b6'),
]

for x, y, label, color in branches:
    # Đường nối
    fig.add_trace(go.Scatter(x=[0.5, x], y=[0.5, y], mode='lines',
        line=dict(color=color, width=3), showlegend=False, hoverinfo='skip'))
    # Nút nhánh
    fig.add_shape(type="circle", x0=x-0.08, y0=y-0.06, x1=x+0.08, y1=y+0.06,
        line=dict(color=color, width=3), fillcolor='rgba(255, 255, 255, 0.9)')
    fig.add_annotation(x=x, y=y, text="<b>" + label + "</b>", showarrow=False,
        font=dict(size=12, color=color))

fig.update_layout(
    title=dict(text='Sơ đồ tư duy', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    plot_bgcolor='white', height=520, margin=dict(l=20, r=20, t=50, b=30))
""",

    "bản đồ đơn giản": """
import plotly.graph_objects as go

fig = go.Figure()

# Khung bản đồ
fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
    line=dict(color='#1f4e9c', width=3), fillcolor='rgba(200, 230, 250, 0.5)')

# Vùng miền (đa giác đơn giản)
vung_bac = dict(x=[0, 1, 1, 0.7, 0.5, 0.3, 0], y=[1, 1, 0.7, 0.65, 0.6, 0.65, 0.7])
fig.add_trace(go.Scatter(x=vung_bac["x"], y=vung_bac["y"], mode='lines',
    line=dict(color='#d62728', width=2), fill='toself',
    fillcolor='rgba(214, 39, 40, 0.15)', showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.5, y=0.85, text="<b>Miền Bắc</b>", showarrow=False,
    font=dict(size=12, color='#d62728'))

vung_trung = dict(x=[0, 0.7, 0.7, 0.6, 0.4, 0.3, 0], y=[0.7, 0.65, 0.4, 0.35, 0.3, 0.35, 0.4])
fig.add_trace(go.Scatter(x=vung_trung["x"], y=vung_trung["y"], mode='lines',
    line=dict(color='#f39c12', width=2), fill='toself',
    fillcolor='rgba(243, 156, 18, 0.15)', showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.35, y=0.5, text="<b>Miền Trung</b>", showarrow=False,
    font=dict(size=12, color='#f39c12'))

vung_nam = dict(x=[0, 0.6, 0.7, 1, 1, 0.3], y=[0.4, 0.35, 0, 0, 0.3, 0.35])
fig.add_trace(go.Scatter(x=vung_nam["x"], y=vung_nam["y"], mode='lines',
    line=dict(color='#2ca02c', width=2), fill='toself',
    fillcolor='rgba(44, 160, 44, 0.15)', showlegend=False, hoverinfo='skip'))
fig.add_annotation(x=0.5, y=0.2, text="<b>Miền Nam</b>", showarrow=False,
    font=dict(size=12, color='#2ca02c'))

fig.update_layout(
    title=dict(text='Bản đồ đơn giản 3 miền', x=0.5, font=dict(size=14, color='#333')),
    xaxis=dict(range=[-0.05, 1.05], visible=False),
    yaxis=dict(range=[-0.05, 1.05], visible=False, scaleanchor="x", scaleratio=1),
    plot_bgcolor='white', height=550, margin=dict(l=20, r=20, t=50, b=30))
""",
}


# ---- Dict tổng hợp theo môn ----
_ALL_TEMPLATES = {
    "Toán học": _TOAN_TEMPLATES,
    "Vật lý": _LY_TEMPLATES,
    "Hóa học": _HOA_TEMPLATES,
    "Sinh học": _SINH_TEMPLATES,
    "Tin học": _TIN_TEMPLATES,
    "Lịch sử & Địa lý": _SUDIA_TEMPLATES,
}


# ============================================================
# SECTION 4: PROMPTS
# ============================================================
def build_lesson_prompt(lesson_input: str, subject: str, grade: str) -> str:
    is_essay = subject in ESSAY_SUBJECTS
    common_head = f"""Bạn là giáo viên chuyên môn cao, soạn tài liệu theo chuẩn chương trình giáo dục phổ thông mới nhất bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

NHIỆM VỤ: Soạn nội dung chi tiết bài học "{lesson_input}" môn {subject} lớp {grade}.

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung hoàn toàn bằng TIẾNG VIỆT chuẩn xác. Không chứa từ tiếng Anh, không suy luận nội tâm, không bản nháp.
2. KHÔNG DÙNG DẤU #. Chỉ dùng định dạng đánh số thứ tự cho các phần lớn.
3. ĐỐI VỚI CÔNG THỨC TOÁN HỌC/KÍ HIỆU KHOA HỌC: Bắt buộc sử dụng kí hiệu LaTeX đặt trong cặp dấu đô la.
4. Kiến thức phải cực kỳ chính xác, khoa học, sư phạm theo đúng sách Kết Nối Tri Thức.

CẤU TRÚC ĐẦU RA BẮT BUỘC:

1. KIẾN THỨC CỐT LÕI CẦN GHI NHỚ
[Viết chi tiết, rõ ràng, giải thích sâu sắc bản chất, định lý, công thức trọng tâm.]

2. CÁC LỖI SAI THƯỜNG GẶP KHI LÀM BÀI
[Liệt kê 4-5 lỗi sai và hướng khắc phục.]

"""
    if is_essay:
        tail = """3. HỆ THỐNG ĐỀ LUYỆN VIẾT
(Tạo 3 đề luyện viết theo cấu trúc đề kiểm tra thật, KHÔNG đưa đáp án.)

---
[ĐỀ 1]
Loại đề: ...
Đề bài: ...
Yêu cầu: ...
Thang điểm: ...
GỢI Ý DÀN Ý: ...
---
(Lặp lại cho ĐỀ 2, ĐỀ 3)."""
    else:
        tail = """3. HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
(Tạo 3 câu hỏi trắc nghiệm 4 lựa chọn A, B, C, D.)

---
[CÂU HỎI 1]
Nội dung câu hỏi...
A. ...
B. ...
C. ...
D. ...
ĐÁP ÁN ĐÚNG: [A/B/C/D]
GỢI Ý TƯ DUY: [gợi ý, không tiết lộ đáp án]
---
(Lặp lại cho Câu 2, Câu 3)."""
    return common_head + tail


def build_virtual_lab_prompt(lab_request: str, subject: str, grade: str) -> str:
    # Lấy template theo môn, fallback Toán nếu không có
    subject_templates = _ALL_TEMPLATES.get(subject, _TOAN_TEMPLATES)

    # Xây khối template text từ dict
    templates_block = ""
    for idx, (name, code) in enumerate(subject_templates.items(), 1):
        templates_block += f"\n=== 📌 TEMPLATE {idx} — {name.upper()} ===\n<PLOT_2D>\n{code.strip()}\n</PLOT_2D>\n"

    # Nếu môn có 3D (Toán), thêm template 3D
    template_3d_block = ""
    if subject == "Toán học":
        template_3d_block = """
=== 📌 TEMPLATE 3D — HÌNH HỌC KHÔNG GIAN ===
<PLOT_3D>
import plotly.graph_objects as go
import numpy as np

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
        text=[name], textfont=dict(size=14, color='black', weight='bold'), showlegend=False))
fig.update_layout(title='Hình chóp S.ABC',
    scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
    margin=dict(l=0, r=0, t=40, b=0), height=520)
</PLOT_3D>
"""

    template = f"""Bạn là chuyên gia mô phỏng thí nghiệm giáo dục cho học sinh __GRADE__ môn __SUBJECT__ theo chương trình GDPT 2018 bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

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

=== 🎯 QUY TẮC CHỌN TEMPLATE (BẮT BUỘC ĐỌC KỸ) ===

BƯỚC 1: Đọc yêu cầu học sinh, tìm TỪ KHÓA.
BƯỚC 2: Tra bảng dưới đây để chọn ĐÚNG 1 template.
BƯỚC 3: KHÔNG tự bịa template mới. KHÔNG mặc định chọn template ĐA THỨC nếu từ khóa không khớp.

| Từ khóa trong yêu cầu | Template cần chọn |
|------------------------|-------------------|
| "sin", "cos", "tan", "cot", "lượng giác", "dao động tuần hoàn" | TEMPLATE LƯỢNG GIÁC |
| "ax² + bx + c", "parabol", "bậc hai", "bậc 3", "bậc 4", "đa thức" | TEMPLATE ĐA THỨC |
| "phân thức", "/(dx + e)", "tiệm cận", "hypebol" | TEMPLATE PHÂN THỨC |
| "mũ", "a^x", "e^x", "exp", "logarit", "ln", "log" | TEMPLATE MŨ VÀ LOGARIT |
| "căn", "√", "sqrt", "căn bậc hai" | TEMPLATE CĂN THỨC |
| "đường tròn", "elip", "hình tròn", "x² + y²" | TEMPLATE ĐƯỜNG TRÒN / ELIP |
| "tam giác", "tứ giác", "đa giác", "hình phẳng" | TEMPLATE HÌNH HỌC PHẲNG |
| "hình chóp", "lăng trụ", "hộp", "mặt cầu", "nón", "trụ", "3D", "không gian" | TEMPLATE 3D |

⚠️ CẢNH BÁO:
- Nếu yêu cầu có "sin" HOẶC "cos" HOẶC "tan" HOẶC "cot" HOẶC "lượng giác" → CHẮC CHẮN chọn TEMPLATE LƯỢNG GIÁC, KHÔNG được chọn ĐA THỨC.
- Nếu yêu cầu có "dao động", "sóng", "chu kỳ" → CHẮC CHẮN chọn TEMPLATE LƯỢNG GIÁC.
- Chỉ chọn ĐA THỨC khi yêu cầu CÓ RÕ "ax² + bx + c", "parabol", "bậc hai/ba/bốn".

=== ⚠️ QUY TẮC KHAI BÁO HỆ SỐ (CHỈ VỚI HÀM SỐ) ===
- Khai báo hệ số ở ĐẦU CODE (TRƯỚC import), MỖI HỆ SỐ 1 DÒNG
- Format: `a = 1` (có khoảng trắng quanh dấu =)
- KHÔNG dùng list `coeffs = [...]`, KHÔNG gộp `a, b, c = 1, 2, 3`

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

{templates_block}
{template_3d_block}

LƯU Ý CUỐI:
- Chọn ĐÚNG 1 template phù hợp với yêu cầu
- KHÔNG gọi fig.show(), KHÔNG savefig
- CHỈ dùng: plotly.graph_objects, numpy, math
- MỌI nhãn điểm PHẢI CÓ bgcolor='rgba(255,255,255,0.9)' + borderpad=4"""

    return template.replace("__LAB_REQUEST__", lab_request).replace("__SUBJECT__", subject).replace("__GRADE__", grade)
# ============================================================
# SECTION 5: UI SETUP
# ============================================================
def setup_page_config():
    str_app.set_page_config(
        page_title="Gia Sư AI - Hệ Sinh Thái Lớp Học Đảo Ngược",
        page_icon="📚",
        layout="wide"
    )
    str_app.markdown("""
        <style>
        /* ===== TIÊU ĐỀ CHÍNH ===== */
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

        /* ===== DÀN ĐỀU 5 TAB (DESKTOP) ===== */
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

        /* ===== ĐẶC TRƯNG ĐỒ THỊ ===== */
        .feature-title {
            color: #4a90e2 !important;
            margin: 20px 0 10px 0;
            font-size: 0.95rem;
            font-weight: 600;
        }
        .feature-item {
            margin: 5px 0;
            padding: 8px 12px;
            background: rgba(74, 144, 226, 0.12);
            border-left: 3px solid #4a90e2;
            border-radius: 4px;
            font-size: 0.88rem;
            color: inherit !important;
            line-height: 1.5;
        }
        .feature-item b {
            color: #4a90e2 !important;
            font-weight: 700;
        }

        /* ============================================================
           RESPONSIVE MOBILE — Áp dụng cho màn hình < 768px
           ============================================================ */
        @media (max-width: 768px) {

            /* --- 1. TAB: chia 2 dòng, chữ xuống dòng thay vì bị cắt --- */
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap !important;
                gap: 4px !important;
            }
            .stTabs [data-baseweb="tab-list"] > button {
                flex: 1 1 calc(50% - 4px) !important;
                font-size: 0.72rem !important;
                padding: 8px 4px !important;
                white-space: normal !important;
                line-height: 1.2 !important;
                min-height: 48px !important;
            }

            /* --- 2. LAYOUT 2 CỘT (sliders + đồ thị) → xếp dọc, full width --- */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="column"],
            [data-testid="stColumn"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 12px !important;
            }

            /* --- 3. TIÊU ĐỀ + KHUNG NỘI DUNG GỌN HƠN --- */
            .main-heading {
                font-size: 1.0rem !important;
                padding: 10px 14px !important;
                margin-top: 15px !important;
                margin-bottom: 12px !important;
            }
            .content-box {
                padding: 15px !important;
                margin-bottom: 15px !important;
            }

            /* --- 4. TIÊU ĐỀ TRANG CHỦ H1 nhỏ hơn --- */
            h1 {
                font-size: 1.3rem !important;
                line-height: 1.3 !important;
            }
            h2 { font-size: 1.1rem !important; }
            h3 { font-size: 1.0rem !important; }

            /* --- 5. ĐẶC TRƯNG ĐỒ THỊ GỌN HƠN --- */
            .feature-item {
                font-size: 0.82rem !important;
                padding: 6px 10px !important;
                margin: 4px 0 !important;
            }
            .feature-title {
                font-size: 0.9rem !important;
                margin: 15px 0 8px 0 !important;
            }

            /* --- 6. SLIDER: label nhỏ, slider dễ kéo --- */
            [data-testid="stSlider"] label {
                font-size: 0.85rem !important;
            }
            [data-testid="stSlider"] [role="slider"] {
                width: 22px !important;
                height: 22px !important;
            }

            /* --- 7. INPUT + BUTTON full width, font vừa --- */
            [data-testid="stTextInput"] input {
                font-size: 0.9rem !important;
                padding: 8px 10px !important;
            }
            [data-testid="stButton"] button {
                font-size: 0.85rem !important;
                padding: 8px 12px !important;
                width: 100% !important;
            }

            /* --- 8. RADIO + EXPANDER nhỏ hơn --- */
            [data-testid="stRadio"] label {
                font-size: 0.85rem !important;
            }
            [data-testid="stExpander"] summary {
                font-size: 0.85rem !important;
                padding: 8px 10px !important;
            }

            /* --- 9. CHAT MESSAGE gọn hơn --- */
            [data-testid="stChatMessage"] {
                font-size: 0.9rem !important;
                padding: 10px !important;
            }

            /* --- 10. ĐỒ THỊ PLOTLY: bo góc + giảm margin --- */
            [data-testid="stPlotlyChart"] {
                border-radius: 8px !important;
                overflow: hidden !important;
            }
        }

        /* ============================================================
           RESPONSIVE TABLET — Màn hình 768px - 1024px
           ============================================================ */
        @media (min-width: 769px) and (max-width: 1024px) {
            .stTabs [data-baseweb="tab-list"] > button {
                font-size: 0.8rem !important;
                padding: 9px 6px !important;
            }
            .main-heading { font-size: 1.15rem !important; }
        }
        </style>
        <script type="text/javascript" async
          src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
        </script>
    """, unsafe_allow_html=True)

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
# SECTION 6: UI QUIZ
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
        r"<div class='main-heading'>\1</div>", theory_part, flags=re.IGNORECASE
    )
    theory_part = re.sub(
        r"(2\.\s*CÁC\s*LỖI\s*SAI\s*THƯỜNG\s*GẶP\s*KHI\s*LÀM\s*BÀI)",
        r"<div class='main-heading'>\1</div>", theory_part, flags=re.IGNORECASE
    )

    str_app.markdown(f"<div class='content-box'>{theory_part}</div>", unsafe_allow_html=True)
    str_app.markdown(f"<div class='main-heading'>{display_header}</div>", unsafe_allow_html=True)
    str_app.markdown(f"<p style='font-weight: 500; margin-bottom: 20px;'>{sub_title}</p>", unsafe_allow_html=True)

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

    question_blocks = re.findall(r"\[CÂU\s*HỎI\s*\d+\](.*?)(?=\[CÂU\s*HỎI|\Z)", exercise_part, re.DOTALL | re.IGNORECASE)
    q_index = 1
    for q_block in question_blocks:
        if not q_block.strip():
            continue
        ans_match = re.search(r"ĐÁP\s*ÁN\s*ĐÚNG:\s*([A-Da-d])", q_block, re.IGNORECASE)
        correct_ans = ans_match.group(1).strip().upper() if ans_match else "A"
        hint_match = re.search(r"GỢI\s*Ý\s*TƯ\s*DUY:\s*(.*?)(?=\n-{2,}|\n\[|$)", q_block, re.DOTALL | re.IGNORECASE)
        hint_text = hint_match.group(1).strip() if hint_match else "Hãy đọc kỹ lại phần lý thuyết cốt lõi ở trên."
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
                options=["A", "B", "C", "D"], index=None,
                key=choice_key, horizontal=True, label_visibility="collapsed"
            )
            btn_clicked = str_app.button(
                "✅ Kiểm tra kết quả", key=f"check_btn_{q_index}", type="primary"
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
                        "Chính xác! Em đã chọn đúng đáp án.</p>", unsafe_allow_html=True)
                else:
                    str_app.markdown(
                        "<p style='color: #dc3545; font-weight: bold; margin-top: 10px;'>"
                        "Chưa chính xác. Hãy xem gợi ý tư duy bên dưới.</p>", unsafe_allow_html=True)
                with str_app.expander(f"💡 Gợi ý tư duy cho câu {q_index}", expanded=True):
                    str_app.info(hint_text)
            else:
                with str_app.expander(f"Gợi ý tư duy cho câu {q_index} (Nhấp để xem khi quá bí)", expanded=False):
                    str_app.info(hint_text)
        q_index += 1


# ============================================================
# SECTION 7: UI MAIN
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

    # ===== HÀM CON: FORMAT SỐ =====
    def _fmt_num(v, suffix=""):
        v_abs = abs(v)
        if v_abs == 1 and suffix:
            return suffix
        if v_abs == int(v_abs):
            return f"{int(v_abs)}{suffix}"
        return f"{v_abs:.1f}{suffix}"

    # ===== HÀM CON: FORMAT CÔNG THỨC =====
    def _format_formula(coeffs_dict, code_str=""):
        code_lower = code_str.lower()

        # === PHÂN LOẠI HÀM ===
        is_frac = ("d" in coeffs_dict and "e" in coeffs_dict and "/" in code_str
                   and "cos" not in code_lower and "sin" not in code_lower)

        # === LƯỢNG GIÁC ===
        if "sin" in code_lower or "cos" in code_lower or "tan" in code_lower or "cot" in code_lower:
            a = coeffs_dict.get("a", 1)
            b = coeffs_dict.get("b", 1)
            c = coeffs_dict.get("c", 0)
            # Xác định tên hàm
            if "sin" in code_lower:
                func_name = "sin"
            elif "cos" in code_lower:
                func_name = "cos"
            elif "tan" in code_lower:
                func_name = "tan"
            else:
                func_name = "cot"
            # Xây chuỗi bên trong ngoặc: "bx + c"
            a_str = "" if abs(a - 1) < 1e-9 else ("-" if abs(a + 1) < 1e-9 else _fmt_num(a))
            b_str = "" if abs(b - 1) < 1e-9 else ("-" if abs(b + 1) < 1e-9 else _fmt_num(b))
            inner = f"{b_str}x"
            if abs(c) > 1e-9:
                if c > 0:
                    inner += f" + {_fmt_num(c)}"
                else:
                    inner += f" - {_fmt_num(abs(c))}"
            return f"y = {a_str}{func_name}({inner})"

        # === PHÂN THỨC ===
        if is_frac:
            num_parts = []
            for name, suffix in [("a", "x²"), ("b", "x"), ("c", "")]:
                if name not in coeffs_dict:
                    continue
                v = coeffs_dict[name]
                if abs(v) < 1e-9 and num_parts:
                    continue
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
                if abs(v) < 1e-9 and den_parts:
                    continue
                v_str = _fmt_num(v, suffix)
                if not den_parts:
                    den_parts.append(f"-{v_str}" if v < 0 else v_str)
                else:
                    den_parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")
            num_str = " ".join(num_parts) if num_parts else "0"
            den_str = " ".join(den_parts) if den_parts else "1"
            return f"y = ({num_str}) / ({den_str})"

        # === MŨ ===
        if "a**x" in code_lower or "e**x" in code_lower or "exp(" in code_lower:
            a = coeffs_dict.get("a", 2)
            return f"y = {_fmt_num(a)}^x"

        # === LOGARIT ===
        if "log" in code_lower or "ln(" in code_lower:
            a = coeffs_dict.get("a", 10)
            return f"y = log_{_fmt_num(a)}(x)"

        # === CĂN THỨC ===
        if "sqrt" in code_lower or "np.sqrt" in code_lower:
            a = coeffs_dict.get("a", 1)
            b = coeffs_dict.get("b", 0)
            a_str = "" if abs(a - 1) < 1e-9 else ("-" if abs(a + 1) < 1e-9 else _fmt_num(a))
            inner = f"{a_str}x"
            if abs(b) > 1e-9:
                if b > 0:
                    inner += f" + {_fmt_num(b)}"
                else:
                    inner += f" - {_fmt_num(abs(b))}"
            return f"y = √({inner})"

        # === ĐƯỜNG TRÒN ===
        if "cos(t)" in code_lower or "sin(t)" in code_lower:
            a = coeffs_dict.get("a", 1)
            return f"x² + y² = {_fmt_num(a)}²"

        # === ĐA THỨC ===
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
            # Bỏ số hạng có hệ số = 0 (trừ số hạng đầu tiên)
            if abs(v) < 1e-9 and parts:
                continue
            v_str = _fmt_num(v, suffix)
            if not parts:
                parts.append(f"-{v_str}" if v < 0 else v_str)
            else:
                parts.append(f"- {v_str}" if v < 0 else f"+ {v_str}")
        if not parts:
            return "y = 0"
        return "y = " + " ".join(parts)

    # ===== HÀM CON: PHÂN TÍCH ĐẶC TRƯNG (CHỈ VỚI TOÁN) =====
    def _analyze_features(coeffs_dict, code_str):
        if subject != "Toán học":
            return []
        features = []
        code_lower = code_str.lower()

        def fmt(v, decimals=2):
            try:
                if abs(v - round(v)) < 1e-9:
                    return str(int(round(v)))
                return f"{v:.{decimals}f}"
            except Exception:
                return str(v)

        # === PHÂN LOẠI HÀM ===
        is_fractional = ("d" in coeffs_dict and "e" in coeffs_dict and "/" in code_str)

        is_quadratic = (not is_fractional
                        and "a" in coeffs_dict and "b" in coeffs_dict and "c" in coeffs_dict
                        and "d" not in coeffs_dict and "e" not in coeffs_dict)

        is_cubic = (not is_fractional
                    and "a" in coeffs_dict and "b" in coeffs_dict and "c" in coeffs_dict
                    and "d" in coeffs_dict and "e" not in coeffs_dict)

        is_quartic = (not is_fractional
                      and "a" in coeffs_dict and "b" in coeffs_dict and "c" in coeffs_dict
                      and "d" in coeffs_dict and "e" in coeffs_dict)

        # === HÀM PHÂN THỨC (ĐÃ THÊM CỰC TRỊ) ===
        if is_fractional:
            a = coeffs_dict["a"]; b = coeffs_dict["b"]; c = coeffs_dict["c"]
            d = coeffs_dict["d"]; e = coeffs_dict["e"]
            if d != 0:
                # Tiệm cận đứng
                x_tcd = -e / d
                features.append(("🔵", "Tiệm cận đứng", f"x = {fmt(x_tcd)}"))

                # Tiệm cận xiên/ngang
                m = a / d; n = (b * d - a * e) / (d * d)
                if abs(m) < 1e-9:
                    features.append(("🔵", "Tiệm cận ngang", f"y = {fmt(n)}"))
                else:
                    if abs(m - 1) < 1e-9:
                        m_part = "x"
                    elif abs(m + 1) < 1e-9:
                        m_part = "-x"
                    else:
                        m_part = fmt(m) + "x"
                    if n > 1e-9:
                        n_part = " + " + fmt(n)
                    elif n < -1e-9:
                        n_part = " - " + fmt(abs(n))
                    else:
                        n_part = ""
                    features.append(("🔵", "Tiệm cận xiên", f"y = {m_part}{n_part}"))

                # === CỰC TRỊ: nghiệm của ad·x² + 2ae·x + (be−cd) = 0 ===
                A2 = a * d
                B2 = 2 * a * e
                C2 = b * e - c * d
                if abs(A2) > 1e-9:
                    delta = B2 * B2 - 4 * A2 * C2
                    if delta > 1e-9:
                        sqrt_delta = np.sqrt(delta)
                        x1 = (-B2 + sqrt_delta) / (2 * A2)
                        x2 = (-B2 - sqrt_delta) / (2 * A2)
                        y1 = (a * x1**2 + b * x1 + c) / (d * x1 + e)
                        y2 = (a * x2**2 + b * x2 + c) / (d * x2 + e)
                        # Sắp xếp theo x tăng dần
                        if x1 < x2:
                            p1 = (x1, y1); p2 = (x2, y2)
                        else:
                            p1 = (x2, y2); p2 = (x1, y1)
                        # Xác định cực đại/tiểu qua y'' = 2a/(dx+e)
                        ypp1 = 2 * a / (d * p1[0] + e)
                        if ypp1 > 0:
                            features.append(("🔴", "Cực tiểu", f"({fmt(p1[0])}; {fmt(p1[1])})"))
                            features.append(("🔴", "Cực đại", f"({fmt(p2[0])}; {fmt(p2[1])})"))
                        else:
                            features.append(("🔴", "Cực đại", f"({fmt(p1[0])}; {fmt(p1[1])})"))
                            features.append(("🔴", "Cực tiểu", f"({fmt(p2[0])}; {fmt(p2[1])})"))
                    else:
                        features.append(("🔴", "Cực trị", "Không có cực trị"))
                else:
                    # A2 = 0 → hàm bậc 1/bậc 1, không có cực trị
                    features.append(("🔴", "Cực trị", "Không có cực trị"))

                # Giao Oy
                if e != 0:
                    features.append(("🟢", "Giao Oy", f"(0; {fmt(c/e)})"))

        # === HÀM BẬC 2 ===
        elif is_quadratic and coeffs_dict["a"] != 0:
            a = coeffs_dict["a"]; b = coeffs_dict["b"]; c = coeffs_dict["c"]
            delta = b * b - 4 * a * c
            vx = -b / (2 * a); vy = a * vx ** 2 + b * vx + c
            features.append(("📐", "Đỉnh", f"I({fmt(vx)}; {fmt(vy)})"))
            features.append(("📏", "Trục đối xứng", f"x = {fmt(vx)}"))
            features.append(("🎯", "Delta (Δ)", fmt(delta)))
            if delta > 0:
                x1 = (-b + np.sqrt(delta)) / (2 * a)
                x2 = (-b - np.sqrt(delta)) / (2 * a)
                features.append(("⚫", "Giao Ox", f"x₁ = {fmt(x1)}, x₂ = {fmt(x2)}"))
            elif abs(delta) < 1e-9:
                features.append(("⚫", "Giao Ox", f"x = {fmt(vx)} (nghiệm kép)"))
            else:
                features.append(("⚫", "Giao Ox", "Không cắt trục Ox"))
            features.append(("🟢", "Giao Oy", f"(0; {fmt(c)})"))
            features.append(("📊", "Bề lõm", "Hướng lên (a > 0)" if a > 0 else "Hướng xuống (a < 0)"))

        # === HÀM BẬC 3 ===
        elif is_cubic and coeffs_dict["a"] != 0:
            a = coeffs_dict["a"]; b = coeffs_dict["b"]
            c = coeffs_dict["c"]; d = coeffs_dict["d"]
            xi = -b / (3 * a); yi = a * xi ** 3 + b * xi ** 2 + c * xi + d
            features.append(("🔄", "Điểm uốn", f"I({fmt(xi)}; {fmt(yi)})"))
            delta_cp = 4 * b * b - 12 * a * c
            if delta_cp > 0:
                x1 = (-2 * b + np.sqrt(delta_cp)) / (6 * a)
                x2 = (-2 * b - np.sqrt(delta_cp)) / (6 * a)
                y1 = a * x1 ** 3 + b * x1 ** 2 + c * x1 + d
                y2 = a * x2 ** 3 + b * x2 ** 2 + c * x2 + d
                if a > 0:
                    features.append(("🔴", "Cực đại", f"({fmt(x2)}; {fmt(y2)})"))
                    features.append(("🔴", "Cực tiểu", f"({fmt(x1)}; {fmt(y1)})"))
                else:
                    features.append(("🔴", "Cực đại", f"({fmt(x1)}; {fmt(y1)})"))
                    features.append(("🔴", "Cực tiểu", f"({fmt(x2)}; {fmt(y2)})"))
            else:
                features.append(("🔴", "Cực trị", "Không có cực trị"))
            features.append(("🟢", "Giao Oy", f"(0; {fmt(d)})"))

        # === HÀM BẬC 4 ===
        elif is_quartic and coeffs_dict["a"] != 0:
            features.append(("📊", "Bậc", "Hàm bậc 4"))
            features.append(("🟢", "Giao Oy", f"(0; {fmt(coeffs_dict['e'])})"))

        # === HÀM LƯỢNG GIÁC ===
        elif "sin" in code_lower or "cos" in code_lower or "tan" in code_lower or "cot" in code_lower:
            a = coeffs_dict.get("a", 1); b = coeffs_dict.get("b", 1)
            if b != 0:
                if "tan" in code_lower or "cot" in code_lower:
                    features.append(("📏", "Chu kỳ", f"T = π/{fmt(abs(b))}"))
                else:
                    features.append(("📏", "Chu kỳ", f"T = 2π/{fmt(abs(b))}"))
                features.append(("📊", "Biên độ", f"|a| = {fmt(abs(a))}"))
            if "sin" in code_lower:
                features.append(("🔄", "Tâm đối xứng", "O(0; 0)"))
            elif "cos" in code_lower:
                features.append(("🔄", "Trục đối xứng", "Oy"))

        # === HÀM MŨ ===
        elif "a**x" in code_lower or "e**x" in code_lower or "exp(" in code_lower:
            features.append(("🔵", "Tiệm cận ngang", "y = 0"))
            features.append(("🟢", "Giao Oy", "(0; 1)"))
            features.append(("📊", "Miền xác định", "D = ℝ"))

        # === HÀM LOG ===
        elif "log" in code_lower or "ln(" in code_lower:
            features.append(("🔵", "Tiệm cận đứng", "x = 0"))
            features.append(("📊", "Miền xác định", "D = (0; +∞)"))
            features.append(("🟢", "Giao Ox", "(1; 0)"))

        # === ĐƯỜNG TRÒN / ELIP ===
        elif ("cos(t)" in code_lower or "np.cos(t)" in code_lower) and \
             ("sin(t)" in code_lower or "np.sin(t)" in code_lower):
            if "a" in coeffs_dict and "b" in coeffs_dict:
                features.append(("🎯", "Tâm đối xứng", "O(0; 0)"))
                if abs(coeffs_dict["a"] - coeffs_dict["b"]) < 1e-9:
                    features.append(("📏", "Bán kính", f"R = {fmt(coeffs_dict['a'])}"))
                else:
                    features.append(("📏", "Trục lớn", f"2a = {fmt(2*coeffs_dict['a'])}"))
                    features.append(("📏", "Trục nhỏ", f"2b = {fmt(2*coeffs_dict['b'])}"))
            elif "a" in coeffs_dict:
                features.append(("🎯", "Tâm đối xứng", "O(0; 0)"))
                features.append(("📏", "Bán kính", f"R = {fmt(coeffs_dict['a'])}"))

        return features

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
        if subject in LAB_SUPPORTED_SUBJECTS:
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

            # ===== RENDER KẾT QUẢ LAB =====
            if str_app.session_state.lab_result:
                raw_lab = str_app.session_state.lab_result

                plot_2d_match = re.search(r"<PLOT_2D>(.*?)</PLOT_2D>", raw_lab, re.DOTALL | re.IGNORECASE)
                plot_3d_match = re.search(r"<PLOT_3D>(.*?)</PLOT_3D>", raw_lab, re.DOTALL | re.IGNORECASE)
                plot_old_match = re.search(r"<PLOT>(.*?)</PLOT>", raw_lab, re.DOTALL | re.IGNORECASE)

                text_part = re.sub(r"<PLOT_2D>.*?</PLOT_2D>", "", raw_lab, flags=re.DOTALL | re.IGNORECASE)
                text_part = re.sub(r"<PLOT_3D>.*?</PLOT_3D>", "", text_part, flags=re.DOTALL | re.IGNORECASE)
                text_part = re.sub(r"<PLOT>.*?</PLOT>", "", text_part, flags=re.DOTALL | re.IGNORECASE).strip()

                clean_text = clean_ai_response(text_part)
                str_app.markdown(f"<div class='content-box'>{clean_text}</div>", unsafe_allow_html=True)

                plot_code = None
                plot_label = ""
                is_2d = False
                if plot_3d_match:
                    plot_code = plot_3d_match.group(1).strip()
                    plot_label = "#### 🌐 Đồ thị 3D tương tác"
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

                        # Chỉ hiển thị sliders khi có từ 1-5 hệ số VÀ môn là Toán
                        if coeffs and 1 <= len(coeffs) <= 5 and subject == "Toán học":
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
                                    min_v = min(-10.0, init_val - 5.0)
                                    max_v = max(10.0, init_val + 5.0)
                                    if slider_key in str_app.session_state:
                                        current_val = str_app.session_state[slider_key]
                                        if current_val < min_v: min_v = current_val - 1.0
                                        if current_val > max_v: max_v = current_val + 1.0
                                        init_val = current_val
                                    str_app.markdown(f"**Hệ số {name}:**")
                                    user_coeffs[name] = str_app.slider(
                                        f"Chọn {name}",
                                        min_value=float(min_v), max_value=float(max_v),
                                        value=float(init_val), step=0.1,
                                        key=slider_key, label_visibility="collapsed"
                                    )

                                formula_text = _format_formula(user_coeffs, plot_code)
                                str_app.markdown(
                                    f"<div style='background: linear-gradient(135deg, #4a90e2, #357abd); color: white; "
                                    f"padding: 14px 18px; border-radius: 10px; font-size: 1.05rem; "
                                    f"font-weight: 600; margin: 20px 0; text-align: center;'>"
                                    f"<i>{formula_text}</i></div>",
                                    unsafe_allow_html=True
                                )

                                features = _analyze_features(user_coeffs, plot_code)
                                if features:
                                    str_app.markdown(
                                        "<div class='feature-title'>📋 Đặc trưng đồ thị:</div>",
                                        unsafe_allow_html=True
                                    )
                                    for icon, label, value in features:
                                        str_app.markdown(
                                            f"<div class='feature-item'>"
                                            f"{icon} <b>{label}:</b> {value}</div>",
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
                            # Các môn khác: render bình thường, không sliders
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
                                api_key=api_key_to_use, system_instruction=sys_prompt
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
                                            "grade": grade, "subject": subject,
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
# SECTION 8: MAIN
# ============================================================
def main():
    setup_page_config()
    grade, subject, api_key_to_use = render_sidebar()
    render_main_interface(grade, subject, api_key_to_use)


if __name__ == "__main__":
    main()

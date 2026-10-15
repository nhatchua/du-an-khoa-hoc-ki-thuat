"""
_lab.py — Phòng Lab: 31 render types cho mô phỏng trực quan.
Bao gồm: Toán (12), Vật lý (12), Hóa học (8), Sinh học (8).
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import re
import math


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _plotly_config(name="chart"):
    """Config chung cho mọi Plotly chart."""
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": name,
            "scale": 2,
        },
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }


def _hovertemplate_rounded(decimals=2):
    """Hovertemplate cho Scatter 2D, làm tròn theo decimals."""
    return f"x = %{{x:.{decimals}f}}<br>y = %{{y:.{decimals}f}}<extra></extra>"


def setup_pedagogical_oxy(fig, x_range, y_range, equal_aspect=False):
    """Setup trục sư phạm cho đồ thị 2D: grid, zeroline, màu tối."""
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
    )
    fig.update_xaxes(
        range=x_range,
        showgrid=True, gridcolor="#1e293b", gridwidth=1,
        zeroline=True, zerolinecolor="#475569", zerolinewidth=1.5,
        showline=True, linecolor="#475569",
    )
    fig.update_yaxes(
        range=y_range,
        showgrid=True, gridcolor="#1e293b", gridwidth=1,
        zeroline=True, zerolinecolor="#475569", zerolinewidth=1.5,
        showline=True, linecolor="#475569",
    )
    if equal_aspect:
        fig.update_yaxes(scaleanchor='x', scaleratio=1)


def _draw_oxyz_axes(fig, axis_len, axis_min, axis_max):
    """Vẽ 3 trục Ox, Oy, Oz với mũi tên và nhãn."""
    for vec, color, label in [
        ((axis_len, 0, 0), "#ef4444", "x"),
        ((0, axis_len, 0), "#22c55e", "y"),
        ((0, 0, axis_len), "#3b82f6", "z"),
    ]:
        fig.add_trace(go.Scatter3d(
            x=[0, vec[0]], y=[0, vec[1]], z=[0, vec[2]],
            mode='lines+text',
            line=dict(color=color, width=5),
            text=["", label],
            textposition="top center",
            textfont=dict(color=color, size=14),
            showlegend=False, hoverinfo='skip',
        ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0], mode='markers+text',
        marker=dict(size=6, color='#f8fafc'),
        text=['O'], textposition='bottom left',
        textfont=dict(color='#f8fafc', size=12),
        showlegend=False, hoverinfo='skip',
    ))


def _auto_fit_view(dtype, params):
    """Tự động tính range view cho từng loại đồ thị 2D."""
    if dtype == "func_3":
        return -4.0, 4.0, -10.0, 10.0
    if dtype in ("func_1_1", "func_2_1"):
        return -8.0, 8.0, -10.0, 10.0
    if dtype in ("parabola", "func_2"):
        return -5.0, 5.0, -8.0, 8.0
    if dtype == "area":
        a = params.get("a", 0.0)
        b = params.get("b", 1.0)
        pad = max(1.0, (b - a) * 0.2)
        return a - pad, b + pad, -5.0, 10.0
    return -5.0, 5.0, -5.0, 5.0


def _render_info_panel(dtype, params):
    """Info panel bên phải cho từng loại đồ thị."""
    if dtype == "func_3":
        a, b, c, d = params.get("a", 1), params.get("b", 0), params.get("c", 0), params.get("d", 0)
        st.markdown("##### 📝 Hàm số")
        st.latex(rf"y = {a}x^3 + {b}x^2 + {c}x + {d}")
        st.markdown("##### 📐 Đạo hàm")
        st.latex(rf"y' = {3*a}x^2 + {2*b}x + {c}")
        delta = (2*b)**2 - 4*(3*a)*c
        st.markdown("##### 🔍 Biện luận cực trị")
        if abs(a) < 1e-9:
            st.caption("a ≈ 0 → không phải hàm bậc 3")
        elif delta > 0:
            st.markdown("✅ Có **2 cực trị** (CĐ và CT)")
        elif abs(delta) < 1e-9:
            st.markdown("⚠️ Có **1 điểm uốn** (không cực trị)")
        else:
            st.markdown("❌ **Không có cực trị** (đơn điệu)")
    elif dtype == "func_1_1":
        a, b, c, d = params.get("a", 1), params.get("b", 1), params.get("c", 1), params.get("d", -1)
        st.markdown("##### 📝 Hàm số")
        st.latex(rf"y = \dfrac{{{a}x + {b}}}{{{c}x + {d}}}")
        if abs(c) > 1e-9:
            st.markdown("##### 📐 Tiệm cận")
            st.latex(rf"TCĐ: x = {-d/c:.2f}")
            st.latex(rf"TCN: y = {a/c:.2f}")
    elif dtype == "func_2_1":
        a, b, c, d, e = (params.get("a", 1), params.get("b", -2), params.get("c", 2),
                         params.get("d", 1), params.get("e", -1))
        st.markdown("##### 📝 Hàm số")
        st.latex(rf"y = \dfrac{{{a}x^2 + {b}x + {c}}}{{{d}x + {e}}}")
        if abs(d) > 1e-9:
            st.markdown("##### 📐 Tiệm cận")
            st.latex(rf"TCĐ: x = {-e/d:.2f}")
    elif dtype in ("parabola", "func_2"):
        a, b, c = params.get("a", 1), params.get("b", -2), params.get("c", 1)
        st.markdown("##### 📝 Hàm số")
        st.latex(rf"y = {a}x^2 + {b}x + {c}")
        x_dinh = -b / (2 * a)
        y_dinh = a * x_dinh**2 + b * x_dinh + c
        st.markdown("##### 📐 Đỉnh")
        st.latex(rf"I({x_dinh:.2f}; {y_dinh:.2f})")
        delta = b*b - 4*a*c
        st.markdown("##### 🔍 Nghiệm")
        if delta > 0:
            st.markdown("✅ 2 nghiệm phân biệt")
        elif abs(delta) < 1e-9:
            st.markdown("⚠️ Nghiệm kép")
        else:
            st.markdown("❌ Vô nghiệm")
    else:
        st.info("ℹ️ Không có thông tin bổ sung.")


# ==============================================================================
# MAIN DISPATCHER
# ==============================================================================

def render_smart_lab(data: dict):
    """Dispatcher: nhận dict data với key 'type', gọi render tương ứng."""
    if not data or not isinstance(data, dict):
        st.warning("⚠️ Dữ liệu mô phỏng không hợp lệ.")
        return
    dtype = data.get("type", "")
    if not dtype:
        st.warning("⚠️ Thiếu trường 'type' trong dữ liệu mô phỏng.")
        return

    # ========== DIỆN TÍCH HÌNH PHẲNG ==========
    if dtype == "area":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            func_options = [
                "x**2 - 3*x + 2", "x**2 - 4", "np.sin(x)",
                "np.exp(-x**2)", "x**3 - 3*x", "(x**2 - 1)/(x**2 + 1)",
            ]
            default_func = data.get("func", "x**2 - 3*x + 2")
            if default_func not in func_options:
                func_options.insert(0, default_func)
            func_str = st.selectbox("Hàm f(x):", func_options, key="lab_area_func")
            custom_func = st.text_input("Hoặc nhập hàm khác (Python):", value="", key="lab_area_custom")
            if custom_func.strip():
                func_str = custom_func.strip()
            a_val = st.slider("Cận dưới a:", -5.0, 5.0, float(data.get("a", 0.0)), 0.5, key="lab_area_a")
            b_val = st.slider("Cận trên b:", -5.0, 5.0, float(data.get("b", 3.0)), 0.5, key="lab_area_b")
            if b_val <= a_val:
                b_val = a_val + 0.5

        with c2:
            try:
                x_min_v, x_max_v, y_min_v, y_max_v = _auto_fit_view("area", {"a": a_val, "b": b_val})
                x_vals = np.linspace(x_min_v, x_max_v, 800)
                safe_env = {"np": np, "x": x_vals, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "abs": np.abs}
                y_vals = eval(func_str, {"__builtins__": {}}, safe_env)
                if not isinstance(y_vals, np.ndarray):
                    y_vals = np.full_like(x_vals, y_vals)
                x_fill = np.linspace(a_val, b_val, 400)
                safe_env["x"] = x_fill
                y_fill = eval(func_str, {"__builtins__": {}}, safe_env)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                          line=dict(color='#38bdf8', width=3), name='f(x)',
                                          hovertemplate=_hovertemplate_rounded(2)))
                fig.add_trace(go.Scatter(
                    x=np.concatenate([x_fill, x_fill[::-1]]),
                    y=np.concatenate([y_fill, np.zeros_like(y_fill)]),
                    fill='toself', fillcolor='rgba(56,189,248,0.3)',
                    line=dict(color='rgba(0,0,0,0)'), name='Miền S', hoverinfo='skip'))
                setup_pedagogical_oxy(fig, [x_min_v, x_max_v], [y_min_v, y_max_v])
                fig.update_layout(title=f"S = ∫|{func_str}|dx từ {a_val} đến {b_val}", height=420)
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("Area"))
            except Exception as e:
                st.error(f"Lỗi vẽ diện tích: {e}")

        with c3:
            st.markdown("##### 📐 Công thức")
            st.latex(r"S = \int_a^b |f(x)|dx")
            try:
                x_check = np.linspace(a_val, b_val, 1000)
                safe_env = {"np": np, "x": x_check, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "abs": np.abs}
                y_check = eval(func_str, {"__builtins__": {}}, safe_env)
                if not isinstance(y_check, np.ndarray):
                    y_check = np.full_like(x_check, y_check)
                S_val = np.trapz(np.abs(y_check), x_check)
                st.markdown("##### 📏 Kết quả (xấp xỉ)")
                st.latex(rf"S \approx {S_val:.4f}")
            except Exception:
                pass

    # ========== KHỐI TRÒN XOAY ==========
    elif dtype == "revolve_ox":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            func_options = ["2*x + 1", "np.sqrt(x)", "np.sin(x) + 2", "x**2", "np.exp(-x) + 1"]
            default_func = data.get("func", "2*x + 1")
            if default_func not in func_options:
                func_options.insert(0, default_func)
            func_str = st.selectbox("Hàm f(x):", func_options, key="lab_rev_func")
            custom_func = st.text_input("Hoặc nhập hàm khác:", value="", key="lab_rev_custom")
            if custom_func.strip():
                func_str = custom_func.strip()
            a_val = st.slider("Cận dưới a:", 0.0, 5.0, float(data.get("a", 2.0)), 0.5, key="lab_rev_a")
            b_val = st.slider("Cận trên b:", 0.5, 6.0, float(data.get("b", 5.0)), 0.5, key="lab_rev_b")
            if b_val <= a_val:
                b_val = a_val + 0.5
            angle_deg = st.slider("Góc quay (°):", 90, 360, 360, 30, key="lab_rev_angle")
            show_slice = st.checkbox("Hiển thị 1/8 + 2 mặt cắt", value=True, key="lab_rev_slice")

        with c2:
            try:
                n_theta = 60
                theta = np.linspace(0, 2 * np.pi * angle_deg / 360, n_theta)
                x_lin = np.linspace(a_val, b_val, 80)
                safe_env = {"np": np, "x": x_lin, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "abs": np.abs}
                y_lin = eval(func_str, {"__builtins__": {}}, safe_env)
                if not isinstance(y_lin, np.ndarray):
                    y_lin = np.full_like(x_lin, y_lin)
                X, T = np.meshgrid(x_lin, theta)
                Y = np.outer(np.sin(theta), np.abs(y_lin))
                Z = np.outer(np.cos(theta), np.abs(y_lin))
                fig = go.Figure()
                fig.add_trace(go.Surface(x=X, y=Y, z=Z,
                                          colorscale='Blues', opacity=0.75, showscale=False,
                                          name='Khối tròn xoay'))
                fig.add_trace(go.Scatter3d(x=x_lin, y=np.zeros_like(x_lin), z=y_lin,
                                            mode='lines', line=dict(color='#fbbf24', width=6),
                                            name='Đường sinh'))
                fig.update_layout(
                    title=f"Khối tròn xoay quanh Ox: y = {func_str}, x ∈ [{a_val}; {b_val}]",
                    template="plotly_dark",
                    scene=dict(
                        xaxis=dict(backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        yaxis=dict(backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        zaxis=dict(backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        aspectmode='cube',
                        camera=dict(eye=dict(x=1.8, y=1.8, z=1.5)),
                    ),
                    height=460, margin=dict(l=10, r=10, t=30, b=10),
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("RevolveOx"))
            except Exception as e:
                st.error(f"Lỗi vẽ khối tròn xoay: {e}")

        with c3:
            st.markdown("##### 📐 Công thức")
            st.latex(r"V = \pi \int_a^b [f(x)]^2 dx")
            try:
                x_check = np.linspace(a_val, b_val, 1000)
                safe_env = {"np": np, "x": x_check, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "abs": np.abs}
                y_check = eval(func_str, {"__builtins__": {}}, safe_env)
                if not isinstance(y_check, np.ndarray):
                    y_check = np.full_like(x_check, y_check)
                V_val = np.pi * np.trapz(y_check**2, x_check)
                st.markdown("##### 📏 Thể tích (xấp xỉ)")
                st.latex(rf"V \approx {V_val:.4f}")
            except Exception:
                pass

    # ========== MERMAID MINDMAP ==========
    elif dtype == "mermaid":
        code = data.get("code", "")
        if not code.strip():
            st.warning("⚠️ Không có mã Mermaid để hiển thị.")
            return
        safe_code = re.sub(r'\\\\([a-zA-Z])', r'\\\1', code)
        try:
            st.markdown(f"```mermaid\n{safe_code}\n```")
        except Exception as e:
            st.error(f"Lỗi render Mermaid: {e}")

    # ========== DYNAMIC CODE ==========
    elif dtype == "dynamic_code":
        code = data.get("python_code", "")
        if not code.strip():
            st.warning("⚠️ Không có code Python để chạy.")
            return
        try:
            safe_globals = {
                "go": go, "np": np, "st": st, "math": math,
                "setup_pedagogical_oxy": setup_pedagogical_oxy,
                "fig": None,
                "__builtins__": {
                    "range": range, "len": len, "min": min, "max": max,
                    "abs": abs, "float": float, "int": int, "str": str,
                    "list": list, "dict": dict, "tuple": tuple, "print": print,
                },
            }
            exec(code, safe_globals)
            fig = safe_globals.get("fig")
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True,
                                config=_plotly_config("DynamicCode"))
            else:
                st.info("ℹ️ Code đã chạy nhưng không tạo biến `fig`.")
        except Exception as e:
            st.error(f"Lỗi chạy code động: {e}")
    # ========== HÀM BẬC 3 ==========
    elif dtype == "func_3":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Hệ số**")
            fa = st.slider("a:", -3.0, 3.0, float(data.get("a", 1.0)), 0.5, key="lab_f3_a")
            if fa == 0: fa = 0.5
            fb = st.slider("b:", -5.0, 5.0, float(data.get("b", -3.0)), 0.5, key="lab_f3_b")
            fc = st.slider("c:", -5.0, 5.0, float(data.get("c", 0.0)), 0.5, key="lab_f3_c")
            fd = st.slider("d:", -5.0, 5.0, float(data.get("d", 2.0)), 0.5, key="lab_f3_d")

        with c2:
            x_min_v, x_max_v, y_min_v, y_max_v = _auto_fit_view("func_3", {"a": fa, "b": fb, "c": fc, "d": fd})
            x_vals = np.linspace(x_min_v, x_max_v, 800)
            y_vals = fa * (x_vals**3) + fb * (x_vals**2) + fc * x_vals + fd
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                      line=dict(color='#38bdf8', width=3), name='Đồ thị',
                                      hovertemplate=_hovertemplate_rounded(2)))
            setup_pedagogical_oxy(fig, [x_min_v, x_max_v], [y_min_v, y_max_v])
            fig.update_layout(title=f"y = {fa}x³ + {fb}x² + {fc}x + {fd}", height=420)
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("HamBac3"))

        with c3:
            _render_info_panel("func_3", {"a": fa, "b": fb, "c": fc, "d": fd})

    # ========== HÀM PHÂN THỨC 1/1 ==========
    elif dtype == "func_1_1":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Hệ số**")
            fa = st.slider("a:", -4.0, 4.0, float(data.get("a", 1.0)), 0.5, key="lab_f11_a")
            fb = st.slider("b:", -5.0, 5.0, float(data.get("b", 1.0)), 0.5, key="lab_f11_b")
            fc = st.slider("c:", -4.0, 4.0, float(data.get("c", 1.0)), 0.5, key="lab_f11_c")
            if fc == 0: fc = 1.0
            fd = st.slider("d:", -5.0, 5.0, float(data.get("d", -1.0)), 0.5, key="lab_f11_d")

        with c2:
            x_min_v, x_max_v, y_min_v, y_max_v = _auto_fit_view("func_1_1", {"a": fa, "b": fb, "c": fc, "d": fd})
            x_tc_dung = -fd / fc
            y_tc_ngang = fa / fc
            y_cap = max(abs(y_min_v), abs(y_max_v)) * 1.2
            x_left = np.linspace(x_min_v, x_tc_dung - 0.05, 400)
            x_right = np.linspace(x_tc_dung + 0.05, x_max_v, 400)
            y_left = (fa * x_left + fb) / (fc * x_left + fd)
            y_right = (fa * x_right + fb) / (fc * x_right + fd)
            y_left[np.abs(y_left) > y_cap] = np.nan
            y_right[np.abs(y_right) > y_cap] = np.nan
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_left, y=y_left, mode='lines', line=dict(color='#38bdf8', width=3), name='Nhánh trái', hovertemplate=_hovertemplate_rounded(2)))
            fig.add_trace(go.Scatter(x=x_right, y=y_right, mode='lines', line=dict(color='#38bdf8', width=3), name='Nhánh phải', hovertemplate=_hovertemplate_rounded(2)))
            fig.add_trace(go.Scatter(x=[x_tc_dung, x_tc_dung], y=[y_min_v, y_max_v], mode='lines', line=dict(color='#f59e0b', width=1.8, dash='dash'), name='TCĐ', hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=[x_min_v, x_max_v], y=[y_tc_ngang, y_tc_ngang], mode='lines', line=dict(color='#10b981', width=1.8, dash='dash'), name='TCN', hoverinfo='skip'))
            setup_pedagogical_oxy(fig, [x_min_v, x_max_v], [y_min_v, y_max_v])
            fig.update_layout(title=f"y = ({fa}x + {fb}) / ({fc}x + {fd})", height=420)
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("PhanThuc11"))

        with c3:
            _render_info_panel("func_1_1", {"a": fa, "b": fb, "c": fc, "d": fd})

    # ========== HÀM PHÂN THỨC 2/1 ==========
    elif dtype == "func_2_1":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Hệ số**")
            fa = st.slider("a:", -3.0, 3.0, float(data.get("a", 1.0)), 0.5, key="lab_f21_a")
            if fa == 0: fa = 1.0
            fb = st.slider("b:", -5.0, 5.0, float(data.get("b", -2.0)), 0.5, key="lab_f21_b")
            fc = st.slider("c:", -5.0, 5.0, float(data.get("c", 2.0)), 0.5, key="lab_f21_c")
            fd = st.slider("d:", -3.0, 3.0, float(data.get("d", 1.0)), 0.5, key="lab_f21_d")
            if fd == 0: fd = 1.0
            fe = st.slider("e:", -5.0, 5.0, float(data.get("e", -1.0)), 0.5, key="lab_f21_e")

        with c2:
            x_min_v, x_max_v, y_min_v, y_max_v = _auto_fit_view("func_2_1", {"a": fa, "b": fb, "c": fc, "d": fd, "e": fe})
            x_tc_dung = -fe / fd
            m_slope = fa / fd
            n_intercept = (fb - m_slope * fe) / fd
            y_cap = max(abs(y_min_v), abs(y_max_v)) * 1.2
            x_left = np.linspace(x_min_v, x_tc_dung - 0.05, 400)
            x_right = np.linspace(x_tc_dung + 0.05, x_max_v, 400)
            y_left = (fa * x_left**2 + fb * x_left + fc) / (fd * x_left + fe)
            y_right = (fa * x_right**2 + fb * x_right + fc) / (fd * x_right + fe)
            y_left[np.abs(y_left) > y_cap] = np.nan
            y_right[np.abs(y_right) > y_cap] = np.nan
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_left, y=y_left, mode='lines', line=dict(color='#38bdf8', width=3), name='Đồ thị', hovertemplate=_hovertemplate_rounded(2)))
            fig.add_trace(go.Scatter(x=x_right, y=y_right, mode='lines', line=dict(color='#38bdf8', width=3), name='Đồ thị', hovertemplate=_hovertemplate_rounded(2)))
            fig.add_trace(go.Scatter(x=[x_tc_dung, x_tc_dung], y=[y_min_v, y_max_v], mode='lines', line=dict(color='#f59e0b', width=1.8, dash='dash'), name='TCĐ', hoverinfo='skip'))
            x_slant = np.linspace(x_min_v, x_max_v, 100)
            y_slant = m_slope * x_slant + n_intercept
            fig.add_trace(go.Scatter(x=x_slant, y=y_slant, mode='lines', line=dict(color='#ec4899', width=1.8, dash='dash'), name='TCX', hoverinfo='skip'))
            setup_pedagogical_oxy(fig, [x_min_v, x_max_v], [y_min_v, y_max_v])
            fig.update_layout(title=f"y = ({fa}x² + {fb}x + {fc}) / ({fd}x + {fe})", height=420)
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("PhanThuc21"))

        with c3:
            _render_info_panel("func_2_1", {"a": fa, "b": fb, "c": fc, "d": fd, "e": fe})

    # ========== PARABOL BẬC 2 ==========
    elif dtype in ["parabola", "func_2"]:
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Hệ số**")
            fa = st.slider("a:", -4.0, 4.0, float(data.get("a", 1.0)), 0.5, key="lab_p2_a")
            if fa == 0: fa = 1.0
            fb = st.slider("b:", -6.0, 6.0, float(data.get("b", -2.0)), 0.5, key="lab_p2_b")
            fc = st.slider("c:", -6.0, 6.0, float(data.get("c", -1.0)), 0.5, key="lab_p2_c")

        with c2:
            x_min_v, x_max_v, y_min_v, y_max_v = _auto_fit_view("parabola", {"a": fa, "b": fb, "c": fc})
            x_dinh = -fb / (2 * fa)
            y_dinh = fa * x_dinh**2 + fb * x_dinh + fc
            x_vals = np.linspace(x_min_v, x_max_v, 500)
            y_vals = fa * x_vals**2 + fb * x_vals + fc
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                      line=dict(color='#38bdf8', width=3), name='Parabol',
                                      hovertemplate=_hovertemplate_rounded(2)))
            fig.add_trace(go.Scatter(x=[x_dinh, x_dinh], y=[y_min_v, y_max_v],
                                      mode='lines', line=dict(color='#f59e0b', width=1.5, dash='dash'),
                                      name='Trục ĐX', hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=[x_dinh], y=[y_dinh], mode='markers+text',
                                      marker=dict(size=8, color='gold'),
                                      text=[f'I({x_dinh:.2f}; {y_dinh:.2f})'],
                                      textposition="top center",
                                      hovertemplate="Đỉnh I<br>x = %{x:.2f}<br>y = %{y:.2f}<extra></extra>"))
            setup_pedagogical_oxy(fig, [x_min_v, x_max_v], [y_min_v, y_max_v], equal_aspect=True)
            fig.update_layout(title=f"y = {fa}x² + {fb}x + {fc}", height=420)
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("Parabol"))

        with c3:
            _render_info_panel("parabola", {"a": fa, "b": fb, "c": fc})

    # ========== KHÔNG GIAN OXYZ — HÌNH HỘP NÉT ĐỨT ==========
    elif dtype == "oxyz":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Tọa độ điểm M**")
            mx = st.slider("x:", -4.0, 5.0, float(data.get("x", 2.0)), 0.5, key="lab_3d_x")
            my = st.slider("y:", -4.0, 5.0, float(data.get("y", 3.0)), 0.5, key="lab_3d_y")
            mz = st.slider("z:", -4.0, 5.0, float(data.get("z", 4.0)), 0.5, key="lab_3d_z")

        with c2:
            axis_min, axis_max, axis_len = -5, 5, 5
            fig = go.Figure()
            _draw_oxyz_axes(fig, axis_len, axis_min, axis_max)

            # Hình hộp nét đứt — 12 cạnh
            A, B, C = (mx, 0, 0), (0, my, 0), (0, 0, mz)
            D, E, F, M = (mx, my, 0), (mx, 0, mz), (0, my, mz), (mx, my, mz)
            edges = [((0, 0, 0), A), ((0, 0, 0), B), ((0, 0, 0), C),
                     (A, D), (A, E), (B, D), (B, F), (C, E), (C, F),
                     (D, M), (E, M), (F, M)]
            bx, by, bz = [], [], []
            for v1, v2 in edges:
                bx.extend([v1[0], v2[0], None])
                by.extend([v1[1], v2[1], None])
                bz.extend([v1[2], v2[2], None])
            fig.add_trace(go.Scatter3d(x=bx, y=by, z=bz, mode='lines',
                                       line=dict(color='#94a3b8', width=2, dash='dash'),
                                       showlegend=False, hoverinfo='skip'))

            # 3 điểm chiếu
            fig.add_trace(go.Scatter3d(x=[mx], y=[0], z=[0], mode='markers+text',
                                       marker=dict(size=6, color='#ef4444'),
                                       text=[f"({mx};0;0)"], textposition="bottom center",
                                       textfont=dict(color='#ef4444', size=10), showlegend=False, hoverinfo='skip'))
            fig.add_trace(go.Scatter3d(x=[0], y=[my], z=[0], mode='markers+text',
                                       marker=dict(size=6, color='#22c55e'),
                                       text=[f"(0;{my};0)"], textposition="bottom center",
                                       textfont=dict(color='#22c55e', size=10), showlegend=False, hoverinfo='skip'))
            fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[mz], mode='markers+text',
                                       marker=dict(size=6, color='#3b82f6'),
                                       text=[f"(0;0;{mz})"], textposition="top center",
                                       textfont=dict(color='#3b82f6', size=10), showlegend=False, hoverinfo='skip'))

            # Điểm M
            fig.add_trace(go.Scatter3d(
                x=[mx], y=[my], z=[mz], mode='markers+text',
                marker=dict(size=10, color='#38bdf8', line=dict(color='#f8fafc', width=1.5)),
                text=[f"M({mx}; {my}; {mz})"], textposition="top center",
                textfont=dict(color='#38bdf8', size=12), showlegend=False,
                hovertemplate="M<br>x = %{x:.2f}<br>y = %{y:.2f}<br>z = %{z:.2f}<extra></extra>"
            ))

            fig.update_layout(
                title="Không gian Oxyz — Hình hộp nét đứt",
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    yaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    zaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    aspectmode='cube',
                    camera=dict(eye=dict(x=1.6, y=1.6, z=1.3))
                ),
                height=460, margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("Oxyz"))

        with c3:
            st.markdown("##### 📝 Tọa độ")
            st.latex(r"M(" + f"{mx}; {my}; {mz}" + r")")
            st.markdown("##### 📐 Chiếu lên trục")
            st.markdown(f"<div style='background:rgba(239,68,68,0.10);border-left:3px solid #ef4444;padding:6px 10px;border-radius:4px;margin:4px 0;font-size:0.85rem;'>Ox: ({mx}; 0; 0)</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:rgba(34,197,94,0.10);border-left:3px solid #22c55e;padding:6px 10px;border-radius:4px;margin:4px 0;font-size:0.85rem;'>Oy: (0; {my}; 0)</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:rgba(59,130,246,0.10);border-left:3px solid #3b82f6;padding:6px 10px;border-radius:4px;margin:4px 0;font-size:0.85rem;'>Oz: (0; 0; {mz})</div>", unsafe_allow_html=True)

    # ========== MẶT PHẲNG OXYZ (MỚI) ==========
    elif dtype == "oxyz_plane":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Hệ số mặt phẳng**")
            st.caption("Ax + By + Cz + D = 0")
            A = st.slider("A:", -3.0, 3.0, float(data.get("A", 1.0)), 0.5, key="lab_mp_A")
            B = st.slider("B:", -3.0, 3.0, float(data.get("B", 2.0)), 0.5, key="lab_mp_B")
            C = st.slider("C:", -3.0, 3.0, float(data.get("C", -1.0)), 0.5, key="lab_mp_C")
            D = st.slider("D:", -8.0, 8.0, float(data.get("D", -6.0)), 0.5, key="lab_mp_D")
            show_normal = st.checkbox("Hiển thị vector pháp tuyến", value=True, key="lab_mp_normal")

        with c2:
            axis_min, axis_max, axis_len = -5, 5, 5
            fig = go.Figure()
            _draw_oxyz_axes(fig, axis_len, axis_min, axis_max)

            # Vẽ mặt phẳng: nếu |C| > 0 → z = -(Ax+By+D)/C
            try:
                if abs(C) > 1e-6:
                    xp = np.linspace(-5, 5, 20)
                    yp = np.linspace(-5, 5, 20)
                    XP, YP = np.meshgrid(xp, yp)
                    ZP = -(A * XP + B * YP + D) / C
                    ZP_clip = np.where(np.abs(ZP) > 6, np.nan, ZP)
                    fig.add_trace(go.Surface(x=XP, y=YP, z=ZP_clip,
                                             colorscale='Blues', opacity=0.65, showscale=False,
                                             name=f'{A}x+{B}y+{C}z+{D}=0',
                                             hovertemplate="x = %{x:.1f}<br>y = %{y:.1f}<br>z = %{z:.2f}<extra></extra>"))
                elif abs(B) > 1e-6:
                    xp = np.linspace(-5, 5, 20); zp = np.linspace(-5, 5, 20)
                    XP, ZP = np.meshgrid(xp, zp)
                    YP = -(A * XP + C * ZP + D) / B
                    fig.add_trace(go.Surface(x=XP, y=YP, z=ZP, colorscale='Blues', opacity=0.65, showscale=False, name='Mặt phẳng'))
                else:
                    yp = np.linspace(-5, 5, 20); zp = np.linspace(-5, 5, 20)
                    YP, ZP = np.meshgrid(yp, zp)
                    XP = -(B * YP + C * ZP + D) / A
                    fig.add_trace(go.Surface(x=XP, y=YP, z=ZP, colorscale='Blues', opacity=0.65, showscale=False, name='Mặt phẳng'))

                # Vector pháp tuyến từ tâm mặt phẳng
                if show_normal:
                    # Điểm nằm trên mặt phẳng gần O nhất
                    denom = A*A + B*B + C*C
                    if denom > 1e-9:
                        x0 = -A * D / denom; y0 = -B * D / denom; z0 = -C * D / denom
                        scale = 2.0
                        fig.add_trace(go.Scatter3d(
                            x=[x0, x0 + A*scale], y=[y0, y0 + B*scale], z=[z0, z0 + C*scale],
                            mode='lines+text', line=dict(color='#ef4444', width=6),
                            text=["", "n"], textposition="top center",
                            textfont=dict(color='#ef4444', size=14),
                            name='Vector pháp tuyến', showlegend=True, hoverinfo='skip'))
            except Exception as e:
                st.error(f"Lỗi vẽ mặt phẳng: {e}")

            fig.update_layout(
                title=f"Mặt phẳng: {A}x + {B}y + {C}z + {D} = 0",
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    yaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    zaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    aspectmode='cube',
                    camera=dict(eye=dict(x=1.6, y=1.6, z=1.3))
                ),
                height=460, margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("MatPhang"))

        with c3:
            st.markdown("##### 📝 Phương trình")
            st.latex(f"{A}x + {B}y + {C}z + {D} = 0")
            st.markdown("##### 📐 Pháp tuyến")
            st.latex(r"\vec{n} = (" + f"{A}; {B}; {C}" + r")")
            # Khoảng cách từ O
            denom = math.sqrt(A*A + B*B + C*C)
            if denom > 1e-9:
                d_O = abs(D) / denom
                st.markdown("##### 📏 Khoảng cách")
                st.latex(r"d(O, \alpha) \approx " + f"{d_O:.2f}")

    # ========== ĐƯỜNG THẲNG OXYZ (MỚI) ==========
    elif dtype == "oxyz_line":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Điểm M₀**")
            x0 = st.slider("x₀:", -4.0, 5.0, float(data.get("x0", 1.0)), 0.5, key="lab_line_x0")
            y0 = st.slider("y₀:", -4.0, 5.0, float(data.get("y0", 2.0)), 0.5, key="lab_line_y0")
            z0 = st.slider("z₀:", -4.0, 5.0, float(data.get("z0", 3.0)), 0.5, key="lab_line_z0")
            st.markdown("**⚙️ Vector chỉ phương**")
            ux = st.slider("u₁:", -3.0, 3.0, float(data.get("ux", 2.0)), 0.5, key="lab_line_ux")
            uy = st.slider("u₂:", -3.0, 3.0, float(data.get("uy", -1.0)), 0.5, key="lab_line_uy")
            uz = st.slider("u₃:", -3.0, 3.0, float(data.get("uz", 2.0)), 0.5, key="lab_line_uz")
            if abs(ux) < 1e-6 and abs(uy) < 1e-6 and abs(uz) < 1e-6:
                ux = 1.0

        with c2:
            axis_min, axis_max, axis_len = -5, 5, 5
            fig = go.Figure()
            _draw_oxyz_axes(fig, axis_len, axis_min, axis_max)

            # Đường thẳng: M₀ + t*u với t ∈ [-10, 10]
            t_vals = np.linspace(-10, 10, 100)
            xt = x0 + ux * t_vals
            yt = y0 + uy * t_vals
            zt = z0 + uz * t_vals
            # Clip trong hộp [-6, 6]
            mask = (np.abs(xt) <= 6) & (np.abs(yt) <= 6) & (np.abs(zt) <= 6)
            fig.add_trace(go.Scatter3d(
                x=xt[mask], y=yt[mask], z=zt[mask], mode='lines',
                line=dict(color='#22c55e', width=5),
                name='Đường thẳng', hovertemplate="x = %{x:.2f}<br>y = %{y:.2f}<br>z = %{z:.2f}<extra></extra>"))

            # Điểm M₀ (đỏ)
            fig.add_trace(go.Scatter3d(
                x=[x0], y=[y0], z=[z0], mode='markers+text',
                marker=dict(size=10, color='#ef4444', line=dict(color='#f8fafc', width=1.5)),
                text=[f"M₀({x0}; {y0}; {z0})"], textposition="top center",
                textfont=dict(color='#ef4444', size=11), showlegend=False,
                hovertemplate="M₀<br>x = %{x:.2f}<br>y = %{y:.2f}<br>z = %{z:.2f}<extra></extra>"))

            # Vector chỉ phương từ M₀ (vàng)
            fig.add_trace(go.Scatter3d(
                x=[x0, x0 + ux*2], y=[y0, y0 + uy*2], z=[z0, z0 + uz*2],
                mode='lines+text', line=dict(color='#fbbf24', width=5),
                text=["", "u"], textposition="top center",
                textfont=dict(color='#fbbf24', size=14),
                name='Vector chỉ phương', showlegend=True, hoverinfo='skip'))

            fig.update_layout(
                title="Đường thẳng trong không gian Oxyz",
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    yaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    zaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    aspectmode='cube',
                    camera=dict(eye=dict(x=1.6, y=1.6, z=1.3))
                ),
                height=460, margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("DuongThang"))

        with c3:
            st.markdown("##### 📝 Phương trình tham số")
            st.latex(f"x = {x0} + {ux}t")
            st.latex(f"y = {y0} + {uy}t")
            st.latex(f"z = {z0} + {uz}t")
            st.markdown("##### 📐 Điểm & VTCP")
            st.latex(r"M_0(" + f"{x0}; {y0}; {z0}" + r")")
            st.latex(r"\vec{{u}} = (" + f"{ux}; {uy}; {uz}" + r")")

    # ========== MẶT CẦU OXYZ (MỚI) ==========
    elif dtype == "oxyz_sphere":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Tâm I**")
            Ix = st.slider("xᵢ:", -3.0, 3.0, float(data.get("Ix", 1.0)), 0.5, key="lab_sph_Ix")
            Iy = st.slider("yᵢ:", -3.0, 3.0, float(data.get("Iy", 2.0)), 0.5, key="lab_sph_Iy")
            Iz = st.slider("zᵢ:", -3.0, 3.0, float(data.get("Iz", 3.0)), 0.5, key="lab_sph_Iz")
            R = st.slider("Bán kính R:", 0.5, 5.0, float(data.get("R", 2.5)), 0.5, key="lab_sph_R")

        with c2:
            axis_min, axis_max, axis_len = -6, 6, 6
            fig = go.Figure()
            _draw_oxyz_axes(fig, 5, axis_min, axis_max)

            # Mặt cầu tham số
            u_sph = np.linspace(0, 2 * np.pi, 40)
            v_sph = np.linspace(0, np.pi, 30)
            U_sph, V_sph = np.meshgrid(u_sph, v_sph)
            X_sph = Ix + R * np.cos(U_sph) * np.sin(V_sph)
            Y_sph = Iy + R * np.sin(U_sph) * np.sin(V_sph)
            Z_sph = Iz + R * np.cos(V_sph)
            fig.add_trace(go.Surface(x=X_sph, y=Y_sph, z=Z_sph,
                                     colorscale='Blues', opacity=0.55, showscale=False,
                                     name=f'Mặt cầu (I; R={R})',
                                     hovertemplate="x = %{x:.2f}<br>y = %{y:.2f}<br>z = %{z:.2f}<extra></extra>"))

            # Tâm I (đỏ)
            fig.add_trace(go.Scatter3d(
                x=[Ix], y=[Iy], z=[Iz], mode='markers+text',
                marker=dict(size=10, color='#ef4444', line=dict(color='#f8fafc', width=1.5)),
                text=[f"I({Ix}; {Iy}; {Iz})"], textposition="top center",
                textfont=dict(color='#ef4444', size=11), showlegend=False,
                hovertemplate="Tâm I<br>x = %{x:.2f}<br>y = %{y:.2f}<br>z = %{z:.2f}<extra></extra>"))

            fig.update_layout(
                title=f"Mặt cầu tâm I({Ix}; {Iy}; {Iz}), R = {R}",
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    yaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    zaxis=dict(range=[axis_min, axis_max], backgroundcolor="#0f172a",
                               showgrid=True, gridcolor="#1e293b", zeroline=False, showticklabels=True),
                    aspectmode='cube',
                    camera=dict(eye=dict(x=1.6, y=1.6, z=1.3))
                ),
                height=460, margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config("MatCau"))

        with c3:
            st.markdown("##### 📝 Phương trình")
            st.latex(r"(x - " + f"{Ix}" + r")^2 + (y - " + f"{Iy}" + r")^2 + (z - " + f"{Iz}" + r")^2 = " + f"{R*R:.2f}")
            st.markdown("##### 📐 Tâm & Bán kính")
            st.latex(r"I(" + f"{Ix}; {Iy}; {Iz}" + r")")
            st.latex(r"R = " + f"{R}")
            st.markdown("##### 📏 Diện tích & Thể tích")
            st.latex(r"S = 4\pi R^2 \approx " + f"{4 * math.pi * R * R:.2f}")
            st.latex(r"V = \frac{{4}}{{3}}\pi R^3 \approx " + f"{4/3 * math.pi * R**3:.2f}")

    # ========== VẬT LÝ: CON LẮC ĐƠN ==========
    elif dtype == "pendulum":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            L = st.slider("Chiều dài L (m):", 0.5, 3.0, float(data.get("L", 1.0)), 0.1, key="ly_pend_L")
            theta0_deg = st.slider("Góc ban đầu θ₀ (°):", 5, 60, float(data.get("theta0", 30.0)), 1.0, key="ly_pend_th0")
            g = st.slider("Gia tốc g (m/s²):", 1.6, 20.0, float(data.get("g", 9.8)), 0.1, key="ly_pend_g")

        theta0 = np.radians(theta0_deg)
        omega = np.sqrt(g / L)  # tần số góc (rad/s)
        T = 2 * np.pi / omega

        with c2:
            try:
                # Vẽ khung: dây + quả cầu + cung quỹ đạo
                pivot_x, pivot_y = 0, 0
                # Vị trí tại θ₀
                bob_x = L * np.sin(theta0)
                bob_y = -L * np.cos(theta0)

                fig = go.Figure()
                # Cung quỹ đạo (nét đứt)
                theta_arc = np.linspace(-theta0, theta0, 60)
                arc_x = L * np.sin(theta_arc)
                arc_y = -L * np.cos(theta_arc)
                fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode='lines',
                    line=dict(color='#94a3b8', width=1.5, dash='dot'),
                    name='Quỹ đạo', hoverinfo='skip'))
                # Dây
                fig.add_trace(go.Scatter(x=[pivot_x, bob_x], y=[pivot_y, bob_y],
                    mode='lines', line=dict(color='#38bdf8', width=3),
                    name='Dây', hoverinfo='skip'))
                # Quả cầu
                fig.add_trace(go.Scatter(x=[bob_x], y=[bob_y], mode='markers+text',
                    marker=dict(size=18, color='#ef4444', line=dict(color='#f8fafc', width=2)),
                    text=[f'm = ?'], textposition='middle center',
                    textfont=dict(color='#ffffff', size=10), name='Vật nặng', hoverinfo='skip'))
                # Trục đứng (đường cân bằng)
                fig.add_trace(go.Scatter(x=[0, 0], y=[0, -L - 0.3], mode='lines',
                    line=dict(color='#475569', width=1.5, dash='dash'),
                    name='Vị trí cân bằng', hoverinfo='skip'))
                # Điểm treo
                fig.add_trace(go.Scatter(x=[pivot_x], y=[pivot_y], mode='markers',
                    marker=dict(size=10, color='#fbbf24', symbol='square'),
                    name='Điểm treo', hoverinfo='skip'))
                # Cung góc
                fig.add_annotation(x=0.1, y=-0.1, ax=0, ay=0,
                    xref='x', yref='y', axref='x', ayref='y',
                    text=f"θ₀ = {theta0_deg}°", showarrow=False,
                    font=dict(color='#fbbf24', size=12))

                fig.update_layout(
                    title=f"Con lắc đơn — L = {L} m, g = {g} m/s²",
                    template="plotly_dark",
                    xaxis=dict(range=[-L*1.2, L*1.2], scaleanchor='y', scaleratio=1,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showticklabels=False),
                    yaxis=dict(range=[-L*1.2, 0.3], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False, showticklabels=False),
                    height=460, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ConLacDon"))
            except Exception as err:
                st.error(f"Lỗi vẽ con lắc: {err}")

        with c3:
            st.markdown("##### 📐 Chu kỳ")
            st.latex(r"T = 2\pi\sqrt{\dfrac{L}{g}} \approx " + f"{T:.3f}\\,s")
            st.markdown("##### 🔄 Tần số")
            st.latex(r"f = \dfrac{1}{T} \approx " + f"{1/T:.3f}\\,Hz")
            st.markdown("##### 📐 Tần số góc")
            st.latex(r"\omega = \sqrt{\dfrac{g}{L}} \approx " + f"{omega:.3f}\\,rad/s")

    # ========== VẬT LÝ: CON LẮC LÒ XO ==========
    elif dtype == "spring":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            m = st.slider("Khối lượng m (kg):", 0.1, 5.0, float(data.get("m", 1.0)), 0.1, key="ly_spring_m")
            k = st.slider("Độ cứng k (N/m):", 5.0, 200.0, float(data.get("k", 50.0)), 5.0, key="ly_spring_k")
            A = st.slider("Biên độ A (m):", 0.05, 0.5, float(data.get("A", 0.2)), 0.05, key="ly_spring_A")

        omega = np.sqrt(k / m)
        T = 2 * np.pi / omega

        with c2:
            try:
                fig = go.Figure()
                # Trục Ox ngang
                x_max = A * 2.5
                fig.add_trace(go.Scatter(x=[-x_max, x_max], y=[0, 0], mode='lines',
                    line=dict(color='#cbd5e1', width=1.5), name='Trục Ox', hoverinfo='skip'))
                # Điểm cân bằng O
                fig.add_trace(go.Scatter(x=[0], y=[0.3], mode='text', text=['O'],
                    textfont=dict(color='#94a3b8', size=14), showlegend=False, hoverinfo='skip'))
                # Vẽ lò xo tại vị trí x = A (nén/giãn)
                n_coils = 8
                x_spring = np.linspace(-A, 0, n_coils * 10)
                y_spring = 0.08 * np.sin((x_spring + A) / (2 * A) * n_coils * 2 * np.pi)
                fig.add_trace(go.Scatter(x=x_spring, y=y_spring, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='Lò xo', hoverinfo='skip'))
                # Vật nặng
                fig.add_trace(go.Scatter(x=[-A], y=[0], mode='markers',
                    marker=dict(size=30, color='#ef4444', symbol='square',
                                line=dict(color='#f8fafc', width=2)),
                    name=f'Vật (m = {m} kg)', hoverinfo='skip'))
                # Đường biên âm
                fig.add_trace(go.Scatter(x=[-2*A, -2*A], y=[-0.3, 0.3], mode='lines',
                    line=dict(color='#475569', width=1, dash='dash'), showlegend=False, hoverinfo='skip'))
                # Đường biên dương
                fig.add_trace(go.Scatter(x=[A, A], y=[-0.3, 0.3], mode='lines',
                    line=dict(color='#475569', width=1, dash='dash'), showlegend=False, hoverinfo='skip'))
                # Đánh dấu biên
                fig.add_annotation(x=-A, y=0.35, text=f"x = -A", showarrow=False,
                    font=dict(color='#fbbf24', size=11))
                fig.add_annotation(x=A, y=0.35, text=f"x = +A", showarrow=False,
                    font=dict(color='#fbbf24', size=11))

                fig.update_layout(
                    title=f"Con lắc lò xo — m = {m} kg, k = {k} N/m",
                    template="plotly_dark",
                    xaxis=dict(range=[-x_max, x_max], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False, showticklabels=False),
                    yaxis=dict(range=[-0.5, 0.5], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False, showticklabels=False),
                    height=300, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ConLacLoXo"))
            except Exception as err:
                st.error(f"Lỗi vẽ lò xo: {err}")

        with c3:
            st.markdown("##### 📐 Chu kỳ")
            st.latex(r"T = 2\pi\sqrt{\dfrac{m}{k}} \approx " + f"{T:.3f}\\,s")
            st.markdown("##### 🔄 Tần số")
            st.latex(r"f = \dfrac{1}{T} \approx " + f"{1/T:.3f}\\,Hz")
            st.markdown("##### 📐 Tần số góc")
            st.latex(r"\omega = \sqrt{\dfrac{k}{m}} \approx " + f"{omega:.3f}\\,rad/s")

    # ========== VẬT LÝ: ĐỒ THỊ DAO ĐỘNG ĐIỀU HÒA x, v, a ==========
    elif dtype == "shm_graph":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            A = st.slider("Biên độ A:", 0.5, 5.0, float(data.get("A", 2.0)), 0.5, key="ly_shm_A")
            omega = st.slider("Tần số góc ω (rad/s):", 0.5, 5.0, float(data.get("omega", 2.0)), 0.5, key="ly_shm_w")
            phi_deg = st.slider("Pha ban đầu φ (°):", 0, 360, float(data.get("phi", 0.0)), 15.0, key="ly_shm_phi")
            show_v = st.checkbox("Hiển thị vận tốc v(t)", value=True, key="ly_shm_showv")
            show_a = st.checkbox("Hiển thị gia tốc a(t)", value=True, key="ly_shm_showa")

        phi = np.radians(phi_deg)
        T = 2 * np.pi / omega
        t = np.linspace(0, 2 * T, 500)
        x = A * np.cos(omega * t + phi)
        v = -A * omega * np.sin(omega * t + phi)
        a = -A * omega**2 * np.cos(omega * t + phi)

        with c2:
            try:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=t, y=x, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='x(t)',
                    hovertemplate="t = %{x:.2f}s<br>x = %{y:.2f}<extra></extra>"))
                if show_v:
                    fig.add_trace(go.Scatter(x=t, y=v, mode='lines',
                        line=dict(color='#34d399', width=2.5), name='v(t)',
                        hovertemplate="t = %{x:.2f}s<br>v = %{y:.2f}<extra></extra>"))
                if show_a:
                    fig.add_trace(go.Scatter(x=t, y=a, mode='lines',
                        line=dict(color='#f43f5e', width=2.5), name='a(t)',
                        hovertemplate="t = %{x:.2f}s<br>a = %{y:.2f}<extra></extra>"))
                # Trục y=0
                fig.add_hline(y=0, line=dict(color='#475569', width=1, dash='dash'))
                fig.update_layout(
                    title=f"Dao động điều hòa — A = {A}, ω = {omega} rad/s, φ = {phi_deg}°",
                    template="plotly_dark",
                    xaxis=dict(title="t (s)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="x, v, a", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("DaoDongDH"))
            except Exception as err:
                st.error(f"Lỗi vẽ đồ thị SHM: {err}")

        with c3:
            st.markdown("##### 📐 Chu kỳ")
            st.latex(r"T = \dfrac{2\pi}{\omega} \approx " + f"{T:.3f}\\,s")
            st.markdown("##### 📈 Vận tốc cực đại")
            st.latex(r"v_{max} = A\omega \approx " + f"{A*omega:.2f}")
            st.markdown("##### 📉 Gia tốc cực đại")
            st.latex(r"a_{max} = A\omega^2 \approx " + f"{A*omega**2:.2f}")

    # ========== VẬT LÝ: CHUYỂN ĐỘNG NÉM XIÊN ==========
    elif dtype == "projectile":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            v0 = st.slider("Vận tốc ban đầu v₀ (m/s):", 5.0, 50.0, float(data.get("v0", 20.0)), 1.0, key="ly_proj_v0")
            alpha_deg = st.slider("Góc ném α (°):", 15, 85, float(data.get("alpha", 45.0)), 5.0, key="ly_proj_a")
            g = st.slider("Gia tốc g (m/s²):", 1.6, 20.0, float(data.get("g", 9.8)), 0.1, key="ly_proj_g")

        alpha = np.radians(alpha_deg)
        v0x = v0 * np.cos(alpha)
        v0y = v0 * np.sin(alpha)
        t_flight = 2 * v0y / g
        x_max = v0x * t_flight
        y_max = v0y**2 / (2 * g)

        with c2:
            try:
                t_vals = np.linspace(0, t_flight, 200)
                x_vals = v0x * t_vals
                y_vals = v0y * t_vals - 0.5 * g * t_vals**2

                fig = go.Figure()
                # Quỹ đạo parabol
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='Quỹ đạo',
                    hovertemplate="x = %{x:.2f}m<br>y = %{y:.2f}m<extra></extra>"))
                # Điểm đầu
                fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers+text',
                    marker=dict(size=10, color='#34d399', line=dict(color='#f8fafc', width=1.5)),
                    text=['Điểm ném'], textposition='bottom right',
                    textfont=dict(color='#34d399', size=11), showlegend=False, hoverinfo='skip'))
                # Điểm cao nhất
                fig.add_trace(go.Scatter(x=[x_max/2], y=[y_max], mode='markers+text',
                    marker=dict(size=10, color='#fbbf24', line=dict(color='#f8fafc', width=1.5)),
                    text=[f'Đỉnh ({x_max/2:.1f}; {y_max:.1f})'], textposition='top center',
                    textfont=dict(color='#fbbf24', size=11), showlegend=False, hoverinfo='skip'))
                # Điểm rơi
                fig.add_trace(go.Scatter(x=[x_max], y=[0], mode='markers+text',
                    marker=dict(size=10, color='#ef4444', line=dict(color='#f8fafc', width=1.5)),
                    text=[f'Rơi ({x_max:.1f}; 0)'], textposition='bottom left',
                    textfont=dict(color='#ef4444', size=11), showlegend=False, hoverinfo='skip'))
                # Vector v0 tại điểm ném
                fig.add_annotation(x=v0x*0.3, y=v0y*0.3, ax=0, ay=0,
                    xref='x', yref='y', axref='x', ayref='y',
                    text='v₀', showarrow=True, arrowhead=2, arrowsize=1.5,
                    arrowwidth=2.5, arrowcolor='#22c55e',
                    font=dict(color='#22c55e', size=14))

                fig.update_layout(
                    title=f"Ném xiên — v₀ = {v0} m/s, α = {alpha_deg}°, g = {g} m/s²",
                    template="plotly_dark",
                    xaxis=dict(title="x (m)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="y (m)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("NemXien"))
            except Exception as err:
                st.error(f"Lỗi vẽ ném xiên: {err}")

        with c3:
            st.markdown("##### ⏱ Thời gian bay")
            st.latex(r"t = \dfrac{2v_0\sin\alpha}{g} \approx " + f"{t_flight:.2f}\\,s")
            st.markdown("##### 📏 Tầm bay xa")
            st.latex(r"L = \dfrac{v_0^2\sin 2\alpha}{g} \approx " + f"{x_max:.2f}\\,m")
            st.markdown("##### 📈 Độ cao cực đại")
            st.latex(r"H = \dfrac{v_0^2\sin^2\alpha}{2g} \approx " + f"{y_max:.2f}\\,m")

    # ========== VẬT LÝ: CHUYỂN ĐỘNG TRÒN ĐỀU ==========
    elif dtype == "circular_motion":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            R = st.slider("Bán kính R (m):", 0.5, 5.0, float(data.get("R", 2.0)), 0.5, key="ly_circ_R")
            omega = st.slider("Tốc độ góc ω (rad/s):", 0.5, 5.0, float(data.get("omega", 2.0)), 0.5, key="ly_circ_w")
            theta_deg = st.slider("Góc hiện tại θ (°):", 0, 360, float(data.get("theta", 45.0)), 15.0, key="ly_circ_theta")

        theta = np.radians(theta_deg)
        v = omega * R          # vận tốc dài
        a_ht = omega**2 * R    # gia tốc hướng tâm
        T = 2 * np.pi / omega

        with c2:
            try:
                fig = go.Figure()
                # Đường tròn quỹ đạo
                t_circ = np.linspace(0, 2 * np.pi, 100)
                fig.add_trace(go.Scatter(x=R*np.cos(t_circ), y=R*np.sin(t_circ),
                    mode='lines', line=dict(color='#38bdf8', width=2.5, dash='dash'),
                    name='Quỹ đạo tròn', hoverinfo='skip'))
                # Tâm O
                fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers+text',
                    marker=dict(size=8, color='#f8fafc'),
                    text=['O'], textposition='bottom left',
                    textfont=dict(color='#f8fafc', size=14), showlegend=False, hoverinfo='skip'))
                # Bán kính đến vật
                x_obj = R * np.cos(theta)
                y_obj = R * np.sin(theta)
                fig.add_trace(go.Scatter(x=[0, x_obj], y=[0, y_obj], mode='lines',
                    line=dict(color='#94a3b8', width=1.5, dash='dot'),
                    name='Bán kính R', hoverinfo='skip'))
                # Vật chuyển động
                fig.add_trace(go.Scatter(x=[x_obj], y=[y_obj], mode='markers+text',
                    marker=dict(size=15, color='#ef4444', line=dict(color='#f8fafc', width=2)),
                    text=['M'], textposition='top center',
                    textfont=dict(color='#ef4444', size=13), showlegend=False,
                    hovertemplate="M<br>x = %{x:.2f}<br>y = %{y:.2f}<extra></extra>"))
                # Vector vận tốc v (tiếp tuyến)
                v_scale = 0.3
                vx = -np.sin(theta) * v * v_scale
                vy = np.cos(theta) * v * v_scale
                fig.add_trace(go.Scatter(x=[x_obj, x_obj + vx], y=[y_obj, y_obj + vy],
                    mode='lines+text', line=dict(color='#22c55e', width=3),
                    text=['', 'v'], textposition='top right',
                    textfont=dict(color='#22c55e', size=14),
                    name='Vector v', showlegend=False, hoverinfo='skip'))
                # Vector gia tốc hướng tâm a
                a_scale = 0.15
                ax = -np.cos(theta) * a_ht * a_scale
                ay = -np.sin(theta) * a_ht * a_scale
                fig.add_trace(go.Scatter(x=[x_obj, x_obj + ax], y=[y_obj, y_obj + ay],
                    mode='lines+text', line=dict(color='#fbbf24', width=3),
                    text=['', 'a'], textposition='bottom left',
                    textfont=dict(color='#fbbf24', size=14),
                    name='Gia tốc hướng tâm', showlegend=False, hoverinfo='skip'))

                fig.update_layout(
                    title=f"Chuyển động tròn đều — R = {R} m, ω = {omega} rad/s",
                    template="plotly_dark",
                    xaxis=dict(range=[-R*1.5, R*1.5], scaleanchor='y', scaleratio=1,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showticklabels=False),
                    yaxis=dict(range=[-R*1.5, R*1.5], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False, showticklabels=False),
                    height=460, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ChuyenDongTron"))
            except Exception as err:
                st.error(f"Lỗi vẽ chuyển động tròn: {err}")

        with c3:
            st.markdown("##### ⏱ Chu kỳ")
            st.latex(r"T = \dfrac{2\pi}{\omega} \approx " + f"{T:.3f}\\,s")
            st.markdown("##### 🏃 Vận tốc dài")
            st.latex(r"v = \omega R \approx " + f"{v:.2f}\\,m/s")
            st.markdown("##### 📉 Gia tốc hướng tâm")
            st.latex(r"a_{ht} = \omega^2 R \approx " + f"{a_ht:.2f}\\,m/s^2")

    # ========== VẬT LÝ: SÓNG CƠ LAN TRUYỀN (2D) ==========
    elif dtype == "wave_2d":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            A = st.slider("Biên độ A:", 0.5, 3.0, float(data.get("A", 1.5)), 0.1, key="ly_w2d_A")
            wavelength = st.slider("Bước sóng λ (m):", 1.0, 5.0, float(data.get("wavelength", 2.0)), 0.5, key="ly_w2d_lam")
            k_wave = st.slider("Số sóng k:", 0.5, 4.0, float(data.get("k", 1.5)), 0.5, key="ly_w2d_k")
            t_snapshot = st.slider("Thời điểm t (chu kỳ):", 0.0, 2.0, float(data.get("t", 0.0)), 0.1, key="ly_w2d_t")

        with c2:
            try:
                x = np.linspace(0, 10, 400)
                # Sóng lan truyền theo Ox: u(x,t) = A cos(2π(x/λ - t))
                u = A * np.cos(2 * np.pi * (x / wavelength - t_snapshot))

                fig = go.Figure()
                # Trục Ox
                fig.add_trace(go.Scatter(x=[0, 10], y=[0, 0], mode='lines',
                    line=dict(color='#475569', width=1, dash='dash'),
                    name='Trục Ox', hoverinfo='skip'))
                # Sóng
                fig.add_trace(go.Scatter(x=x, y=u, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='Sóng',
                    hovertemplate="x = %{x:.2f}m<br>u = %{y:.2f}<extra></extra>"))
                # Đỉnh sóng (đánh dấu 1 điểm)
                i0 = len(x) // 2
                fig.add_trace(go.Scatter(x=[x[i0]], y=[u[i0]], mode='markers+text',
                    marker=dict(size=10, color='#fbbf24', line=dict(color='#f8fafc', width=1.5)),
                    text=[f'u = {u[i0]:.2f}'], textposition='top center',
                    textfont=dict(color='#fbbf24', size=11), showlegend=False, hoverinfo='skip'))

                # Mũi tên chỉ hướng truyền sóng
                fig.add_annotation(x=8, y=A + 0.5, ax=6, ay=A + 0.5,
                    xref='x', yref='y', axref='x', ayref='y',
                    text='→ v', showarrow=True, arrowhead=2, arrowsize=1.5,
                    arrowwidth=2.5, arrowcolor='#34d399',
                    font=dict(color='#34d399', size=14))

                fig.update_layout(
                    title=f"Sóng cơ lan truyền — λ = {wavelength} m, A = {A}",
                    template="plotly_dark",
                    xaxis=dict(title="x (m)", range=[0, 10], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="u (m)", range=[-A*1.5, A*1.5], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=320, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("SongCo"))
            except Exception as err:
                st.error(f"Lỗi vẽ sóng: {err}")

        with c3:
            st.markdown("##### 📐 Tần số")
            st.latex(r"f = \dfrac{v}{\lambda}")
            st.markdown("##### 🌊 Số sóng")
            st.latex(r"k = \dfrac{2\pi}{\lambda}")
            st.markdown("##### ⚡ Tốc độ")
            st.latex(r"v = \lambda \cdot f")

    # ========== VẬT LÝ: SÓNG DỪNG ==========
    elif dtype == "standing_wave":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            L_string = st.slider("Chiều dài dây L (m):", 1.0, 5.0, float(data.get("L", 2.0)), 0.5, key="ly_sw_L")
            n_nodes = st.slider("Số bó sóng:", 1, 5, int(data.get("n", 2)), 1, key="ly_sw_n")
            A = st.slider("Biên độ bụng sóng:", 0.1, 1.0, float(data.get("A", 0.5)), 0.05, key="ly_sw_A")

        with c2:
            try:
                x = np.linspace(0, L_string, 300)
                # Sóng dừng trên dây 2 đầu cố định: u(x) = A sin(nπx/L)
                u = A * np.sin(n_nodes * np.pi * x / L_string)

                fig = go.Figure()
                # Trục Ox
                fig.add_trace(go.Scatter(x=[0, L_string], y=[0, 0], mode='lines',
                    line=dict(color='#475569', width=1.5, dash='dash'),
                    name='Trục Ox', hoverinfo='skip'))
                # Sóng dừng
                fig.add_trace(go.Scatter(x=x, y=u, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='Sóng dừng',
                    hovertemplate="x = %{x:.2f}m<br>u = %{y:.2f}<extra></extra>"))
                # Nút sóng (biên độ = 0)
                x_nodes = np.linspace(0, L_string, n_nodes + 1)
                fig.add_trace(go.Scatter(x=x_nodes, y=np.zeros_like(x_nodes),
                    mode='markers+text', marker=dict(size=10, color='#ef4444',
                    line=dict(color='#f8fafc', width=1.5)),
                    text=['Nút'] * (n_nodes + 1), textposition='bottom center',
                    textfont=dict(color='#ef4444', size=10),
                    name='Nút sóng', hoverinfo='skip'))
                # Bụng sóng (điểm có biên độ = A)
                x_bụng = []
                for k_b in range(n_nodes):
                    x_bụng.append((k_b + 0.5) * L_string / n_nodes)
                y_bụng_simple = []
                for xb in x_bụng:
                    val = A * np.sin(n_nodes * np.pi * xb / L_string)
                    y_bụng_simple.append(val)
                fig.add_trace(go.Scatter(x=x_bụng, y=y_bụng_simple,
                    mode='markers+text', marker=dict(size=10, color='#fbbf24',
                    line=dict(color='#f8fafc', width=1.5)),
                    text=['Bụng'] * len(x_bụng), textposition='top center',
                    textfont=dict(color='#fbbf24', size=10),
                    name='Bụng sóng', hoverinfo='skip'))

                fig.update_layout(
                    title=f"Sóng dừng — L = {L_string} m, {n_nodes} bó sóng",
                    template="plotly_dark",
                    xaxis=dict(title="x (m)", range=[-0.2, L_string + 0.2], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="u (m)", range=[-A*1.5, A*1.5], backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=320, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("SongDung"))
            except Exception as err:
                st.error(f"Lỗi vẽ sóng dừng: {err}")

        with c3:
            st.markdown("##### 📐 Bước sóng")
            st.latex(r"\lambda = \dfrac{2L}{n} = " + f"{2*L_string/n_nodes:.3f}\\,m")
            st.markdown("##### 🔗 Điều kiện")
            st.latex(r"L = n\cdot\dfrac{\lambda}{2}")
            st.markdown("##### 📊 Số nút - bụng")
            st.markdown(f"- **Nút:** {n_nodes + 1}")
            st.markdown(f"- **Bụng:** {n_nodes}")

    # ========== VẬT LÝ: GIAO THOA SÓNG ==========
    elif dtype == "interference":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            lam = st.slider("Bước sóng λ (m):", 0.5, 3.0, float(data.get("lam", 1.0)), 0.1, key="ly_int_lam")
            d = st.slider("Khoảng cách 2 nguồn d (m):", 0.5, 5.0, float(data.get("d", 2.0)), 0.1, key="ly_int_d")
            A = st.slider("Biên độ mỗi nguồn:", 0.5, 3.0, float(data.get("A", 2.0)), 0.5, key="ly_int_A")

        with c2:
            try:
                # Vùng khảo sát
                x_grid = np.linspace(-4, 4, 200)
                y_grid = np.linspace(-4, 4, 200)
                X, Y = np.meshgrid(x_grid, y_grid)
                # 2 nguồn đặt tại (-d/2, 0) và (d/2, 0)
                S1 = (-d/2, 0)
                S2 = (d/2, 0)
                r1 = np.sqrt((X - S1[0])**2 + (Y - S1[1])**2)
                r2 = np.sqrt((X - S2[0])**2 + (Y - S2[1])**2)
                # Biên độ tổng hợp
                k = 2 * np.pi / lam
                U = A * np.cos(k * r1) + A * np.cos(k * r2)

                fig = go.Figure()
                # Heatmap giao thoa
                fig.add_trace(go.Heatmap(x=x_grid, y=y_grid, z=U,
                    colorscale='RdBu', zmid=0,
                    colorbar=dict(title="u", len=0.7),
                    hovertemplate="x = %{x:.2f}<br>y = %{y:.2f}<br>u = %{z:.2f}<extra></extra>"))
                # 2 nguồn
                fig.add_trace(go.Scatter(x=[S1[0]], y=[S1[1]], mode='markers+text',
                    marker=dict(size=15, color='#fbbf24', symbol='circle',
                    line=dict(color='#000', width=2)),
                    text=['S₁'], textposition='bottom center',
                    textfont=dict(color='#fbbf24', size=14), showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=[S2[0]], y=[S2[1]], mode='markers+text',
                    marker=dict(size=15, color='#fbbf24', symbol='circle',
                    line=dict(color='#000', width=2)),
                    text=['S₂'], textposition='bottom center',
                    textfont=dict(color='#fbbf24', size=14), showlegend=False, hoverinfo='skip'))

                fig.update_layout(
                    title=f"Giao thoa sóng — λ = {lam} m, d = {d} m",
                    template="plotly_dark",
                    xaxis=dict(title="x (m)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False, scaleanchor='y', scaleratio=1),
                    yaxis=dict(title="y (m)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=520, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("GiaoThoa"))
            except Exception as err:
                st.error(f"Lỗi vẽ giao thoa: {err}")

        with c3:
            st.markdown("##### 📐 Hiệu đường đi")
            st.latex(r"\Delta d = d_2 - d_1")
            st.markdown("##### 🟢 Cực đại giao thoa")
            st.latex(r"\Delta d = k\lambda")
            st.markdown("##### 🔴 Cực tiểu giao thoa")
            st.latex(r"\Delta d = \left(k + \dfrac{1}{2}\right)\lambda")
            st.markdown("##### 📊 Số cực đại")
            n_max = int(2 * d / lam) + 1
            st.markdown(f"Trên đoạn S₁S₂: **{n_max}** cực đại")

    # ========== VẬT LÝ: SƠ ĐỒ TIA SÁNG QUA THẤU KÍNH ==========
    elif dtype == "lens_ray":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            f = st.slider("Tiêu cự f (cm):", 5.0, 30.0, float(data.get("f", 15.0)), 1.0, key="ly_lens_f")
            d_o = st.slider("Khoảng cách vật d (cm):", 5.0, 60.0, float(data.get("d", 30.0)), 1.0, key="ly_lens_d")
            h_o = st.slider("Chiều cao vật (cm):", 1.0, 10.0, float(data.get("h", 5.0)), 0.5, key="ly_lens_h")
            lens_type = st.radio("Loại thấu kính:", ["Hội tụ", "Phân kỳ"], key="ly_lens_type")

        # Tính toán ảnh
        f_signed = f if lens_type == "Hội tụ" else -f
        # 1/f = 1/d + 1/d' → d' = f*d / (d - f)
        if abs(d_o - f_signed) < 1e-6:
            d_prime = float('inf')
        else:
            d_prime = (f_signed * d_o) / (d_o - f_signed)
        h_prime = -h_o * d_prime / d_o if d_prime != float('inf') else 0

        with c2:
            try:
                fig = go.Figure()
                # Trục chính (trục quang học)
                fig.add_trace(go.Scatter(x=[-50, 70], y=[0, 0], mode='lines',
                    line=dict(color='#475569', width=1.5, dash='dash'),
                    name='Trục chính', hoverinfo='skip'))
                # Ký hiệu thấu kính (đường thẳng đứng qua O)
                fig.add_trace(go.Scatter(x=[0, 0], y=[-15, 15], mode='lines',
                    line=dict(color='#38bdf8', width=3), name='Thấu kính', hoverinfo='skip'))
                # Mũi tên 2 đầu cho thấu kính hội tụ
                fig.add_annotation(x=0, y=15, ax=0, ay=-15, xref='x', yref='y',
                    axref='x', ayref='y', text='', showarrow=True,
                    arrowhead=2, arrowsize=1.2, arrowwidth=0)
                # Vật (mũi tên từ trục lên)
                fig.add_trace(go.Scatter(x=[-d_o, -d_o], y=[0, h_o], mode='lines',
                    line=dict(color='#34d399', width=4), name='Vật',
                    hovertemplate="Vật tại d = %{x:.1f} cm<extra></extra>"))
                fig.add_annotation(x=-d_o, y=h_o, ax=-d_o, ay=0, xref='x', yref='y',
                    axref='x', ayref='y', text='AB', showarrow=True,
                    arrowhead=2, arrowsize=1.5, arrowwidth=3, arrowcolor='#34d399',
                    font=dict(color='#34d399', size=13))
                # Tiêu điểm F và F'
                fig.add_trace(go.Scatter(x=[-f_signed, f_signed], y=[0, 0],
                    mode='markers+text',
                    marker=dict(size=8, color='#fbbf24', symbol='x'),
                    text=["F", "F'"], textposition='bottom center',
                    textfont=dict(color='#fbbf24', size=12),
                    name='Tiêu điểm', showlegend=False, hoverinfo='skip'))
                # Ảnh (nếu tồn tại và hữu hạn)
                if d_prime != float('inf') and abs(d_prime) < 100:
                    x_img = d_prime
                    fig.add_trace(go.Scatter(x=[x_img, x_img], y=[0, h_prime], mode='lines',
                        line=dict(color='#ef4444', width=4), name="Ảnh",
                        hovertemplate="Ảnh tại d' = %{x:.1f} cm<extra></extra>"))
                    fig.add_annotation(x=x_img, y=h_prime, ax=x_img, ay=0, xref='x', yref='y',
                        axref='x', ayref='y', text="A'B'", showarrow=True,
                        arrowhead=2, arrowsize=1.5, arrowwidth=3, arrowcolor='#ef4444',
                        font=dict(color='#ef4444', size=13))
                    # Tia sáng 1: từ B song song trục chính → qua F'
                    fig.add_trace(go.Scatter(x=[-d_o, 0], y=[h_o, h_o], mode='lines',
                        line=dict(color='#fbbf24', width=1.5, dash='dot'),
                        name='Tia 1', showlegend=False, hoverinfo='skip'))
                    # Tia sáng 2: từ B qua O
                    fig.add_trace(go.Scatter(x=[-d_o, x_img], y=[h_o, h_prime], mode='lines',
                        line=dict(color='#f472b6', width=1.5, dash='dot'),
                        name='Tia 2', showlegend=False, hoverinfo='skip'))

                fig.update_layout(
                    title=f"Thấu kính {lens_type} — f = {f} cm, d = {d_o} cm",
                    template="plotly_dark",
                    xaxis=dict(title="Trục chính (cm)", range=[-50, 70],
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False),
                    yaxis=dict(title="y (cm)", range=[-15, 15],
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, scaleanchor='x', scaleratio=1),
                    height=380, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ThauKinh"))
            except Exception as err:
                st.error(f"Lỗi vẽ thấu kính: {err}")

        with c3:
            st.markdown("##### 📝 Công thức thấu kính")
            st.latex(r"\dfrac{1}{f} = \dfrac{1}{d} + \dfrac{1}{d'}")
            st.markdown("##### 📏 Kết quả")
            if d_prime == float('inf'):
                st.latex(r"d' = \infty")
                st.caption("Ảnh ở vô cực")
            else:
                st.latex(r"d' = \dfrac{df}{d-f} = " + f"{d_prime:.2f}\\,cm")
                st.latex(r"h' = -\dfrac{d'}{d}\cdot h = " + f"{h_prime:.2f}\\,cm")
            st.markdown("##### 🔍 Độ phóng đại")
            if d_prime != float('inf'):
                k_mag = -d_prime / d_o
                st.latex(r"k = -\dfrac{d'}{d} = " + f"{k_mag:.2f}")

    # ========== VẬT LÝ 12: THANG SÓNG ĐIỆN TỪ ==========
    elif dtype == "em_spectrum":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            f_hz = st.slider(
                "Tần số f (Hz):",
                min_value=4.0, max_value=21.0,
                value=float(data.get("log_f", 14.0)),
                step=0.5, key="ly12_em_logf",
                help="Log₁₀(f) — từ 10⁴ Hz (vô tuyến) đến 10²¹ Hz (gamma)"
            )
            st.caption("Kéo slider để xem loại sóng tương ứng")

        # Xác định loại sóng theo tần số
        if f_hz < 9:
            band = "Sóng vô tuyến"; color = "#818cf8"; icon = "📻"
        elif f_hz < 11:
            band = "Vi ba"; color = "#60a5fa"; icon = "📡"
        elif f_hz < 13:
            band = "Hồng ngoại"; color = "#f87171"; icon = "🔥"
        elif f_hz < 14.8:
            band = "Ánh sáng khả kiến"; color = "#fbbf24"; icon = "👁️"
        elif f_hz < 16:
            band = "Tử ngoại"; color = "#a78bfa"; icon = "🟣"
        elif f_hz < 18.5:
            band = "Tia X"; color = "#c084fc"; icon = "☢️"
        else:
            band = "Tia gamma"; color = "#f43f5e"; icon = "💥"

        with c2:
            try:
                fig = go.Figure()
                # Dải phổ liên tục từ 10^4 đến 10^21 Hz
                bands_data = [
                    (4, 9, "Vô tuyến", "#818cf8"),
                    (9, 11, "Vi ba", "#60a5fa"),
                    (11, 13, "Hồng ngoại", "#f87171"),
                    (13, 14.8, "Khả kiến", "#fbbf24"),
                    (14.8, 16, "Tử ngoại", "#a78bfa"),
                    (16, 18.5, "Tia X", "#c084fc"),
                    (18.5, 21, "Gamma", "#f43f5e"),
                ]
                for x0, x1, label, col in bands_data:
                    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0, y1=1,
                                  fillcolor=col, opacity=0.65,
                                  line=dict(color='#0f172a', width=2))
                    fig.add_annotation(x=(x0+x1)/2, y=0.5, text=label,
                                       showarrow=False,
                                       font=dict(color='#0f172a', size=12, family='Times New Roman'))

                # Đường chỉ tần số hiện tại
                fig.add_shape(type="line", x0=f_hz, x1=f_hz, y0=-0.15, y1=1.15,
                              line=dict(color='#ffffff', width=3))
                fig.add_annotation(x=f_hz, y=1.25,
                                   text=f"{icon} f = 10^{f_hz:.1f} Hz",
                                   showarrow=False,
                                   font=dict(color='#ffffff', size=13))

                fig.update_layout(
                    title=f"Thang sóng điện từ — Đang chọn: {band}",
                    template="plotly_dark",
                    xaxis=dict(title="Log₁₀(Tần số) (Hz)", range=[4, 21],
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, tickfont=dict(color='#cbd5e1')),
                    yaxis=dict(range=[-0.3, 1.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    height=300, margin=dict(l=10, r=10, t=50, b=30),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ThangSongDT"))
            except Exception as err:
                st.error(f"Lỗi vẽ thang sóng: {err}")

        with c3:
            st.markdown("##### 📡 Loại sóng")
            st.markdown(f"**{icon} {band}**")
            st.markdown("##### 📐 Bước sóng")
            c_light = 3e8
            lam_m = c_light / (10 ** f_hz)
            if lam_m >= 1:
                st.latex(r"\lambda \approx " + f"{lam_m:.2e}\\,m")
            elif lam_m >= 1e-3:
                st.latex(r"\lambda \approx " + f"{lam_m*100:.2f}\\,cm")
            elif lam_m >= 1e-6:
                st.latex(r"\lambda \approx " + f"{lam_m*1e6:.2f}\\,\\mu m")
            elif lam_m >= 1e-9:
                st.latex(r"\lambda \approx " + f"{lam_m*1e9:.2f}\\,nm")
            else:
                st.latex(r"\lambda \approx " + f"{lam_m:.2e}\\,m")
            st.markdown("##### 📏 Công thức")
            st.latex(r"c = \lambda \cdot f")

    # ========== VẬT LÝ 12: MẠCH ĐIỆN ĐƠN GIẢN ==========
    elif dtype == "circuit_simple":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số mạch**")
            U = st.slider("Hiệu điện thế U (V):", 1.0, 24.0, float(data.get("U", 12.0)), 0.5, key="ly12_cir_U")
            R1 = st.slider("Điện trở R₁ (Ω):", 1.0, 20.0, float(data.get("R1", 4.0)), 0.5, key="ly12_cir_R1")
            R2 = st.slider("Điện trở R₂ (Ω):", 1.0, 20.0, float(data.get("R2", 6.0)), 0.5, key="ly12_cir_R2")
            mode = st.radio("Cách mắc:", ["Nối tiếp", "Song song"], key="ly12_cir_mode")

        if mode == "Nối tiếp":
            R_total = R1 + R2
            I_main = U / R_total
            U1 = I_main * R1
            U2 = I_main * R2
        else:  # Song song
            R_total = (R1 * R2) / (R1 + R2)
            I_main = U / R_total
            I1 = U / R1
            I2 = U / R2
            U1 = U2 = U
        P_total = U * I_main

        with c2:
            try:
                fig = go.Figure()
                # Vẽ mạch điện dạng sơ đồ khối
                # Khung mạch hình chữ nhật
                fig.add_shape(type="rect", x0=0, x1=10, y0=0, y1=5,
                              line=dict(color='#38bdf8', width=3), fillcolor='rgba(0,0,0,0)')

                if mode == "Nối tiếp":
                    # Nguồn U ở cạnh trái (dọc)
                    fig.add_shape(type="line", x0=0, x1=0, y0=1.5, y1=3.5,
                                  line=dict(color='#34d399', width=8))
                    fig.add_annotation(x=-0.6, y=2.5, text=f"U = {U}V",
                                       showarrow=False, textangle=-90,
                                       font=dict(color='#34d399', size=13))
                    # Vẽ R1 trên cạnh trên
                    fig.add_shape(type="rect", x0=2, x1=4, y0=4.3, y1=5.7,
                                  line=dict(color='#fbbf24', width=2),
                                  fillcolor='rgba(251,191,36,0.2)')
                    fig.add_annotation(x=3, y=5, text=f"R₁ = {R1}Ω",
                                       showarrow=False, font=dict(color='#fbbf24', size=12))
                    # Vẽ R2 trên cạnh trên
                    fig.add_shape(type="rect", x0=6, x1=8, y0=4.3, y1=5.7,
                                  line=dict(color='#fbbf24', width=2),
                                  fillcolor='rgba(251,191,36,0.2)')
                    fig.add_annotation(x=7, y=5, text=f"R₂ = {R2}Ω",
                                       showarrow=False, font=dict(color='#fbbf24', size=12))
                    # Mũi tên dòng điện trên cạnh trên
                    fig.add_annotation(x=5, y=5, ax=4.5, ay=5, xref='x', yref='y',
                                       axref='x', ayref='y', text='',
                                       showarrow=True, arrowhead=2, arrowsize=1.5,
                                       arrowwidth=2.5, arrowcolor='#f472b6')
                else:  # Song song
                    # Nguồn U ở cạnh trái
                    fig.add_shape(type="line", x0=0, x1=0, y0=1.5, y1=3.5,
                                  line=dict(color='#34d399', width=8))
                    fig.add_annotation(x=-0.6, y=2.5, text=f"U = {U}V",
                                       showarrow=False, textangle=-90,
                                       font=dict(color='#34d399', size=13))
                    # R1 nhánh trên
                    fig.add_shape(type="rect", x0=4, x1=6, y0=3.2, y1=4.2,
                                  line=dict(color='#fbbf24', width=2),
                                  fillcolor='rgba(251,191,36,0.2)')
                    fig.add_annotation(x=5, y=3.7, text=f"R₁ = {R1}Ω",
                                       showarrow=False, font=dict(color='#fbbf24', size=12))
                    # R2 nhánh dưới
                    fig.add_shape(type="rect", x0=4, x1=6, y0=0.8, y1=1.8,
                                  line=dict(color='#fbbf24', width=2),
                                  fillcolor='rgba(251,191,36,0.2)')
                    fig.add_annotation(x=5, y=1.3, text=f"R₂ = {R2}Ω",
                                       showarrow=False, font=dict(color='#fbbf24', size=12))
                    # Đường nối vào 2 nhánh
                    fig.add_shape(type="line", x0=2.5, x1=2.5, y0=0.3, y1=4.7,
                                  line=dict(color='#38bdf8', width=3))
                    fig.add_shape(type="line", x0=7.5, x1=7.5, y0=0.3, y1=4.7,
                                  line=dict(color='#38bdf8', width=3))

                # Nhãn "Mạch điện"
                fig.add_annotation(x=5, y=2.5, text=f"<b>Mạch {mode.lower()}</b><br>"
                                                     f"R<sub>tđ</sub> = {R_total:.2f} Ω<br>"
                                                     f"I = {I_main:.2f} A",
                                   showarrow=False,
                                   font=dict(color='#f8fafc', size=14))

                fig.update_layout(
                    title=f"Mạch điện {mode.lower()} — R₁ = {R1}Ω, R₂ = {R2}Ω",
                    template="plotly_dark",
                    xaxis=dict(range=[-2, 12], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(range=[-1, 7], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, scaleanchor='x', scaleratio=1),
                    height=380, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("MachDien"))
            except Exception as err:
                st.error(f"Lỗi vẽ mạch điện: {err}")

        with c3:
            st.markdown("##### 📐 Điện trở tương đương")
            if mode == "Nối tiếp":
                st.latex(r"R_{tđ} = R_1 + R_2 = " + f"{R_total:.2f}\\,\\Omega")
            else:
                st.latex(r"\dfrac{1}{R_{tđ}} = \dfrac{1}{R_1} + \dfrac{1}{R_2}")
                st.latex(r"R_{tđ} = " + f"{R_total:.2f}\\,\\Omega")
            st.markdown("##### ⚡ Cường độ dòng điện")
            st.latex(r"I = \dfrac{U}{R_{tđ}} = " + f"{I_main:.2f}\\,A")
            if mode == "Nối tiếp":
                st.latex(r"U_1 = " + f"{U1:.2f}\\,V")
                st.latex(r"U_2 = " + f"{U2:.2f}\\,V")
            else:
                st.latex(r"I_1 = " + f"{I1:.2f}\\,A")
                st.latex(r"I_2 = " + f"{I2:.2f}\\,A")
            st.markdown("##### 🔋 Công suất")
            st.latex(r"P = U \cdot I = " + f"{P_total:.2f}\\,W")

    # ========== VẬT LÝ 12: CHUỖI PHÓNG XẠ ==========
    elif dtype == "nuclear_decay":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            N0 = st.slider("Số hạt ban đầu N₀:", 100, 10000, int(data.get("N0", 1000)), 100, key="ly12_nd_N0")
            half_life = st.slider("Chu kỳ bán rã T₁/₂ (đơn vị thời gian):", 1.0, 10.0, float(data.get("T", 5.0)), 0.5, key="ly12_nd_T")
            t_max = st.slider("Khoảng thời gian khảo sát (× T₁/₂):", 1, 10, int(data.get("t_max", 5)), 1, key="ly12_nd_tmax")

        lam = np.log(2) / half_life
        t = np.linspace(0, t_max * half_life, 300)
        N_t = N0 * np.exp(-lam * t)
        N_con_lai = N_t
        N_phan_ra = N0 - N_t

        with c2:
            try:
                fig = go.Figure()
                # Đường N(t) còn lại
                fig.add_trace(go.Scatter(x=t, y=N_con_lai, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='N còn lại',
                    hovertemplate="t = %{x:.2f}<br>N = %{y:.1f}<extra></extra>"))
                # Đường N đã phân rã
                fig.add_trace(go.Scatter(x=t, y=N_phan_ra, mode='lines',
                    line=dict(color='#f43f5e', width=3, dash='dash'), name='N đã phân rã',
                    hovertemplate="t = %{x:.2f}<br>N = %{y:.1f}<extra></extra>"))
                # Đường N0/2
                fig.add_hline(y=N0/2, line=dict(color='#fbbf24', width=2, dash='dot'),
                              annotation_text=f"N₀/2 = {N0/2:.0f}",
                              annotation_position="right")
                # Đường dọc tại t = T1/2
                fig.add_vline(x=half_life, line=dict(color='#fbbf24', width=2, dash='dot'),
                              annotation_text=f"t = T₁/₂",
                              annotation_position="top")

                fig.update_layout(
                    title=f"Phân rã phóng xạ — N₀ = {N0}, T₁/₂ = {half_life}",
                    template="plotly_dark",
                    xaxis=dict(title="t (đơn vị thời gian)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="Số hạt N", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("PhongXa"))
            except Exception as err:
                st.error(f"Lỗi vẽ phóng xạ: {err}")

        with c3:
            st.markdown("##### 📐 Hằng số phóng xạ")
            st.latex(r"\lambda = \dfrac{\ln 2}{T_{1/2}} \approx " + f"{lam:.4f}")
            st.markdown("##### 📈 Định luật phân rã")
            st.latex(r"N(t) = N_0 \cdot e^{-\lambda t}")
            st.markdown("##### ⏱ Tại t = T₁/₂")
            st.latex(r"N(T_{1/2}) = \dfrac{N_0}{2} = " + f"{N0/2:.0f}")
            st.markdown("##### 📊 Tại t = " + f"{t_max}" + " × T₁/₂")
            t_final = t_max * half_life
            N_final = N0 * np.exp(-lam * t_final)
            st.latex(r"N = " + f"{N_final:.1f}" + r"\text{ hạt}")

    # ========== HÓA HỌC: BẢNG TUẦN HOÀN ==========
    elif dtype == "periodic_table":
        st.markdown("### ⚗️ Bảng tuần hoàn các nguyên tố hóa học")
        st.caption("Hover để xem chi tiết · Click vào nguyên tố để xem thông tin")

        # Compact data: (số hiệu, ký hiệu, tên Việt, nhóm, chu kỳ, loại)
        # Loại: klk (kim loại kiềm), klkt (kiềm thổ), klcg (chuyển tiếp),
        #       kl (kim loại), al (á kim), pk (phi kim), hl (halogen),
        #       kh (khí hiếm), lan (lanthanide), act (actinide)
        ELEMENTS = [
            (1,"H","Hydro",1,1,"pk"),(2,"He","Heli",18,1,"kh"),
            (3,"Li","Liti",1,2,"klk"),(4,"Be","Beri",2,2,"klkt"),
            (5,"B","Bo",13,2,"al"),(6,"C","Cacbon",14,2,"pk"),
            (7,"N","Nitơ",15,2,"pk"),(8,"O","Oxi",16,2,"pk"),
            (9,"F","Flo",17,2,"hl"),(10,"Ne","Neon",18,2,"kh"),
            (11,"Na","Natri",1,3,"klk"),(12,"Mg","Magie",2,3,"klkt"),
            (13,"Al","Nhôm",13,3,"kl"),(14,"Si","Silic",14,3,"al"),
            (15,"P","Photpho",15,3,"pk"),(16,"S","Lưu huỳnh",16,3,"pk"),
            (17,"Cl","Clo",17,3,"hl"),(18,"Ar","Argon",18,3,"kh"),
            (19,"K","Kali",1,4,"klk"),(20,"Ca","Canxi",2,4,"klkt"),
            (21,"Sc","Scandi",3,4,"klcg"),(22,"Ti","Titan",4,4,"klcg"),
            (23,"V","Vanadi",5,4,"klcg"),(24,"Cr","Crom",6,4,"klcg"),
            (25,"Mn","Mangan",7,4,"klcg"),(26,"Fe","Sắt",8,4,"klcg"),
            (27,"Co","Coban",9,4,"klcg"),(28,"Ni","Niken",10,4,"klcg"),
            (29,"Cu","Đồng",11,4,"klcg"),(30,"Zn","Kẽm",12,4,"klcg"),
            (31,"Ga","Gali",13,4,"kl"),(32,"Ge","Gecmani",14,4,"al"),
            (33,"As","Asen",15,4,"al"),(34,"Se","Selen",16,4,"pk"),
            (35,"Br","Brom",17,4,"hl"),(36,"Kr","Kripton",18,4,"kh"),
            (37,"Rb","Rubidi",1,5,"klk"),(38,"Sr","Stronti",2,5,"klkt"),
            (39,"Y","Ytri",3,5,"klcg"),(40,"Zr","Ziriconi",4,5,"klcg"),
            (41,"Nb","Niobi",5,5,"klcg"),(42,"Mo","Molypden",6,5,"klcg"),
            (43,"Tc","Tecneti",7,5,"klcg"),(44,"Ru","Rutheni",8,5,"klcg"),
            (45,"Rh","Rhodi",9,5,"klcg"),(46,"Pd","Paladi",10,5,"klcg"),
            (47,"Ag","Bạc",11,5,"klcg"),(48,"Cd","Cadmi",12,5,"klcg"),
            (49,"In","Indi",13,5,"kl"),(50,"Sn","Thiếc",14,5,"kl"),
            (51,"Sb","Antimon",15,5,"al"),(52,"Te","Telu",16,5,"al"),
            (53,"I","Iot",17,5,"hl"),(54,"Xe","Xenon",18,5,"kh"),
            (55,"Cs","Xesi",1,6,"klk"),(56,"Ba","Bari",2,6,"klkt"),
            (57,"La","Lantan",3,6,"lan"),(72,"Hf","Hafni",4,6,"klcg"),
            (73,"Ta","Tantal",5,6,"klcg"),(74,"W","Vonfram",6,6,"klcg"),
            (75,"Re","Rheni",7,6,"klcg"),(76,"Os","Osmi",8,6,"klcg"),
            (77,"Ir","Iridi",9,6,"klcg"),(78,"Pt","Platin",10,6,"klcg"),
            (79,"Au","Vàng",11,6,"klcg"),(80,"Hg","Thủy ngân",12,6,"klcg"),
            (81,"Tl","Tali",13,6,"kl"),(82,"Pb","Chì",14,6,"kl"),
            (83,"Bi","Bitmut",15,6,"kl"),(84,"Po","Poloni",16,6,"al"),
            (85,"At","Astatin",17,6,"hl"),(86,"Rn","Radon",18,6,"kh"),
            (87,"Fr","Franxi",1,7,"klk"),(88,"Ra","Radi",2,7,"klkt"),
            (89,"Ac","Actini",3,7,"act"),(104,"Rf","Rutherfordi",4,7,"klcg"),
            (105,"Db","Dubni",5,7,"klcg"),(106,"Sg","Seaborgi",6,7,"klcg"),
            (107,"Bh","Bohri",7,7,"klcg"),(108,"Hs","Hassi",8,7,"klcg"),
            (109,"Mt","Meitneri",9,7,"klcg"),(110,"Ds","Darmstadti",10,7,"klcg"),
            (111,"Rg","Roentgeni",11,7,"klcg"),(112,"Cn","Copernici",12,7,"klcg"),
            (113,"Nh","Nihoni",13,7,"kl"),(114,"Fl","Flerovi",14,7,"kl"),
            (115,"Mc","Moscovi",15,7,"kl"),(116,"Lv","Livermori",16,7,"kl"),
            (117,"Ts","Tennessine",17,7,"hl"),(118,"Og","Oganesson",18,7,"kh"),
        ]
        # Lanthanide + Actinide (tách riêng, hiển thị 2 hàng dưới)
        LANTHANIDE = [
            (57,"La","Lantan"),(58,"Ce","Xeri"),(59,"Pr","Praseodymi"),(60,"Nd","Neodymi"),
            (61,"Pm","Promethi"),(62,"Sm","Samari"),(63,"Eu","Europi"),(64,"Gd","Gadolini"),
            (65,"Tb","Terbi"),(66,"Dy","Dysprosi"),(67,"Ho","Holmi"),(68,"Er","Erbi"),
            (69,"Tm","Thuli"),(70,"Yb","Ytterbi"),(71,"Lu","Luteti"),
        ]
        ACTINIDE = [
            (89,"Ac","Actini"),(90,"Th","Thori"),(91,"Pa","Protactini"),(92,"U","Urani"),
            (93,"Np","Neptuni"),(94,"Pu","Plutoni"),(95,"Am","Americi"),(96,"Cm","Curi"),
            (97,"Bk","Berkeli"),(98,"Cf","Californi"),(99,"Es","Einsteini"),(100,"Fm","Fermi"),
            (101,"Md","Mendelevi"),(102,"No","Nobeli"),(103,"Lr","Lawrenci"),
        ]

        CATEGORY_COLORS = {
            "klk": "#f87171", "klkt": "#fb923c", "klcg": "#fbbf24",
            "kl": "#a3e635", "al": "#34d399", "pk": "#38bdf8",
            "hl": "#a78bfa", "kh": "#f472b6", "lan": "#fcd34d", "act": "#fbcfe8",
        }

        with st.expander("🎨 Chú thích màu sắc", expanded=False):
            cols_leg = st.columns(5)
            legend_items = [
                ("Kim loại kiềm", "#f87171"),
                ("Kim loại kiềm thổ", "#fb923c"),
                ("Kim loại chuyển tiếp", "#fbbf24"),
                ("Kim loại", "#a3e635"),
                ("Á kim", "#34d399"),
            ]
            for i, (name, col) in enumerate(legend_items):
                with cols_leg[i]:
                    st.markdown(
                        f"<div style='background:{col};padding:6px 10px;border-radius:6px;"
                        f"color:#0f172a;font-weight:700;font-size:12px;text-align:center;'>"
                        f"{name}</div>", unsafe_allow_html=True)
            cols_leg2 = st.columns(5)
            legend_items2 = [
                ("Phi kim", "#38bdf8"),
                ("Halogen", "#a78bfa"),
                ("Khí hiếm", "#f472b6"),
                ("Lanthanide", "#fcd34d"),
                ("Actinide", "#fbcfe8"),
            ]
            for i, (name, col) in enumerate(legend_items2):
                with cols_leg2[i]:
                    st.markdown(
                        f"<div style='background:{col};padding:6px 10px;border-radius:6px;"
                        f"color:#0f172a;font-weight:700;font-size:12px;text-align:center;'>"
                        f"{name}</div>", unsafe_allow_html=True)

        # Vẽ bảng bằng HTML grid
        html = '<div style="overflow-x:auto;">'
        html += '<table style="border-collapse:collapse;margin:12px 0;">'
        # 7 hàng × 18 cột
        grid = {}
        for num, sym, name_vi, grp, per, cat in ELEMENTS:
            if per <= 7:
                grid[(per, grp)] = (num, sym, name_vi, cat)
        for per in range(1, 8):
            html += '<tr>'
            for grp in range(1, 19):
                if (per, grp) in grid:
                    num, sym, name_vi, cat = grid[(per, grp)]
                    color = CATEGORY_COLORS.get(cat, "#94a3b8")
                    html += (
                        f'<td style="padding:2px;">'
                        f'<div style="background:{color};color:#0f172a;width:52px;height:52px;'
                        f'border-radius:6px;display:flex;flex-direction:column;'
                        f'align-items:center;justify-content:center;font-weight:700;'
                        f'font-family:system-ui;cursor:pointer;transition:transform 0.2s;" '
                        f'title="{sym} — {name_vi} (Z={num})">'
                        f'<div style="font-size:10px;line-height:1;">{num}</div>'
                        f'<div style="font-size:16px;line-height:1.2;">{sym}</div>'
                        f'<div style="font-size:8px;line-height:1;opacity:0.8;">{name_vi[:6]}</div>'
                        f'</div></td>'
                    )
                else:
                    html += '<td style="padding:2px;"></td>'
            html += '</tr>'
        # 2 hàng Lanthanide + Actinide
        html += '<tr><td colspan="18" style="height:8px;"></td></tr>'
        for label, row in [("La-Lu (Lanthanide)", LANTHANIDE), ("Ac-Lr (Actinide)", ACTINIDE)]:
            html += '<tr>'
            html += f'<td colspan="2" style="color:#fcd34d;font-size:11px;font-weight:700;'
            html += f'vertical-align:middle;padding-right:6px;">{label}</td>'
            for i, (num, sym, name_vi) in enumerate(row):
                cat = "lan" if "La" in label else "act"
                color = CATEGORY_COLORS[cat]
                html += (
                    f'<td style="padding:2px;">'
                    f'<div style="background:{color};color:#0f172a;width:44px;height:44px;'
                    f'border-radius:6px;display:flex;flex-direction:column;'
                    f'align-items:center;justify-content:center;font-weight:700;'
                    f'font-family:system-ui;" title="{sym} — {name_vi} (Z={num})">'
                    f'<div style="font-size:9px;line-height:1;">{num}</div>'
                    f'<div style="font-size:14px;line-height:1.2;">{sym}</div>'
                    f'</div></td>'
                )
            html += '<td colspan="3"></td></tr>'
        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)

        st.caption(f"📊 Tổng cộng **118 nguyên tố** đã được hiển thị")

    # ========== HÓA HỌC: SƠ ĐỒ NĂNG LƯỢNG PHẢN ỨNG ==========
    elif dtype == "energy_diagram":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            e_reactant = st.slider("Năng lượng chất đầu E₁ (kJ):", 0.0, 100.0,
                                    float(data.get("e1", 30.0)), 5.0, key="hoa_ed_e1")
            e_product = st.slider("Năng lượng sản phẩm E₂ (kJ):", 0.0, 100.0,
                                   float(data.get("e2", 70.0)), 5.0, key="hoa_ed_e2")
            e_activated = st.slider("Năng lượng hoạt hóa Ea (kJ):", 5.0, 80.0,
                                     float(data.get("ea", 40.0)), 5.0, key="hoa_ed_ea")

        delta_h = e_product - e_reactant
        is_exo = delta_h < 0

        with c2:
            try:
                fig = go.Figure()
                # Trục tung: năng lượng
                # Đường phản ứng: E1 → đỉnh (E1+Ea) → E2
                x_vals = [0, 1, 2, 3, 4, 5, 6, 7]
                y_vals = [
                    e_reactant, e_reactant,      # Chất đầu
                    e_reactant + e_activated,    # Đỉnh (phức hoạt hóa)
                    e_reactant + e_activated,    # Đỉnh
                    e_product, e_product,        # Sản phẩm
                    e_product, e_product,
                ]
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                    line=dict(color='#38bdf8', width=3, shape='spline'),
                    name='Đường phản ứng', hoverinfo='skip'))

                # Đường ngang E1
                fig.add_trace(go.Scatter(x=[0, 7], y=[e_reactant, e_reactant],
                    mode='lines', line=dict(color='#34d399', width=1.5, dash='dash'),
                    name=f'E(chất đầu) = {e_reactant} kJ', hoverinfo='skip'))
                # Đường ngang E2
                fig.add_trace(go.Scatter(x=[0, 7], y=[e_product, e_product],
                    mode='lines', line=dict(color='#f43f5e', width=1.5, dash='dash'),
                    name=f'E(sản phẩm) = {e_product} kJ', hoverinfo='skip'))
                # Mũi tên Ea
                fig.add_annotation(x=3.5, y=e_reactant, ax=3.5, ay=e_reactant + e_activated,
                    xref='x', yref='y', axref='x', ayref='y',
                    text=f'Ea = {e_activated} kJ', showarrow=True, arrowhead=2,
                    arrowsize=1.5, arrowwidth=2, arrowcolor='#fbbf24',
                    font=dict(color='#fbbf24', size=12))
                # Mũi tên ΔH
                fig.add_annotation(x=6.5, y=e_reactant, ax=6.5, ay=e_product,
                    xref='x', yref='y', axref='x', ayref='y',
                    text=f'ΔH = {delta_h:+.0f} kJ', showarrow=True, arrowhead=2,
                    arrowsize=1.5, arrowwidth=2,
                    arrowcolor='#a78bfa' if is_exo else '#f472b6',
                    font=dict(color='#a78bfa' if is_exo else '#f472b6', size=12))

                fig.update_layout(
                    title=f"Sơ đồ năng lượng — {'Tỏa nhiệt' if is_exo else 'Thu nhiệt'} phản ứng",
                    template="plotly_dark",
                    xaxis=dict(title="Tiến trình phản ứng", range=[-0.3, 7.3],
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showticklabels=False),
                    yaxis=dict(title="Năng lượng (kJ)", range=[min(0, e_product-10), 
                               max(e_reactant, e_product) + e_activated + 10],
                               backgroundcolor="#0f172a", gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("SoDoNangLuong"))
            except Exception as err:
                st.error(f"Lỗi vẽ sơ đồ năng lượng: {err}")

        with c3:
            st.markdown("##### 📝 Loại phản ứng")
            if is_exo:
                st.markdown("🔴 **Tỏa nhiệt** (ΔH < 0)")
                st.caption("Giải phóng năng lượng ra môi trường")
            else:
                st.markdown("🔵 **Thu nhiệt** (ΔH > 0)")
                st.caption("Hấp thụ năng lượng từ môi trường")
            st.markdown("##### 📐 Biến thiên enthalpy")
            st.latex(r"\Delta H = E_{sp} - E_{cd} = " + f"{delta_h:+.0f}\\,kJ")
            st.markdown("##### ⚡ Năng lượng hoạt hóa")
            st.latex(r"E_a = " + f"{e_activated}\\,kJ")

    # ========== HÓA HỌC: THANG pH ==========
    elif dtype == "ph_scale":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn pH**")
            ph_val = st.slider("Giá trị pH:", 0.0, 14.0, float(data.get("ph", 7.0)), 0.5, key="hoa_ph_val")

        # Xác định môi trường
        if ph_val < 6.5:
            medium = "Axit"; icon = "🔴"; color = "#ef4444"
        elif ph_val > 7.5:
            medium = "Base"; icon = "🔵"; color = "#3b82f6"
        else:
            medium = "Trung tính"; icon = "🟢"; color = "#22c55e"

        # Ví dụ theo pH
        examples = {
            0: "HCl đặc, H₂SO₄ đặc",
            1: "Dịch vị dạ dày (HCl 0.1M)",
            2: "Nước chanh, giấm ăn",
            3: "Nước cam, cà chua",
            4: "Cà phê đen, bia",
            5: "Nước mưa axit nhẹ",
            6: "Sữa tươi",
            7: "Nước tinh khiết",
            8: "Nước biển",
            9: "Baking soda (NaHCO₃)",
            10: "Xà phòng, nước vôi",
            11: "Amoniac (NH₃) loãng",
            12: "Nước vôi trong",
            13: "Dung dịch NaOH 0.1M",
            14: "NaOH đặc",
        }
        example = examples.get(int(round(ph_val)), "—")

        with c2:
            try:
                fig = go.Figure()
                # Vẽ dải pH 0-14, chia gradient
                colors_pH = ["#dc2626", "#ef4444", "#f97316", "#fb923c",
                             "#fbbf24", "#fcd34d", "#a3e635", "#22c55e",
                             "#34d399", "#2dd4bf", "#06b6d4", "#3b82f6",
                             "#6366f1", "#818cf8", "#a78bfa"]
                for i in range(14):
                    fig.add_shape(type="rect", x0=i, x1=i+1, y0=0, y1=1,
                                  fillcolor=colors_pH[i], opacity=0.85,
                                  line=dict(color='#0f172a', width=2))
                    fig.add_annotation(x=i+0.5, y=0.5, text=str(i),
                                       showarrow=False,
                                       font=dict(color='#ffffff', size=16, family='system-ui'))

                # Đường chỉ pH hiện tại
                fig.add_shape(type="line", x0=ph_val, x1=ph_val, y0=-0.2, y1=1.3,
                              line=dict(color='#ffffff', width=4))
                fig.add_annotation(x=ph_val, y=1.4,
                                   text=f"{icon} pH = {ph_val}",
                                   showarrow=False,
                                   font=dict(color='#ffffff', size=15, family='system-ui'))

                fig.update_layout(
                    title=f"Thang pH — Môi trường: {medium}",
                    template="plotly_dark",
                    xaxis=dict(title="pH", range=[0, 14],
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, tickmode='linear', dtick=1),
                    yaxis=dict(range=[-0.5, 1.7], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    height=260, margin=dict(l=10, r=10, t=50, b=40),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ThangPH"))
            except Exception as err:
                st.error(f"Lỗi vẽ thang pH: {err}")

        with c3:
            st.markdown("##### 🧪 Môi trường")
            st.markdown(f"**{icon} {medium}**")
            st.markdown("##### 💧 Ví dụ")
            st.markdown(f"*{example}*")
            st.markdown("##### 📐 Nồng độ H⁺")
            h_conc = 10 ** (-ph_val)
            st.latex(r"[H^+] = 10^{-pH} = " + f"{h_conc:.2e}\\,M")
            st.markdown("##### 📐 Nồng độ OH⁻")
            oh_conc = 10 ** (ph_val - 14)
            st.latex(r"[OH^-] = 10^{pH-14} = " + f"{oh_conc:.2e}\\,M")

    # ========== HÓA HỌC: ĐỒ THỊ TỐC ĐỘ PHẢN ỨNG ==========
    elif dtype == "reaction_rate":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            k_rate = st.slider("Hằng số tốc độ k:", 0.05, 1.0,
                               float(data.get("k", 0.3)), 0.05, key="hoa_rr_k")
            order = st.radio("Bậc phản ứng:", [0, 1, 2], index=1, key="hoa_rr_order",
                             horizontal=True)
            temp_effect = st.checkbox("So sánh 2 nhiệt độ (T₁ và T₂ = 2×T₁)",
                                      value=True, key="hoa_rr_temp")

        with c2:
            try:
                t = np.linspace(0, 10, 200)
                # Bậc 0: [A] = [A]0 - kt
                # Bậc 1: [A] = [A]0 * e^(-kt)
                # Bậc 2: 1/[A] = 1/[A]0 + kt → [A] = 1/(1/[A]0 + kt)
                A0 = 1.0
                if order == 0:
                    A_t = np.clip(A0 - k_rate * t, 0, A0)
                    A_t2 = np.clip(A0 - 2 * k_rate * t, 0, A0)
                elif order == 1:
                    A_t = A0 * np.exp(-k_rate * t)
                    A_t2 = A0 * np.exp(-2 * k_rate * t)
                else:
                    A_t = 1 / (1 / A0 + k_rate * t)
                    A_t2 = 1 / (1 / A0 + 2 * k_rate * t)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=t, y=A_t, mode='lines',
                    line=dict(color='#38bdf8', width=3),
                    name=f'Bậc {order} — T₁ (k = {k_rate})',
                    hovertemplate="t = %{x:.2f}<br>[A] = %{y:.3f}<extra></extra>"))
                if temp_effect:
                    fig.add_trace(go.Scatter(x=t, y=A_t2, mode='lines',
                        line=dict(color='#f43f5e', width=3, dash='dash'),
                        name=f'Bậc {order} — T₂ = 2T₁ (k = {2*k_rate:.2f})',
                        hovertemplate="t = %{x:.2f}<br>[A] = %{y:.3f}<extra></extra>"))

                fig.update_layout(
                    title=f"Đồ thị tốc độ phản ứng — Bậc {order}",
                    template="plotly_dark",
                    xaxis=dict(title="Thời gian t (đơn vị)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="Nồng độ [A] (M)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("TocDoPhanUng"))
            except Exception as err:
                st.error(f"Lỗi vẽ đồ thị tốc độ: {err}")

        with c3:
            st.markdown("##### 📐 Phương trình tốc độ")
            if order == 0:
                st.latex(r"v = k")
                st.latex(r"[A] = [A]_0 - kt")
            elif order == 1:
                st.latex(r"v = k[A]")
                st.latex(r"[A] = [A]_0 \cdot e^{-kt}")
            else:
                st.latex(r"v = k[A]^2")
                st.latex(r"\dfrac{1}{[A]} = \dfrac{1}{[A]_0} + kt")
            st.markdown("##### 🌡 Ảnh hưởng nhiệt độ")
            st.caption("Khi T tăng, k tăng → phản ứng nhanh hơn (quy tắc Van't Hoff)")
            st.latex(r"k_T = k_{T_0} \cdot \gamma^{\Delta T/10}")

    # ========== HÓA HỌC: CÂN BẰNG HÓA HỌC ĐỘNG ==========
    elif dtype == "equilibrium":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            Kc = st.slider("Hằng số cân bằng Kc:", 0.1, 10.0,
                           float(data.get("Kc", 2.0)), 0.1, key="hoa_eq_Kc")
            A0 = st.slider("Nồng độ ban đầu [N₂]₀:", 0.5, 3.0,
                           float(data.get("A0", 1.0)), 0.1, key="hoa_eq_A0")
            B0 = st.slider("Nồng độ ban đầu [H₂]₀:", 0.5, 3.0,
                           float(data.get("B0", 3.0)), 0.1, key="hoa_eq_B0")
            t_max = st.slider("Thời gian khảo sát:", 5, 50,
                              int(data.get("t_max", 20)), 5, key="hoa_eq_tmax")

        with c2:
            try:
                # Phản ứng mẫu: N₂ + 3H₂ ⇌ 2NH₃
                t = np.linspace(0, t_max, 300)
                # Mô phỏng tiến về cân bằng bằng hàm mũ
                # Giả sử phản ứng thuận: N₂ + 3H₂ → 2NH₃
                # Tìm x tại cân bằng: Kc = (2x)^2 / ((A0-x)*(B0-3x)^3)
                # Đơn giản hóa: dùng x = A0 * (1 - exp(-k*t))
                # Với Kc ảnh hưởng đến x_max
                x_max_frac = min(0.9, Kc / (Kc + 1))  # heuristic
                x_max = A0 * x_max_frac * 0.7
                k_speed = 0.15
                x_t = x_max * (1 - np.exp(-k_speed * t))

                N2_t = A0 - x_t
                H2_t = B0 - 3 * x_t
                NH3_t = 2 * x_t

                # Tránh âm
                H2_t = np.clip(H2_t, 0, None)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=t, y=N2_t, mode='lines',
                    line=dict(color='#38bdf8', width=3), name='[N₂]',
                    hovertemplate="t = %{x:.1f}<br>[N₂] = %{y:.3f} M<extra></extra>"))
                fig.add_trace(go.Scatter(x=t, y=H2_t, mode='lines',
                    line=dict(color='#34d399', width=3), name='[H₂]',
                    hovertemplate="t = %{x:.1f}<br>[H₂] = %{y:.3f} M<extra></extra>"))
                fig.add_trace(go.Scatter(x=t, y=NH3_t, mode='lines',
                    line=dict(color='#fbbf24', width=3), name='[NH₃]',
                    hovertemplate="t = %{x:.1f}<br>[NH₃] = %{y:.3f} M<extra></extra>"))

                fig.update_layout(
                    title="Cân bằng hóa học động: N₂ + 3H₂ ⇌ 2NH₃",
                    template="plotly_dark",
                    xaxis=dict(title="Thời gian t", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="Nồng độ (M)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("CanBangHoaHoc"))
            except Exception as err:
                st.error(f"Lỗi vẽ cân bằng: {err}")

        with c3:
            st.markdown("##### 📐 Hằng số cân bằng")
            st.latex(r"K_c = \dfrac{[NH_3]^2}{[N_2]\cdot[H_2]^3}")
            st.markdown("##### 📊 Tại cân bằng")
            st.latex(r"K_c = " + f"{Kc:.2f}")
            st.markdown("##### 🔄 Nguyên lý Le Chatelier")
            st.caption("Khi thay đổi nồng độ, nhiệt độ, áp suất → cân bằng dịch chuyển để chống lại sự thay đổi.")

    # ========== HÓA HỌC: SƠ ĐỒ ĐIỆN PHÂN ==========
    elif dtype == "electrolysis":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            U = st.slider("Hiệu điện thế U (V):", 1.0, 12.0,
                          float(data.get("U", 5.0)), 0.5, key="hoa_el_U")
            solution = st.selectbox(
                "Dung dịch điện phân:",
                ["CuSO₄ (điện cực Cu)", "NaCl (điện cực trơ)", "H₂O (điện cực trơ)"],
                key="hoa_el_sol"
            )

        with c2:
            try:
                fig = go.Figure()
                # Bình điện phân (hình chữ nhật)
                fig.add_shape(type="rect", x0=1, x1=9, y0=0, y1=6,
                              line=dict(color='#38bdf8', width=3),
                              fillcolor='rgba(56,189,248,0.1)')

                # Dung dịch (màu xanh nhạt)
                fig.add_shape(type="rect", x0=1.1, x1=8.9, y0=0.1, y1=4,
                              fillcolor='rgba(56,189,248,0.25)',
                              line=dict(color='rgba(0,0,0,0)'))

                # 2 điện cực (nhúng xuống dung dịch)
                # Cathode (-) bên trái
                fig.add_shape(type="rect", x0=2.5, x1=3.0, y0=2, y1=6.5,
                              line=dict(color='#ef4444', width=2),
                              fillcolor='#ef4444')
                fig.add_annotation(x=2.75, y=6.8, text="Cực âm (−)",
                                   showarrow=False,
                                   font=dict(color='#ef4444', size=12))
                # Anode (+) bên phải
                fig.add_shape(type="rect", x0=7.0, x1=7.5, y0=2, y1=6.5,
                              line=dict(color='#3b82f6', width=2),
                              fillcolor='#3b82f6')
                fig.add_annotation(x=7.25, y=6.8, text="Cực dương (+)",
                                   showarrow=False,
                                   font=dict(color='#3b82f6', size=12))

                # Nguồn điện (pin) trên đỉnh
                fig.add_shape(type="rect", x0=4, x1=6, y0=7, y1=8,
                              line=dict(color='#fbbf24', width=2),
                              fillcolor='rgba(251,191,36,0.3)')
                fig.add_annotation(x=5, y=7.5, text=f"{U}V",
                                   showarrow=False,
                                   font=dict(color='#fbbf24', size=14, family='system-ui'))
                # Dây dẫn
                fig.add_shape(type="line", x0=2.75, x1=4, y0=6.5, y1=7.5,
                              line=dict(color='#fbbf24', width=2))
                fig.add_shape(type="line", x0=6, x1=7.25, y0=7.5, y1=6.5,
                              line=dict(color='#fbbf24', width=2))

                # Nhãn "Dung dịch điện phân"
                fig.add_annotation(x=5, y=1.5, text=f"<b>{solution}</b>",
                                   showarrow=False,
                                   font=dict(color='#f8fafc', size=13))

                fig.update_layout(
                    title=f"Bình điện phân — U = {U}V",
                    template="plotly_dark",
                    xaxis=dict(range=[0, 10], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(range=[-0.5, 9], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, scaleanchor='x', scaleratio=1),
                    height=500, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("DienPhan"))
            except Exception as err:
                st.error(f"Lỗi vẽ điện phân: {err}")

        with c3:
            st.markdown("##### 🧪 Phương trình")
            if "CuSO₄" in solution:
                st.markdown("**Cathode (−):**")
                st.latex(r"Cu^{2+} + 2e^- \rightarrow Cu")
                st.markdown("**Anode (+):**")
                st.latex(r"Cu \rightarrow Cu^{2+} + 2e^-")
                st.caption("→ Nồng độ CuSO₄ không đổi (anode tan)")
            elif "NaCl" in solution:
                st.markdown("**Cathode (−):**")
                st.latex(r"2H_2O + 2e^- \rightarrow H_2 + 2OH^-")
                st.markdown("**Anode (+):**")
                st.latex(r"2Cl^- \rightarrow Cl_2 + 2e^-")
                st.caption("→ Thu được H₂ (cathode) và Cl₂ (anode)")
            else:
                st.markdown("**Cathode (−):**")
                st.latex(r"2H_2O + 2e^- \rightarrow H_2 + 2OH^-")
                st.markdown("**Anode (+):**")
                st.latex(r"2H_2O \rightarrow O_2 + 4H^+ + 4e^-")
                st.caption("→ Điện phân nước: 2H₂O → 2H₂ + O₂")

    # ========== HÓA HỌC: MÔ HÌNH PHÂN TỬ 3D ==========
    elif dtype == "molecule_3d":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn phân tử**")
            molecule = st.selectbox(
                "Phân tử:",
                ["H₂O", "CH₄", "NH₃", "CO₂", "C₂H₄", "C₂H₂", "C₆H₆", "CH₃OH"],
                key="hoa_mol_choice"
            )
            show_bonds = st.checkbox("Hiển thị liên kết", value=True, key="hoa_mol_bonds")
            show_labels = st.checkbox("Hiển thị nhãn nguyên tử", value=True, key="hoa_mol_labels")

        # Dữ liệu: (x, y, z, element, size)
        ATOM_COLORS = {"H": "#f8fafc", "C": "#334155", "N": "#3b82f6",
                       "O": "#ef4444", "S": "#fbbf24"}
        ATOM_SIZES = {"H": 8, "C": 14, "N": 13, "O": 13, "S": 16}

        molecules_data = {
            "H₂O": {
                "atoms": [(0, 0, 0, "O"), (0.757, 0.586, 0, "H"), (-0.757, 0.586, 0, "H")],
                "bonds": [(0, 1), (0, 2)],
            },
            "CH₄": {
                "atoms": [(0, 0, 0, "C"),
                          (0.63, 0.63, 0.63, "H"), (-0.63, -0.63, 0.63, "H"),
                          (-0.63, 0.63, -0.63, "H"), (0.63, -0.63, -0.63, "H")],
                "bonds": [(0, 1), (0, 2), (0, 3), (0, 4)],
            },
            "NH₃": {
                "atoms": [(0, 0, 0, "N"),
                          (0, 0.94, 0, "H"),
                          (0.81, -0.47, 0, "H"), (-0.81, -0.47, 0, "H")],
                "bonds": [(0, 1), (0, 2), (0, 3)],
            },
            "CO₂": {
                "atoms": [(0, 0, 0, "C"), (1.16, 0, 0, "O"), (-1.16, 0, 0, "O")],
                "bonds": [(0, 1), (0, 2)],
            },
            "C₂H₄": {
                "atoms": [(0.67, 0, 0, "C"), (-0.67, 0, 0, "C"),
                          (1.23, 0.93, 0, "H"), (1.23, -0.93, 0, "H"),
                          (-1.23, 0.93, 0, "H"), (-1.23, -0.93, 0, "H")],
                "bonds": [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)],
            },
            "C₂H₂": {
                "atoms": [(0.6, 0, 0, "C"), (-0.6, 0, 0, "C"),
                          (1.66, 0, 0, "H"), (-1.66, 0, 0, "H")],
                "bonds": [(0, 1), (0, 2), (1, 3)],
            },
            "C₆H₆": {
                "atoms": [(1.4, 0, 0, "C"), (0.7, 1.21, 0, "C"), (-0.7, 1.21, 0, "C"),
                          (-1.4, 0, 0, "C"), (-0.7, -1.21, 0, "C"), (0.7, -1.21, 0, "C")] +
                         [(2.48, 0, 0, "H"), (1.24, 2.15, 0, "H"), (-1.24, 2.15, 0, "H"),
                          (-2.48, 0, 0, "H"), (-1.24, -2.15, 0, "H"), (1.24, -2.15, 0, "H")],
                "bonds": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0),
                          (0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)],
            },
            "CH₃OH": {
                "atoms": [(0, 0, 0, "C"), (1.43, 0, 0, "O"),
                          (1.77, 0.89, 0, "H"),
                          (-0.36, 1.02, 0, "H"), (-0.36, -0.51, 0.89, "H"),
                          (-0.36, -0.51, -0.89, "H")],
                "bonds": [(0, 1), (1, 2), (0, 3), (0, 4), (0, 5)],
            },
        }

        mdata = molecules_data.get(molecule, {"atoms": [], "bonds": []})

        with c2:
            try:
                fig = go.Figure()

                # Vẽ liên kết (đường nối)
                if show_bonds:
                    for i, j in mdata["bonds"]:
                        a1 = mdata["atoms"][i]
                        a2 = mdata["atoms"][j]
                        fig.add_trace(go.Scatter3d(
                            x=[a1[0], a2[0]], y=[a1[1], a2[1]], z=[a1[2], a2[2]],
                            mode='lines',
                            line=dict(color='#94a3b8', width=6),
                            showlegend=False, hoverinfo='skip'
                        ))

                # Vẽ nguyên tử theo nhóm element
                grouped = {}
                for x, y, z, elem in mdata["atoms"]:
                    grouped.setdefault(elem, {"x": [], "y": [], "z": [], "text": []})
                    grouped[elem]["x"].append(x)
                    grouped[elem]["y"].append(y)
                    grouped[elem]["z"].append(z)
                    grouped[elem]["text"].append(elem if show_labels else "")

                for elem, coords in grouped.items():
                    fig.add_trace(go.Scatter3d(
                        x=coords["x"], y=coords["y"], z=coords["z"],
                        mode='markers+text' if show_labels else 'markers',
                        marker=dict(
                            size=ATOM_SIZES.get(elem, 12),
                            color=ATOM_COLORS.get(elem, "#94a3b8"),
                            line=dict(color='#0f172a', width=1.5)
                        ),
                        text=coords["text"],
                        textposition="middle center",
                        textfont=dict(color='#0f172a' if elem != "C" else '#f8fafc', size=11),
                        name=elem,
                        hovertemplate=f"{elem}<br>x=%{{x:.2f}}<br>y=%{{y:.2f}}<br>z=%{{z:.2f}}<extra></extra>"
                    ))

                fig.update_layout(
                    title=f"Mô hình phân tử 3D — {molecule}",
                    template="plotly_dark",
                    scene=dict(
                        xaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False),
                        yaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False),
                        zaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False),
                        aspectmode='cube',
                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                    ),
                    height=500, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("PhanTu3D"))
            except Exception as err:
                st.error(f"Lỗi vẽ phân tử: {err}")

        with c3:
            st.markdown("##### 🧪 Phân tử")
            st.markdown(f"### {molecule}")
            st.markdown("##### 📐 Số nguyên tử")
            atom_count = {}
            for x, y, z, elem in mdata["atoms"]:
                atom_count[elem] = atom_count.get(elem, 0) + 1
            for elem, count in atom_count.items():
                st.markdown(f"- **{elem}**: {count}")
            st.markdown("##### 🎨 Chú thích màu")
            for elem in ["H", "C", "N", "O"]:
                if elem in atom_count:
                    st.markdown(
                        f"<div style='background:{ATOM_COLORS[elem]};width:20px;"
                        f"height:20px;border-radius:50%;display:inline-block;"
                        f"vertical-align:middle;margin-right:6px;"
                        f"border:1px solid #475569;'></div> **{elem}**",
                        unsafe_allow_html=True
                    )

    # ========== HÓA HỌC: CÔNG THỨC CẤU TẠO HỮU CƠ ==========
    elif dtype == "organic_structure":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn hợp chất**")
            compound = st.selectbox(
                "Hợp chất:",
                ["Methane (CH₄)", "Ethylene (C₂H₄)", "Acetylene (C₂H₂)",
                 "Ethanol (C₂H₅OH)", "Acetic acid (CH₃COOH)",
                 "Benzene (C₆H₆)", "Glucose (C₆H₁₂O₆)"],
                key="hoa_org_choice"
            )

        # Render cấu trúc bằng HTML đơn giản
        structures = {
            "Methane (CH₄)": {
                "formula": "CH₄",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 18px;
                            color: #f8fafc; line-height: 2;">
                    &nbsp;&nbsp;&nbsp;H<br>
                    &nbsp;&nbsp;&nbsp;|<br>
                    H—C—H<br>
                    &nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;&nbsp;H
                </div>
                """,
                "info": "Liên kết đơn C–H, cấu trúc tứ diện đều. Góc liên kết 109.5°.",
            },
            "Ethylene (C₂H₄)": {
                "formula": "C₂H₄",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 18px;
                            color: #f8fafc; line-height: 2;">
                    H&nbsp;&nbsp;&nbsp;&nbsp;H<br>
                    &nbsp;\\&nbsp;&nbsp;/<br>
                    &nbsp;&nbsp;C=C<br>
                    &nbsp;/&nbsp;&nbsp;\\<br>
                    H&nbsp;&nbsp;&nbsp;&nbsp;H
                </div>
                """,
                "info": "Liên kết đôi C=C, cấu trúc phẳng. Góc liên kết ~120°.",
            },
            "Acetylene (C₂H₂)": {
                "formula": "C₂H₂",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 18px;
                            color: #f8fafc; line-height: 2;">
                    H—C≡C—H
                </div>
                """,
                "info": "Liên kết ba C≡C, cấu trúc thẳng. Góc liên kết 180°.",
            },
            "Ethanol (C₂H₅OH)": {
                "formula": "C₂H₅OH",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 16px;
                            color: #f8fafc; line-height: 2;">
                    &nbsp;&nbsp;&nbsp;H&nbsp;&nbsp;&nbsp;H<br>
                    &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;|<br>
                    H—C—C—O—H<br>
                    &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;&nbsp;H&nbsp;&nbsp;&nbsp;H
                </div>
                """,
                "info": "Nhóm chức –OH (alcohol). Có liên kết hydrogen giữa các phân tử.",
            },
            "Acetic acid (CH₃COOH)": {
                "formula": "CH₃COOH",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 16px;
                            color: #f8fafc; line-height: 2;">
                    &nbsp;&nbsp;&nbsp;&nbsp;O<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;||<br>
                    H—C—C—O—H<br>
                    &nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;&nbsp;H
                </div>
                """,
                "info": "Nhóm chức –COOH (carboxylic acid). Tính axit yếu.",
            },
            "Benzene (C₆H₆)": {
                "formula": "C₆H₆",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 16px;
                            color: #f8fafc; line-height: 2;">
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;H<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;C&nbsp;—&nbsp;C<br>
                    &nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\\<br>
                    C&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C<br>
                    &nbsp;\\&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/<br>
                    &nbsp;&nbsp;C&nbsp;—&nbsp;C<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;H<br>
                    <div style="color: #fbbf24; font-size: 14px; margin-top: 8px;">
                    (Vòng benzen — 3 liên kết đôi xen kẽ)
                    </div>
                </div>
                """,
                "info": "Vòng thơm 6 cạnh, 3 liên kết đôi xen kẽ liên kết đơn. Bền vững.",
            },
            "Glucose (C₆H₁₂O₆)": {
                "formula": "C₆H₁₂O₆",
                "html": """
                <div style="font-family: 'Courier New', monospace; font-size: 14px;
                            color: #f8fafc; line-height: 1.8;">
                    &nbsp;&nbsp;CH₂OH<br>
                    &nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;C——O<br>
                    &nbsp;/&nbsp;&nbsp;&nbsp;\\<br>
                    C&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C—OH<br>
                    &nbsp;\\&nbsp;&nbsp;&nbsp;/<br>
                    &nbsp;&nbsp;C——C—OH<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;OH<br>
                    <div style="color: #fbbf24; font-size: 13px; margin-top: 6px;">
                    (Dạng vòng pyranose)
                    </div>
                </div>
                """,
                "info": "Monosaccharide, dạng vòng 6 cạnh. Có nhóm –OH hemiacetal.",
            },
        }

        data_org = structures.get(compound, {"formula": "", "html": "", "info": ""})

        with c2:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #0f172a, #1e293b); '
                f'padding: 40px; border-radius: 12px; border: 2px solid #38bdf8; '
                f'text-align: center; min-height: 380px; '
                f'display: flex; align-items: center; justify-content: center; '
                f'box-shadow: 0 0 20px rgba(56,189,248,0.15);">'
                f'{data_org["html"]}'
                f'</div>',
                unsafe_allow_html=True
            )

        with c3:
            st.markdown("##### 🧪 Hợp chất")
            st.markdown(f"### {data_org['formula']}")
            st.markdown("##### 📝 Đặc điểm")
            st.info(data_org["info"])
            st.markdown("##### 🎓 Loại hợp chất")
            if "ane" in compound.lower() or "methane" in compound.lower():
                st.markdown("**Alkane** (hydrocarbon no)")
            elif "ylene" in compound.lower():
                st.markdown("**Alkene** (1 liên kết đôi)")
            elif "cetylene" in compound.lower():
                st.markdown("**Alkyne** (1 liên kết ba)")
            elif "ol" in compound.lower():
                st.markdown("**Alcohol** (nhóm –OH)")
            elif "acid" in compound.lower():
                st.markdown("**Carboxylic acid** (–COOH)")
            elif "benzene" in compound.lower():
                st.markdown("**Arene** (vòng thơm)")
            elif "glucose" in compound.lower():
                st.markdown("**Carbohydrate** (monosaccharide)")

    # ========== SINH HỌC: DNA XOẮN KÉP 3D ==========
    elif dtype == "dna_helix":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            n_turns = st.slider("Số vòng xoắn:", 1, 6,
                                int(data.get("n_turns", 3)), 1, key="sinh_dna_turns")
            radius = st.slider("Bán kính xoắn:", 0.5, 1.5,
                               float(data.get("radius", 1.0)), 0.1, key="sinh_dna_r")
            pitch = st.slider("Bước xoắn (chiều cao/vòng):", 1.0, 3.0,
                              float(data.get("pitch", 2.0)), 0.2, key="sinh_dna_pitch")
            show_bases = st.checkbox("Hiển thị base pair (A-T, G-C)", value=True, key="sinh_dna_bases")

        with c2:
            try:
                t_vals = np.linspace(0, 2 * np.pi * n_turns, 400)
                # 2 mạch xoắn ngược chiều nhau (lệch pha π)
                x1 = radius * np.cos(t_vals)
                y1 = radius * np.sin(t_vals)
                z1 = pitch * t_vals / (2 * np.pi)

                x2 = radius * np.cos(t_vals + np.pi)
                y2 = radius * np.sin(t_vals + np.pi)
                z2 = z1

                fig = go.Figure()

                # Mạch 1 (xanh dương)
                fig.add_trace(go.Scatter3d(
                    x=x1, y=y1, z=z1, mode='lines',
                    line=dict(color='#38bdf8', width=8),
                    name='Mạch 1 (5\'→3\')', hoverinfo='skip'
                ))
                # Mạch 2 (hồng)
                fig.add_trace(go.Scatter3d(
                    x=x2, y=y2, z=z2, mode='lines',
                    line=dict(color='#f472b6', width=8),
                    name='Mạch 2 (3\'→5\')', hoverinfo='skip'
                ))

                # Base pair (rungs) - vẽ khoảng 20 base
                if show_bases:
                    n_bases = 20
                    base_indices = np.linspace(0, len(t_vals) - 1, n_bases).astype(int)
                    bx, by, bz = [], [], []
                    base_colors = []
                    base_pairs = ['A-T', 'T-A', 'G-C', 'C-G']
                    for i, idx in enumerate(base_indices):
                        bx.extend([x1[idx], x2[idx], None])
                        by.extend([y1[idx], y2[idx], None])
                        bz.extend([z1[idx], z2[idx], None])
                    fig.add_trace(go.Scatter3d(
                        x=bx, y=by, z=bz, mode='lines',
                        line=dict(color='#fbbf24', width=3),
                        name='Base pair (A-T, G-C)', hoverinfo='skip'
                    ))

                fig.update_layout(
                    title=f"DNA xoắn kép — {n_turns} vòng xoắn",
                    template="plotly_dark",
                    scene=dict(
                        xaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False),
                        yaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False),
                        zaxis=dict(showbackground=True, backgroundcolor="#0f172a",
                                   showgrid=True, gridcolor="#1e293b",
                                   showticklabels=False, zeroline=False,
                                   title="Chiều dài DNA"),
                        aspectmode='manual',
                        aspectratio=dict(x=1, y=1, z=2),
                        camera=dict(eye=dict(x=1.5, y=1.5, z=0.8))
                    ),
                    height=560, margin=dict(l=10, r=10, t=40, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("DNA"))
            except Exception as err:
                st.error(f"Lỗi vẽ DNA: {err}")

        with c3:
            st.markdown("##### 🧬 Cấu trúc")
            st.markdown("**Mô hình Watson-Crick** (1953)")
            st.markdown("##### 📐 Thông số thật")
            st.latex(r"\text{Bước xoắn} = 3.4\,\text{nm}")
            st.latex(r"10\,\text{base pair/vòng}")
            st.latex(r"\text{Đường kính} = 2\,\text{nm}")
            st.markdown("##### 🔗 Nguyên tắc bổ sung")
            st.markdown("- **A** (Adenine) ↔ **T** (Thymine): 2 liên kết H")
            st.markdown("- **G** (Guanine) ↔ **C** (Cytosine): 3 liên kết H")
            st.markdown("##### 🎯 Chiều mạch")
            st.markdown("- Mạch 1: **5' → 3'**")
            st.markdown("- Mạch 2: **3' → 5'** (ngược chiều)")

    # ========== SINH HỌC: TỔNG HỢP PROTEIN ==========
    elif dtype == "protein_synthesis":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn giai đoạn**")
            stage = st.radio(
                "Giai đoạn:",
                ["1. Phiên mã (DNA→mRNA)", "2. Dịch mã (mRNA→Protein)"],
                key="sinh_ps_stage"
            )
            show_animation = st.checkbox("Hiển thị mũi tên di chuyển", value=True, key="sinh_ps_anim")

        with c2:
            try:
                fig = go.Figure()
                if "Phiên mã" in stage:
                    # DNA → mRNA
                    # DNA (đoạn thẳng đôi)
                    fig.add_trace(go.Scatter(x=[0, 10], y=[2, 2], mode='lines',
                        line=dict(color='#38bdf8', width=6), name='Mạch DNA gốc 3\'→5\''))
                    fig.add_trace(go.Scatter(x=[0, 10], y=[1.5, 1.5], mode='lines',
                        line=dict(color='#f472b6', width=6), name='Mạch DNA bổ sung 5\'→3\''))

                    # Base pairs
                    for i in range(0, 11):
                        fig.add_trace(go.Scatter(x=[i, i], y=[1.5, 2], mode='lines',
                            line=dict(color='#fbbf24', width=2), showlegend=False, hoverinfo='skip'))

                    # Enzyme RNA polymerase (vòng tròn)
                    fig.add_shape(type="circle", x0=4, x1=5.5, y0=0.8, y1=2.6,
                                  fillcolor='rgba(34,197,94,0.4)',
                                  line=dict(color='#22c55e', width=2))
                    fig.add_annotation(x=4.75, y=2.8, text="RNA polymerase",
                                       showarrow=False,
                                       font=dict(color='#22c55e', size=12))

                    # mRNA đang tách ra
                    fig.add_trace(go.Scatter(x=[0, 10], y=[-1, -1], mode='lines',
                        line=dict(color='#a78bfa', width=6), name='mRNA (5\'→3\')'))
                    # Mũi tên nối mRNA với mạch gốc
                    if show_animation:
                        for i in range(3, 8):
                            fig.add_annotation(x=i, y=-0.5, ax=i, ay=0.5,
                                xref='x', yref='y', axref='x', ayref='y',
                                text='', showarrow=True, arrowhead=0,
                                arrowwidth=1, arrowcolor='#a78bfa')

                else:  # Dịch mã
                    # mRNA
                    fig.add_trace(go.Scatter(x=[0, 12], y=[1, 1], mode='lines',
                        line=dict(color='#a78bfa', width=6), name='mRNA'))

                    # Codons
                    codons = ["AUG", "GCA", "UAA", "CCG"]
                    for i, codon in enumerate(codons):
                        fig.add_annotation(x=i*3 + 1.5, y=1.4, text=f"<b>{codon}</b>",
                                           showarrow=False,
                                           font=dict(color='#f8fafc', size=13))

                    # Ribosome (2 tiểu phần)
                    fig.add_shape(type="circle", x0=2, x1=8, y0=0.3, y1=2.2,
                                  fillcolor='rgba(34,197,94,0.2)',
                                  line=dict(color='#22c55e', width=2))
                    fig.add_annotation(x=5, y=2.4, text="Ribosome",
                                       showarrow=False,
                                       font=dict(color='#22c55e', size=13))

                    # tRNA (chữ Y) mang axit amin
                    trna_x = [1.5, 4.5, 7.5]
                    trna_labels = ["Met", "Ala", "STOP"]
                    trna_colors = ['#fbbf24', '#f472b6', '#94a3b8']
                    for x, label, col in zip(trna_x, trna_labels, trna_colors):
                        # tRNA
                        fig.add_trace(go.Scatter(x=[x, x, x], y=[3.5, 2.5, 1.8],
                            mode='lines+markers+text',
                            line=dict(color=col, width=3),
                            marker=dict(size=8, color=col),
                            text=['', '', label],
                            textposition='top center',
                            textfont=dict(color=col, size=12),
                            showlegend=False, hoverinfo='skip'))

                    # Axit amin (chuỗi)
                    fig.add_trace(go.Scatter(x=[1.5, 4.5], y=[3.5, 3.5], mode='lines+markers',
                        line=dict(color='#f43f5e', width=3),
                        marker=dict(size=10, color='#f43f5e', symbol='circle'),
                        name='Chuỗi polypeptide',
                        hoverinfo='skip'))

                fig.update_layout(
                    title=f"Tổng hợp protein — {stage}",
                    template="plotly_dark",
                    xaxis=dict(range=[-1, 13], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-2, 4.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False,
                               scaleanchor='x', scaleratio=1),
                    height=460, margin=dict(l=10, r=10, t=40, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("TongHopProtein"))
            except Exception as err:
                st.error(f"Lỗi vẽ tổng hợp protein: {err}")

        with c3:
            if "Phiên mã" in stage:
                st.markdown("##### 📝 Quá trình")
                st.markdown("DNA → **mRNA** (diễn ra trong nhân)")
                st.markdown("##### 🔗 Nguyên tắc")
                st.latex(r"A_{DNA} \rightarrow U_{mRNA}")
                st.latex(r"T_{DNA} \rightarrow A_{mRNA}")
                st.latex(r"G_{DNA} \rightarrow X_{mRNA}")
                st.latex(r"X_{DNA} \rightarrow G_{mRNA}")
                st.markdown("##### 🎯 Enzyme")
                st.markdown("**RNA polymerase**")
            else:
                st.markdown("##### 📝 Quá trình")
                st.markdown("mRNA → **Protein** (tại ribosome)")
                st.markdown("##### 🎯 Mã di truyền")
                st.markdown("- **AUG**: mã mở đầu (Met)")
                st.markdown("- **UAA, UAG, UGA**: mã kết thúc")
                st.markdown("##### 🔗 Liên kết")
                st.markdown("Codon (mRNA) ↔ Anticodon (tRNA)")

    # ========== SINH HỌC: NGUYÊN PHÂN / GIẢM PHÂN ==========
    elif dtype == "cell_division":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn kiểu**")
            division_type = st.radio(
                "Kiểu phân bào:",
                ["Nguyên phân (Mitosis)", "Giảm phân (Meiosis)"],
                key="sinh_cd_type"
            )
            if "Nguyên phân" in division_type:
                stage = st.select_slider(
                    "Giai đoạn:",
                    options=["Kỳ trung gian", "Kỳ đầu", "Kỳ giữa", "Kỳ sau", "Kỳ cuối"],
                    value="Kỳ giữa", key="sinh_cd_stage_mit"
                )
            else:
                stage = st.select_slider(
                    "Giai đoạn:",
                    options=["Kỳ trung gian", "Giảm phân I", "Giảm phân II", "4 tế bào con"],
                    value="Giảm phân I", key="sinh_cd_stage_mei"
                )

        with c2:
            try:
                fig = go.Figure()

                if "Nguyên phân" in division_type:
                    # 2n = 4 (2 cặp NST)
                    if stage == "Kỳ trung gian":
                        # NST tháo xoắn
                        for i, (x, y) in enumerate([(-1.5, 0.8), (-0.5, 0.8), (0.5, -0.8), (1.5, -0.8)]):
                            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers+text',
                                marker=dict(size=25, color='#38bdf8' if i < 2 else '#f472b6',
                                            line=dict(color='#f8fafc', width=2)),
                                text=[f'({i+1})'], textposition='middle center',
                                textfont=dict(color='#0f172a', size=10),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="NST tháo xoắn, nhân đôi",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    elif stage == "Kỳ đầu":
                        # NST bắt đầu xoắn
                        for i, (x, y) in enumerate([(-1.5, 0.8), (-0.5, 0.8), (0.5, -0.8), (1.5, -0.8)]):
                            fig.add_trace(go.Scatter(x=[x, x+0.15], y=[y, y], mode='lines+markers',
                                line=dict(color='#38bdf8' if i < 2 else '#f472b6', width=6),
                                marker=dict(size=8),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_shape(type="circle", x0=-2.2, x1=2.2, y0=-1.5, y1=1.5,
                                      line=dict(color='#fbbf24', width=2, dash='dot'),
                                      fillcolor='rgba(0,0,0,0)')
                        fig.add_annotation(x=0, y=-2, text="NST co xoắn, màng nhân tiêu biến",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    elif stage == "Kỳ giữa":
                        # NST xếp hàng ở mặt phẳng xích đạo
                        ys = [0.6, 0, -0.6, -1.2]
                        for i, y in enumerate(ys):
                            fig.add_trace(go.Scatter(x=[0, 0], y=[y, y+0.4], mode='lines+markers',
                                line=dict(color='#38bdf8' if i < 2 else '#f472b6', width=8),
                                marker=dict(size=6),
                                showlegend=False, hoverinfo='skip'))
                        # Thoi phân bào
                        fig.add_trace(go.Scatter(x=[-2, 0], y=[1.5, 1], mode='lines',
                            line=dict(color='#a78bfa', width=1.5, dash='dash'),
                            showlegend=False, hoverinfo='skip'))
                        fig.add_trace(go.Scatter(x=[-2, 0], y=[-1.5, -1], mode='lines',
                            line=dict(color='#a78bfa', width=1.5, dash='dash'),
                            showlegend=False, hoverinfo='skip'))
                        fig.add_trace(go.Scatter(x=[2, 0], y=[1.5, 1], mode='lines',
                            line=dict(color='#a78bfa', width=1.5, dash='dash'),
                            showlegend=False, hoverinfo='skip'))
                        fig.add_trace(go.Scatter(x=[2, 0], y=[-1.5, -1], mode='lines',
                            line=dict(color='#a78bfa', width=1.5, dash='dash'),
                            showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="NST xếp 1 hàng trên mặt phẳng xích đạo",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    elif stage == "Kỳ sau":
                        # NST phân ly về 2 cực
                        for i in range(4):
                            color = '#38bdf8' if i < 2 else '#f472b6'
                            y = 0.5 - i * 0.4
                            fig.add_trace(go.Scatter(x=[-1.8, -1.5], y=[y, y], mode='lines',
                                line=dict(color=color, width=8), showlegend=False, hoverinfo='skip'))
                            fig.add_trace(go.Scatter(x=[1.5, 1.8], y=[y, y], mode='lines',
                                line=dict(color=color, width=8), showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="NST tách ra, di chuyển về 2 cực",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    else:  # Kỳ cuối
                        # 2 tế bào con
                        fig.add_shape(type="circle", x0=-2.8, x1=-0.2, y0=-1, y1=1,
                                      line=dict(color='#38bdf8', width=2),
                                      fillcolor='rgba(56,189,248,0.1)')
                        fig.add_shape(type="circle", x0=0.2, x1=2.8, y0=-1, y1=1,
                                      line=dict(color='#f472b6', width=2),
                                      fillcolor='rgba(244,114,182,0.1)')
                        for i in range(4):
                            color = '#38bdf8' if i < 2 else '#f472b6'
                            cx = -1.5 if i < 2 else 1.5
                            cy = 0.3 if i % 2 == 0 else -0.3
                            fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers',
                                marker=dict(size=15, color=color,
                                            line=dict(color='#f8fafc', width=1.5)),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="2 tế bào con (2n)",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                else:  # Giảm phân
                    if stage == "Kỳ trung gian":
                        for i, (x, y) in enumerate([(-1.5, 0.8), (-0.5, 0.8), (0.5, -0.8), (1.5, -0.8)]):
                            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers+text',
                                marker=dict(size=25, color='#38bdf8' if i < 2 else '#f472b6',
                                            line=dict(color='#f8fafc', width=2)),
                                text=[f'({i+1})'], textposition='middle center',
                                textfont=dict(color='#0f172a', size=10),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="Tế bào 2n chuẩn bị giảm phân",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    elif stage == "Giảm phân I":
                        # Tiếp hợp tạo cặp tương đồng
                        for i in range(2):
                            y = 0.6 - i * 1.2
                            fig.add_trace(go.Scatter(x=[-2, -1, -0.5], y=[y, y, y], mode='lines+markers',
                                line=dict(color='#38bdf8', width=6),
                                marker=dict(size=6), showlegend=False, hoverinfo='skip'))
                            fig.add_trace(go.Scatter(x=[-2, -1, -0.5], y=[y+0.15, y+0.15, y+0.15],
                                mode='lines+markers',
                                line=dict(color='#f472b6', width=6),
                                marker=dict(size=6), showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=-1.5, y=1.6, text="Cặp NST tương đồng",
                                           showarrow=False, font=dict(color='#f8fafc', size=12))
                        # Trao đổi chéo
                        fig.add_annotation(x=-1, y=0.6, ax=-1, ay=1.5,
                            xref='x', yref='y', axref='x', ayref='y',
                            text='', showarrow=True, arrowhead=2,
                            arrowwidth=2, arrowcolor='#fbbf24')
                        fig.add_annotation(x=-1, y=0.9, text="Trao đổi chéo",
                                           showarrow=False, font=dict(color='#fbbf24', size=11))
                        fig.add_annotation(x=1.5, y=-2, text="Giảm phân I → 2 tế bào (n, kép)",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    elif stage == "Giảm phân II":
                        # 2 tế bào, mỗi tế bào có 2 NST kép
                        for cx in [-1.8, 1.8]:
                            fig.add_shape(type="circle", x0=cx-1, x1=cx+1, y0=-1, y1=1,
                                          line=dict(color='#38bdf8', width=2),
                                          fillcolor='rgba(56,189,248,0.1)')
                            fig.add_trace(go.Scatter(x=[cx-0.3, cx+0.3], y=[0.3, 0.3],
                                mode='lines', line=dict(color='#f472b6', width=6),
                                showlegend=False, hoverinfo='skip'))
                            fig.add_trace(go.Scatter(x=[cx-0.3, cx+0.3], y=[-0.3, -0.3],
                                mode='lines', line=dict(color='#38bdf8', width=6),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="Giảm phân II → 4 tế bào (n, đơn)",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                    else:  # 4 tế bào con
                        for i, (cx, cy) in enumerate([(-2.5, 0.5), (-1.5, -0.5), (1.5, 0.5), (2.5, -0.5)]):
                            fig.add_shape(type="circle", x0=cx-0.4, x1=cx+0.4, y0=cy-0.4, y1=cy+0.4,
                                          line=dict(color='#34d399', width=2),
                                          fillcolor='rgba(52,211,153,0.2)')
                            fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers',
                                marker=dict(size=12, color='#38bdf8' if i % 2 == 0 else '#f472b6',
                                            line=dict(color='#f8fafc', width=1)),
                                showlegend=False, hoverinfo='skip'))
                        fig.add_annotation(x=0, y=-2, text="4 tế bào con (n) — giao tử",
                                           showarrow=False, font=dict(color='#f8fafc', size=13))

                fig.update_layout(
                    title=f"{division_type} — {stage}",
                    template="plotly_dark",
                    xaxis=dict(range=[-3.5, 3.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-2.5, 2.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False,
                               scaleanchor='x', scaleratio=1),
                    height=460, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("PhanBao"))
            except Exception as err:
                st.error(f"Lỗi vẽ phân bào: {err}")

        with c3:
            if "Nguyên phân" in division_type:
                st.markdown("##### 📝 Kết quả")
                st.markdown("1 tế bào (2n) → **2 tế bào con (2n)**")
                st.markdown("##### 🎯 Ý nghĩa")
                st.markdown("- Giúp cơ thể **sinh trưởng**")
                st.markdown("- **Thay thế** tế bào già, tổn thương")
                st.markdown("- Truyền **nguyên vẹn** bộ NST")
                st.markdown("##### 📊 Số NST qua các kỳ")
                st.markdown("- Kỳ trung gian: 2n (nhân đôi → 2n kép)")
                st.markdown("- Kỳ giữa: 2n kép")
                st.markdown("- Kỳ sau: 4n đơn")
                st.markdown("- Kỳ cuối: 2n × 2 tế bào")
            else:
                st.markdown("##### 📝 Kết quả")
                st.markdown("1 tế bào (2n) → **4 tế bào con (n)**")
                st.markdown("##### 🎯 Ý nghĩa")
                st.markdown("- Tạo **giao tử** (trứng/tinh trùng)")
                st.markdown("- **Giảm ½** số NST → phục hồi khi thụ tinh")
                st.markdown("- Tạo **biến dị tổ hợp**")
                st.markdown("##### 📊 Số NST qua các kỳ")
                st.markdown("- Kỳ trung gian: 2n (2n kép)")
                st.markdown("- GP I: 2n kép → 2 tế bào (n kép)")
                st.markdown("- GP II: n kép → 4 tế bào (n đơn)")

    # ========== SINH HỌC: SƠ ĐỒ PUNNETT ==========
    elif dtype == "punnett_square":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            parent1 = st.text_input("Kiểu gen Bố mẹ 1:", value=data.get("p1", "Aa"),
                                     key="sinh_pn_p1", max_chars=2).strip()
            parent2 = st.text_input("Kiểu gen Bố mẹ 2:", value=data.get("p2", "Aa"),
                                     key="sinh_pn_p2", max_chars=2).strip()

            # ✅ FIX 5: Validate kiểu gen bằng regex
            #   ^[AaBbCcDdEe]{2}$  → đúng 2 alen, cùng 1 gen (1 trong 5 cặp A-E)
            _VALID_GENOTYPE = re.compile(r'^[AaBbCcDdEe]{2}$')
            if not _VALID_GENOTYPE.match(parent1):
                st.warning(f"⚠️ Kiểu gen 1 không hợp lệ (`{parent1 or '∅'}`) — "
                           f"cần 2 alen cùng 1 gen (VD: AA, Aa, aa)")
                parent1 = "Aa"
            if not _VALID_GENOTYPE.match(parent2):
                st.warning(f"⚠️ Kiểu gen 2 không hợp lệ (`{parent2 or '∅'}`) — "
                           f"cần 2 alen cùng 1 gen (VD: AA, Aa, aa)")
                parent2 = "Aa"

        # Tính giao tử và kết quả lai
        gametes1 = [parent1[0], parent1[1]] if len(parent1) == 2 else [parent1]
        gametes2 = [parent2[0], parent2[1]] if len(parent2) == 2 else [parent2]

        # Tạo bảng Punnett
        punnett = []
        for g1 in gametes1:
            row = []
            for g2 in gametes2:
                # Sắp xếp để chữ hoa đứng trước
                combo = "".join(sorted([g1, g2], key=lambda c: (not c.isupper(), c)))
                row.append(combo)
            punnett.append(row)

        # Đếm kiểu gen
        genotype_count = {}
        for row in punnett:
            for g in row:
                genotype_count[g] = genotype_count.get(g, 0) + 1
        total = sum(genotype_count.values())

        # Đếm kiểu hình (trội nếu có ít nhất 1 chữ hoa)
        phenotype_count = {"Trội": 0, "Lặn": 0}
        for row in punnett:
            for g in row:
                if any(c.isupper() for c in g):
                    phenotype_count["Trội"] += 1
                else:
                    phenotype_count["Lặn"] += 1

        with c2:
            try:
                # Vẽ bảng Punnett
                fig = go.Figure()

                n_cols = len(gametes2)
                n_rows = len(gametes1)

                cell_size = 1.0
                # Vẽ ô header
                for j, g2 in enumerate(gametes2):
                    fig.add_shape(type="rect",
                                  x0=j * cell_size + 1, x1=(j + 1) * cell_size + 1,
                                  y0=n_rows * cell_size, y1=(n_rows + 1) * cell_size,
                                  line=dict(color='#38bdf8', width=2),
                                  fillcolor='rgba(56,189,248,0.25)')
                    fig.add_annotation(x=j * cell_size + 1.5, y=n_rows * cell_size + 0.5,
                                       text=f"<b>{g2}</b>", showarrow=False,
                                       font=dict(color='#f8fafc', size=18))
                for i, g1 in enumerate(gametes1):
                    fig.add_shape(type="rect",
                                  x0=0, x1=cell_size,
                                  y0=(n_rows - 1 - i) * cell_size,
                                  y1=(n_rows - i) * cell_size,
                                  line=dict(color='#38bdf8', width=2),
                                  fillcolor='rgba(56,189,248,0.25)')
                    fig.add_annotation(x=0.5, y=(n_rows - 1 - i) * cell_size + 0.5,
                                       text=f"<b>{g1}</b>", showarrow=False,
                                       font=dict(color='#f8fafc', size=18))
                # Góc trên trái
                fig.add_shape(type="rect", x0=0, x1=cell_size,
                              y0=n_rows * cell_size, y1=(n_rows + 1) * cell_size,
                              line=dict(color='#0f172a', width=2),
                              fillcolor='rgba(0,0,0,0)')
                fig.add_annotation(x=0.5, y=n_rows * cell_size + 0.5,
                                   text="♀ \\ ♂", showarrow=False,
                                   font=dict(color='#94a3b8', size=12))

                # Vẽ ô kết quả
                for i, row in enumerate(punnett):
                    for j, g in enumerate(row):
                        has_dominant = any(c.isupper() for c in g)
                        fill = 'rgba(52,211,153,0.2)' if has_dominant else 'rgba(244,114,182,0.2)'
                        fig.add_shape(type="rect",
                                      x0=j * cell_size + 1, x1=(j + 1) * cell_size + 1,
                                      y0=(n_rows - 1 - i) * cell_size,
                                      y1=(n_rows - i) * cell_size,
                                      line=dict(color='#334155', width=1),
                                      fillcolor=fill)
                        # Sắp xếp chữ hoa trước
                        sorted_g = "".join(sorted(g, key=lambda c: (not c.isupper(), c)))
                        fig.add_annotation(x=j * cell_size + 1.5,
                                           y=(n_rows - 1 - i) * cell_size + 0.5,
                                           text=f"<b>{sorted_g}</b>", showarrow=False,
                                           font=dict(color='#f8fafc', size=20))

                fig.update_layout(
                    title=f"Phép lai: {parent1} × {parent2}",
                    template="plotly_dark",
                    xaxis=dict(range=[-0.3, n_cols + 1.3], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-0.3, n_rows + 1.3], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False,
                               scaleanchor='x', scaleratio=1),
                    height=460, margin=dict(l=10, r=10, t=50, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("Punnett"))
            except Exception as err:
                st.error(f"Lỗi vẽ Punnett: {err}")

        with c3:
            st.markdown("##### 📊 Tỉ lệ kiểu gen")
            for g, count in sorted(genotype_count.items()):
                ratio = count / total
                st.markdown(f"- **{g}**: {count}/{total} ({ratio*100:.0f}%)")
            st.markdown("##### 🎨 Tỉ lệ kiểu hình")
            if phenotype_count["Lặn"] > 0:
                st.markdown(f"- **Trội**: {phenotype_count['Trội']}/{total}")
                st.markdown(f"- **Lặn**: {phenotype_count['Lặn']}/{total}")
            else:
                st.markdown(f"- **100% Trội** (tất cả có alen trội)")
            st.markdown("##### 📝 Nhận xét")
            if parent1 == "Aa" and parent2 == "Aa":
                st.caption("→ Phép lai phân tích của Mendel: TLKG 1:2:1, TLKH 3:1")
            elif parent1 == "AA" and parent2 == "aa":
                st.caption("→ F₁ đồng tính trội (100% Aa)")
            elif parent1 == "Aa" and parent2 == "aa":
                st.caption("→ Phép lai phân tích: TLKG 1:1, TLKH 1:1")

    # ========== SINH HỌC: CHU TRÌNH KREBS ==========
    elif dtype == "krebs_cycle":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            show_atp = st.checkbox("Hiển thị số ATP/NADH/FADH₂", value=True, key="sinh_krebs_atp")
            highlight_step = st.slider("Highlight bước:", 1, 8,
                                       int(data.get("step", 1)), 1, key="sinh_krebs_step")

        # ✅ FIX 4: `steps` được định nghĩa NGOÀI try để c3 luôn truy cập được
        steps = [
            ("Citrate", "Acetyl-CoA\n+ Oxaloacetate"),
            ("Isocitrate", "Citrate\n- H₂O"),
            ("α-Ketoglutarate", "Isocitrate\n- CO₂, NADH"),
            ("Succinyl-CoA", "α-KG\n- CO₂, NADH"),
            ("Succinate", "Succinyl-CoA\n- GTP"),
            ("Fumarate", "Succinate\n- FADH₂"),
            ("Malate", "Fumarate\n+ H₂O"),
            ("Oxaloacetate", "Malate\n- NADH"),
        ]

        with c2:
            try:
                fig = go.Figure()
                n_steps = len(steps)
                radius = 2.5
                angles = np.linspace(0, 2 * np.pi, n_steps, endpoint=False)

                # Vẽ vòng tròn chu trình
                circle_t = np.linspace(0, 2 * np.pi, 100)
                fig.add_trace(go.Scatter(x=radius*np.cos(circle_t), y=radius*np.sin(circle_t),
                    mode='lines', line=dict(color='#475569', width=2, dash='dot'),
                    showlegend=False, hoverinfo='skip'))

                # Vẽ mũi tên giữa các bước
                for i in range(n_steps):
                    a1 = angles[i]
                    a2 = angles[(i+1) % n_steps]
                    mid_angle = (a1 + a2) / 2
                    if a1 > a2:  # wrap around
                        mid_angle = (a1 + a2 + 2 * np.pi) / 2
                    fig.add_annotation(
                        x=radius * np.cos(mid_angle),
                        y=radius * np.sin(mid_angle),
                        ax=radius * 0.95 * np.cos(mid_angle),
                        ay=radius * 0.95 * np.sin(mid_angle),
                        xref='x', yref='y', axref='x', ayref='y',
                        text='', showarrow=True, arrowhead=2,
                        arrowsize=1.2, arrowwidth=2, arrowcolor='#38bdf8'
                    )

                # Vẽ các chất
                for i, (name, desc) in enumerate(steps):
                    x = radius * np.cos(angles[i])
                    y = radius * np.sin(angles[i])
                    is_highlight = (i + 1 == highlight_step)
                    color = '#fbbf24' if is_highlight else '#38bdf8'
                    size = 30 if is_highlight else 22
                    fig.add_trace(go.Scatter(
                        x=[x], y=[y], mode='markers+text',
                        marker=dict(size=size, color=color,
                                    line=dict(color='#f8fafc', width=2)),
                        text=[f'<b>{i+1}</b>'],
                        textposition='middle center',
                        textfont=dict(color='#0f172a', size=12),
                        showlegend=False, hoverinfo='skip'
                    ))
                    # Nhãn tên chất
                    label_r = radius + 0.85
                    fig.add_annotation(x=label_r * np.cos(angles[i]),
                                       y=label_r * np.sin(angles[i]),
                                       text=f"<b>{name}</b>",
                                       showarrow=False,
                                       font=dict(color='#f8fafc', size=11),
                                       bgcolor='rgba(15,23,42,0.7)',
                                       borderpad=3)
                    if show_atp:
                        fig.add_annotation(x=(radius + 0.5) * np.cos(angles[i]),
                                           y=(radius + 0.5) * np.sin(angles[i]),
                                           text=desc.replace("\n", "<br>"),
                                           showarrow=False,
                                           font=dict(color='#94a3b8', size=9))

                fig.update_layout(
                    title=f"Chu trình Krebs (Citric Acid Cycle) — Bước {highlight_step}",
                    template="plotly_dark",
                    xaxis=dict(range=[-4.5, 4.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-4.5, 4.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False,
                               scaleanchor='x', scaleratio=1),
                    height=560, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("Krebs"))
            except Exception as err:
                st.error(f"Lỗi vẽ Krebs: {err}")

        with c3:
            st.markdown("##### 📝 Bước hiện tại")
            # ✅ FIX 4: `steps` giờ luôn tồn tại, c3 không còn crash
            st.markdown(f"**Bước {highlight_step}:** {steps[highlight_step-1][0]}")
            st.caption(steps[highlight_step-1][1].replace("\n", " "))
            st.markdown("##### 🔋 Sản phẩm chu trình")
            st.latex(r"3\,NADH + 1\,FADH_2 + 1\,GTP")
            st.latex(r"+ 2\,CO_2")
            st.markdown("##### 📊 Vị trí")
            st.caption("Chất nền ti thể (mitochondrial matrix)")

    # ========== SINH HỌC: SƠ ĐỒ QUANG HỢP ==========
    elif dtype == "photosynthesis":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            intensity = st.slider("Cường độ ánh sáng (%):", 0, 100,
                                  int(data.get("light", 80)), 5, key="sinh_ps_intensity")
            co2_level = st.slider("Nồng độ CO₂ (%):", 0, 100,
                                  int(data.get("co2", 50)), 5, key="sinh_ps_co2")
            show_products = st.checkbox("Hiển thị sản phẩm", value=True, key="sinh_ps_prod")

        with c2:
            try:
                fig = go.Figure()

                # Lục lạp (hình oval)
                fig.add_shape(type="circle", x0=-4, x1=4, y0=-1.8, y1=1.8,
                              line=dict(color='#34d399', width=3),
                              fillcolor='rgba(52,211,153,0.1)')
                fig.add_annotation(x=0, y=2.1, text="<b>Lục lạp (Chloroplast)</b>",
                                   showarrow=False, font=dict(color='#34d399', size=13))

                # Pha sáng (bên trái - màng tilacoit)
                fig.add_shape(type="rect", x0=-3.8, x1=-0.5, y0=-1.5, y1=1.5,
                              line=dict(color='#fbbf24', width=2),
                              fillcolor='rgba(251,191,36,0.15)')
                fig.add_annotation(x=-2.15, y=1.7, text="<b>Pha sáng</b>",
                                   showarrow=False, font=dict(color='#fbbf24', size=12))
                # Mũi tên ánh sáng
                alpha_light = intensity / 100 * 0.8
                fig.add_annotation(x=-2.15, y=2.6, ax=-2.15, ay=1.9,
                                   xref='x', yref='y', axref='x', ayref='y',
                                   text='☀️', showarrow=True, arrowhead=2,
                                   arrowsize=1.5, arrowwidth=2,
                                   arrowcolor=f'rgba(251,191,36,{alpha_light})',
                                   font=dict(size=20))
                # H₂O vào
                fig.add_annotation(x=-4.5, y=-1, text="H₂O",
                                   showarrow=False, font=dict(color='#38bdf8', size=13))
                fig.add_annotation(x=-3.9, y=-1, ax=-4.3, ay=-1,
                                   xref='x', yref='y', axref='x', ayref='y',
                                   text='', showarrow=True, arrowhead=2,
                                   arrowwidth=2, arrowcolor='#38bdf8')
                # O₂ ra
                fig.add_annotation(x=-4.5, y=1, text="O₂",
                                   showarrow=False, font=dict(color='#f43f5e', size=13))
                fig.add_annotation(x=-3.9, y=1, ax=-4.3, ay=1,
                                   xref='x', yref='y', axref='x', ayref='y',
                                   text='', showarrow=True, arrowhead=2,
                                   arrowwidth=2, arrowcolor='#f43f5e')

                # Pha tối (bên phải - chất nền)
                fig.add_shape(type="rect", x0=0.5, x1=3.8, y0=-1.5, y1=1.5,
                              line=dict(color='#a78bfa', width=2),
                              fillcolor='rgba(167,139,250,0.15)')
                fig.add_annotation(x=2.15, y=1.7, text="<b>Pha tối (Calvin)</b>",
                                   showarrow=False, font=dict(color='#a78bfa', size=12))
                # CO₂ vào
                alpha_co2 = co2_level / 100 * 0.8
                fig.add_annotation(x=4.5, y=0, text="CO₂",
                                   showarrow=False, font=dict(color='#94a3b8', size=13))
                fig.add_annotation(x=3.9, y=0, ax=4.3, ay=0,
                                   xref='x', yref='y', axref='x', ayref='y',
                                   text='', showarrow=True, arrowhead=2,
                                   arrowwidth=2,
                                   arrowcolor=f'rgba(148,163,184,{alpha_co2})')

                # ATP/NADPH chuyển từ pha sáng → pha tối
                fig.add_annotation(x=0, y=0.8, ax=-0.5, ay=0.8,
                                   xref='x', yref='y', axref='x', ayref='y',
                                   text='ATP, NADPH', showarrow=True, arrowhead=2,
                                   arrowwidth=2, arrowcolor='#fbbf24',
                                   font=dict(color='#fbbf24', size=11))

                # Sản phẩm glucose
                if show_products:
                    fig.add_annotation(x=2.15, y=-1, text="→ C₆H₁₂O₆ (Glucose)",
                                       showarrow=False, font=dict(color='#34d399', size=14))
                    fig.add_annotation(x=2.15, y=-1.5, text="(Sản phẩm cuối)",
                                       showarrow=False, font=dict(color='#94a3b8', size=10))

                fig.update_layout(
                    title=f"Quang hợp — Ánh sáng {intensity}% · CO₂ {co2_level}%",
                    template="plotly_dark",
                    xaxis=dict(range=[-5.5, 5.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-2.5, 3], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False,
                               scaleanchor='x', scaleratio=1),
                    height=460, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("QuangHop"))
            except Exception as err:
                st.error(f"Lỗi vẽ quang hợp: {err}")

        with c3:
            st.markdown("##### 📝 Phương trình tổng")
            st.latex(r"6CO_2 + 6H_2O \xrightarrow{as} C_6H_{12}O_6 + 6O_2")
            st.markdown("##### ☀️ Pha sáng")
            st.caption("Vị trí: màng tilacoit")
            st.caption("Sản phẩm: ATP, NADPH, O₂")
            st.markdown("##### 🌙 Pha tối")
            st.caption("Vị trí: chất nền lục lạp")
            st.caption("Sản phẩm: Glucose (C₆H₁₂O₆)")
            st.markdown("##### 📊 Hiệu suất ước lượng")
            eff = min(intensity, co2_level) / 100
            st.progress(eff)
            st.caption(f"Hiệu suất ≈ {eff*100:.0f}%")

    # ========== SINH HỌC: LƯỚI THỨC ĂN ==========
    elif dtype == "food_web":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Chọn hệ sinh thái**")
            ecosystem = st.radio(
                "Hệ sinh thái:",
                ["Đồng cỏ", "Rừng nhiệt đới", "Biển"],
                key="sinh_fw_ecosystem"
            )

        # Dữ liệu các loài theo bậc dinh dưỡng
        food_data = {
            "Đồng cỏ": {
                "producers": ["🌾 Cỏ", "🌿 Cây bụi"],
                "primary": ["🦗 Châu chấu", "🐰 Thỏ", "🐭 Chuột đồng"],
                "secondary": ["🐸 Ếch", "🐍 Rắn", "🦊 Cáo"],
                "tertiary": ["🦅 Đại bàng", "🐺 Sói"],
                "edges": [
                    ("Cỏ", "Châu chấu"), ("Cỏ", "Thỏ"), ("Cỏ", "Chuột đồng"),
                    ("Châu chấu", "Ếch"), ("Châu chấu", "Rắn"),
                    ("Thỏ", "Cáo"), ("Thỏ", "Sói"),
                    ("Chuột đồng", "Rắn"), ("Chuột đồng", "Cáo"),
                    ("Ếch", "Rắn"), ("Rắn", "Đại bàng"),
                    ("Cáo", "Đại bàng"), ("Cáo", "Sói"),
                ],
            },
            "Rừng nhiệt đới": {
                "producers": ["🌳 Cây gỗ", "🍃 Lá cây"],
                "primary": ["🐛 Sâu bọ", "🐒 Khỉ", "🦜 Vẹt"],
                "secondary": ["🐦 Chim nhỏ", "🐍 Trăn", "🐆 Báo"],
                "tertiary": ["🦅 Đại bàng", "🐊 Cá sấu"],
                "edges": [
                    ("Lá cây", "Sâu bọ"), ("Lá cây", "Khỉ"), ("Lá cây", "Vẹt"),
                    ("Sâu bọ", "Chim nhỏ"), ("Sâu bọ", "Trăn"),
                    ("Khỉ", "Báo"), ("Vẹt", "Trăn"),
                    ("Chim nhỏ", "Đại bàng"), ("Trăn", "Đại bàng"),
                    ("Báo", "Cá sấu"),
                ],
            },
            "Biển": {
                "producers": ["🦠 Tảo", "🌿 Cỏ biển"],
                "primary": ["🦐 Tôm", "🐟 Cá nhỏ", "🐚 Nghêu"],
                "secondary": ["🐟 Cá vừa", "🦑 Mực", "🦀 Cua"],
                "tertiary": ["🦈 Cá mập", "🐋 Cá voi", "🐬 Cá heo"],
                "edges": [
                    ("Tảo", "Tôm"), ("Tảo", "Cá nhỏ"), ("Cỏ biển", "Nghêu"),
                    ("Tôm", "Cá vừa"), ("Cá nhỏ", "Cá vừa"), ("Cá nhỏ", "Mực"),
                    ("Nghêu", "Cua"),
                    ("Cá vừa", "Cá mập"), ("Mực", "Cá heo"),
                    ("Cua", "Cá voi"), ("Cá vừa", "Cá heo"),
                ],
            },
        }

        data_fw = food_data.get(ecosystem, food_data["Đồng cỏ"])

        with c2:
            try:
                fig = go.Figure()

                # Layout: hàng ngang theo bậc dinh dưỡng
                # Bậc 1 (producers): y = 0
                # Bậc 2 (primary): y = 1
                # Bậc 3 (secondary): y = 2
                # Bậc 4 (tertiary): y = 3
                node_pos = {}

                levels = [
                    (data_fw["producers"], 0, "#34d399", "Sinh vật sản xuất"),
                    (data_fw["primary"], 1, "#38bdf8", "Sinh vật tiêu thụ bậc 1"),
                    (data_fw["secondary"], 2, "#fbbf24", "Sinh vật tiêu thụ bậc 2"),
                    (data_fw["tertiary"], 3, "#f43f5e", "Sinh vật tiêu thụ bậc 3+"),
                ]

                for nodes, y, color, label in levels:
                    n = len(nodes)
                    for i, node in enumerate(nodes):
                        # Lấy tên không có emoji
                        name = node.split(" ", 1)[1] if " " in node else node
                        x = (i - (n - 1) / 2) * 2.5
                        node_pos[name] = (x, y)
                        fig.add_trace(go.Scatter(
                            x=[x], y=[y], mode='markers+text',
                            marker=dict(size=40, color=color,
                                        line=dict(color='#f8fafc', width=2)),
                            text=[node], textposition='middle center',
                            textfont=dict(color='#0f172a', size=14),
                            showlegend=False, hoverinfo='skip'
                        ))
                    # Nhãn bậc
                    fig.add_annotation(x=-5, y=y, text=f"<b>{label}</b>",
                                       showarrow=False,
                                       font=dict(color=color, size=11),
                                       xanchor='right')

                # Vẽ các mối quan hệ (mũi tên)
                for src, tgt in data_fw["edges"]:
                    if src in node_pos and tgt in node_pos:
                        x1, y1 = node_pos[src]
                        x2, y2 = node_pos[tgt]
                        fig.add_annotation(
                            x=x2, y=y2, ax=x1, ay=y1,
                            xref='x', yref='y', axref='x', ayref='y',
                            text='', showarrow=True, arrowhead=2,
                            arrowsize=1.2, arrowwidth=1.5,
                            arrowcolor='rgba(148,163,184,0.6)'
                        )

                fig.update_layout(
                    title=f"Lưới thức ăn — Hệ sinh thái {ecosystem}",
                    template="plotly_dark",
                    xaxis=dict(range=[-6, 6], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    yaxis=dict(range=[-0.5, 3.5], showticklabels=False,
                               backgroundcolor="#0f172a", gridcolor="#1e293b",
                               zeroline=False, showgrid=False),
                    height=480, margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("LuoiThucAn"))
            except Exception as err:
                st.error(f"Lỗi vẽ lưới thức ăn: {err}")

        with c3:
            st.markdown("##### 🌱 Sinh vật sản xuất")
            for p in data_fw["producers"]:
                st.markdown(f"- {p}")
            st.markdown("##### 🐛 Tiêu thụ bậc 1")
            for p in data_fw["primary"]:
                st.markdown(f"- {p}")
            st.markdown("##### 🐍 Tiêu thụ bậc 2")
            for p in data_fw["secondary"]:
                st.markdown(f"- {p}")
            st.markdown("##### 🦅 Tiêu thụ bậc 3+")
            for p in data_fw["tertiary"]:
                st.markdown(f"- {p}")
            st.caption(f"Tổng cộng **{sum(len(v) for v in data_fw.values() if isinstance(v, list))}** loài")

    # ========== SINH HỌC: CHU KỲ TIM ==========
    elif dtype == "heart_cycle":
        c1, c2, c3 = st.columns([0.8, 3.2, 1])
        with c1:
            st.markdown("**⚙️ Thông số**")
            bpm = st.slider("Nhịp tim (bpm):", 50, 120,
                            int(data.get("bpm", 75)), 5, key="sinh_heart_bpm")
            show_pressure = st.checkbox("Hiển thị áp suất", value=True, key="sinh_heart_pressure")

        with c2:
            try:
                # 1 chu kỳ tim ~ 0.8s (75 bpm)
                cycle_time = 60.0 / bpm  # giây
                t = np.linspace(0, cycle_time, 500)

                # Mô phỏng áp suất tâm thất trái theo thời gian
                # Pha 1: Tâm nhĩ thu (~0.1s)
                # Pha 2: Tâm thất thu (~0.3s)
                # Pha 3: Tâm trương (~0.4s)
                phase_atrial = 0.125 * cycle_time
                phase_ventricular = 0.375 * cycle_time
                phase_diastole = 0.5 * cycle_time

                # Áp suất tâm thất trái (mmHg) - đơn giản hóa
                p_ventricle = np.zeros_like(t)
                for i, ti in enumerate(t):
                    if ti < phase_atrial:
                        p_ventricle[i] = 5 + 5 * np.sin(np.pi * ti / phase_atrial)
                    elif ti < phase_atrial + phase_ventricular:
                        # Tâm thất thu — áp suất tăng vọt
                        phase_t = (ti - phase_atrial) / phase_ventricular
                        p_ventricle[i] = 5 + 115 * (1 - np.exp(-6 * phase_t))
                    else:
                        # Tâm trương
                        phase_t = (ti - phase_atrial - phase_ventricular) / phase_diastole
                        p_ventricle[i] = 120 * np.exp(-3 * phase_t) + 5

                fig = go.Figure()

                if show_pressure:
                    fig.add_trace(go.Scatter(x=t, y=p_ventricle, mode='lines',
                        line=dict(color='#ef4444', width=3),
                        name='Áp suất tâm thất trái (mmHg)',
                        hovertemplate="t = %{x:.2f}s<br>P = %{y:.1f} mmHg<extra></extra>"))

                # Đường phân chia các pha
                fig.add_vline(x=phase_atrial, line=dict(color='#fbbf24', width=2, dash='dash'),
                              annotation_text="Nhĩ thu kết thúc", annotation_position="top")
                fig.add_vline(x=phase_atrial + phase_ventricular,
                              line=dict(color='#3b82f6', width=2, dash='dash'),
                              annotation_text="Thất thu kết thúc", annotation_position="top")

                # Nhãn pha
                fig.add_annotation(x=phase_atrial/2, y=130, text="<b>Nhĩ thu</b>",
                                   showarrow=False, font=dict(color='#fbbf24', size=13))
                fig.add_annotation(x=phase_atrial + phase_ventricular/2, y=130,
                                   text="<b>Thất thu</b>",
                                   showarrow=False, font=dict(color='#ef4444', size=13))
                fig.add_annotation(x=phase_atrial + phase_ventricular + phase_diastole/2, y=130,
                                   text="<b>Tâm trương</b>",
                                   showarrow=False, font=dict(color='#34d399', size=13))

                fig.update_layout(
                    title=f"Chu kỳ tim — Nhịp {bpm} bpm (1 chu kỳ = {cycle_time:.2f}s)",
                    template="plotly_dark",
                    xaxis=dict(title="Thời gian (s)", backgroundcolor="#0f172a",
                               gridcolor="#1e293b", zeroline=False),
                    yaxis=dict(title="Áp suất (mmHg)", range=[0, 145],
                               backgroundcolor="#0f172a", gridcolor="#1e293b", zeroline=False),
                    height=420, margin=dict(l=10, r=10, t=40, b=30),
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True, config=_plotly_config("ChuKyTim"))
            except Exception as err:
                st.error(f"Lỗi vẽ chu kỳ tim: {err}")

        with c3:
            st.markdown("##### ⏱ Thời gian các pha")
            st.markdown(f"- **Nhĩ thu:** {phase_atrial:.2f}s")
            st.markdown(f"- **Thất thu:** {phase_ventricular:.2f}s")
            st.markdown(f"- **Tâm trương:** {phase_diastole:.2f}s")
            st.markdown("##### 📊 Áp suất điển hình")
            st.latex(r"P_{tâm\ thất\ trái} \approx 120/80\,mmHg")
            st.latex(r"P_{tâm\ nhĩ} \approx 5\,mmHg")
            st.markdown("##### 🔄 Chu kỳ")
            st.caption(f"Với {bpm} bpm → 1 phút có **{bpm}** chu kỳ tim")

    else:
        st.info("💡 Đã tiếp nhận yêu cầu. Kéo thanh trượt hoặc nhập tham số để mô phỏng tương tác!")


# ==============================================================================
# TEXT-ONLY PROMPT
# ==============================================================================
def _build_text_only_prompt(lab_request, subject, grade_num):
    if subject == "Hóa học":
        structure = """1. PHƯƠNG TRÌNH PHẢN ỨNG
Viết phương trình hóa học đầy đủ (đã cân bằng), ghi rõ điều kiện phản ứng (nhiệt độ, xúc tác, ánh sáng...). Dùng LaTeX trong cặp dấu $...$ cho công thức.

2. TÊN GỌI CÁC CHẤT
Liệt kê từng chất tham gia và sản phẩm: tên thường gọi, tên khoa học, công thức phân tử, vai trò trong phản ứng.

3. CÁC BƯỚC TIẾN HÀNH THÍ NGHIỆM
Mô tả chi tiết từng bước theo trình tự chuẩn phòng thí nghiệm: chuẩn bị dụng cụ, hóa chất, tiến hành, quan sát.

4. HIỆN TƯỢNG QUAN SÁT ĐƯỢC
Mô tả hiện tượng cụ thể: kết tủa (màu gì), sủi bọt khí, đổi màu dung dịch, tỏa nhiệt, phát sáng, mùi đặc trưng...

5. GIẢI THÍCH BẢN CHẤT
Giải thích hiện tượng bằng kiến thức hóa học, viết phương trình ion thu gọn (nếu có)."""
    elif subject == "Sinh học":
        structure = """1. KHÁI NIỆM / ĐỊNH NGHĨA
Nêu rõ khái niệm, định nghĩa chuẩn theo SGK Kết Nối Tri Thức.

2. CƠ CHẾ / DIỄN BIẾN
Mô tả chi tiết cơ chế, các giai đoạn, các yếu tố tham gia, mối quan hệ nhân quả.

3. Ý NGHĨA SINH HỌC
Ý nghĩa của quá trình / cấu trúc đối với sinh vật, đối với hệ sinh thái.

4. ỨNG DỤNG / LIÊN HỆ THỰC TẾ
Ứng dụng trong đời sống, y học, nông nghiệp, công nghệ sinh học..."""
    else:
        structure = """1. BỐI CẢNH / ĐIỀU KIỆN
Trình bày bối cảnh lịch sử hoặc điều kiện tự nhiên - kinh tế - xã hội liên quan.

2. DIỄN BIẾN CHÍNH
Trình bày diễn biến theo trình tự thời gian hoặc không gian rõ ràng, có mốc cụ thể.

3. KẾT QUẢ / Ý NGHĨA
Nêu kết quả và ý nghĩa của sự kiện / hiện tượng.

4. LIÊN HỆ MỞ RỘNG
Liên hệ với kiến thức liên quan, bài học kinh nghiệm, xu hướng hiện nay."""

    return f"""Bạn là giáo viên chuyên môn cao, soạn tài liệu theo chuẩn chương trình giáo dục phổ thông mới nhất bộ sách "Kết Nối Tri Thức Với Cuộc Sống".

YÊU CẦU CỦA HỌC SINH: {lab_request}
MÔN: {subject} - Lớp {grade_num}

QUY TẮC BẮT BUỘC:
1. TOÀN BỘ nội dung bằng TIẾNG VIỆT chuẩn xác, không có từ tiếng Anh xen lẫn.
2. KHÔNG DÙNG DẤU #.
3. Công thức hóa học, ký hiệu khoa học: dùng LaTeX đặt trong cặp dấu $...$.
4. TUYỆT ĐỐI KHÔNG sinh code Python, KHÔNG sinh thẻ <PLOT_2D>, <PLOT_3D> hay <PLOT>.
5. KHÔNG vẽ đồ thị, không vẽ hình — chỉ trả về nội dung văn bản thuần.
6. KHÔNG có mục "MÃ VẼ ĐỒ THỊ" hay bất kỳ mục nào liên quan đến code vẽ. Chỉ có ĐÚNG các mục đã liệt kê ở CẤU TRÚC ĐẦU RA, không thêm mục mới.
7. Kiến thức phải cực kỳ chính xác, khoa học, sư phạm theo đúng sách Kết Nối Tri Thức.

CẤU TRÚC ĐẦU RA BẮT BUỘC:

{structure}

LƯU Ý CUỐI:
- Chỉ trả lời bằng văn bản, KHÔNG có code Python, KHÔNG có thẻ XML nào.
- Trình bày rõ ràng, có xuống dòng giữa các mục lớn."""


# ==============================================================================
# RENDER TEXT BLOCK
# ==============================================================================
def render_lab_text_block(text):
    if not text or not text.strip():
        return
    heading_re = re.compile(r"^(?:\d{1,2}|[IVX]{1,4})\.\s+\S")
    with st.container(border=True):
        buffer = []
        def flush():
            if buffer:
                block = "\n".join(buffer).strip()
                if block:
                    st.markdown(block)
                buffer.clear()
        for line in text.split("\n"):
            s = line.strip()
            if s and len(s) < 100 and heading_re.match(s):
                flush()
                st.markdown(
                    f"<div style='background: linear-gradient(135deg, #0ea5e9, #38bdf8); "
                    f"color: white; padding: 12px 18px; border-radius: 10px; "
                    f"font-weight: 800; font-size: 1.05rem; margin: 22px 0 12px 0; "
                    f"border-left: 6px solid #0284c7; "
                    f"box-shadow: 0 3px 10px rgba(14,165,233,0.25); "
                    f"letter-spacing: 0.3px;'>{s}</div>",
                    unsafe_allow_html=True,
                )
            else:
                buffer.append(line)
        flush()


# ==============================================================================
# CLEAN AI RESPONSE
# ==============================================================================
def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(r"(#{1,3}\s*)?📌?\s*1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI", re.IGNORECASE | re.UNICODE)
    match = pattern.search(text)
    if match:
        text = text[match.start():]
    text = re.sub(r"^[ \t]*#{1,6}[ \t]*", "", text, flags=re.MULTILINE)
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
        r")", re.IGNORECASE
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


# ==============================================================================
# STRIP PLOT SECTION
# ==============================================================================
def strip_plot_section_from_text(text):
    if not text:
        return text
    pattern = re.compile(
        r"^\s*\d+\.\s*(MÃ\s*VẼ\s*ĐỒ\s*THỊ|VẼ\s*ĐỒ\s*THỊ|CODE\s*VẼ|PLOT|SƠ\s*ĐỒ\s*CODE|MÃ\s*PLOT)[^\n]*$",
        re.IGNORECASE | re.MULTILINE | re.UNICODE,
    )
    m = pattern.search(text)
    if m:
        text = text[:m.start()].rstrip()
    return text

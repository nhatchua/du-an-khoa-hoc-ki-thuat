# ==============================================================================
# _exam.py — Tab 3: Khảo thí độc lập
# ==============================================================================
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import re
import json
import random
from datetime import datetime
from _config import VN_TZ, get_vn_time
from _ai_client import call_gemini_with_fallback
from _curriculum import BIGDATA_CURRICULUM
from _lab import setup_pedagogical_oxy


# ==============================================================================
# HELPER: VẼ BẢNG BIẾN THIÊN + ĐỒ THỊ MINI (0-TOKEN)
# ==============================================================================
def _render_fast_visual(q):
    """Vẽ bảng biến thiên + đồ thị mini từ dữ liệu AI đã sinh (không gọi lại AI)."""
    if q.get("bbt"):
        raw_bbt = str(q["bbt"])
        raw_bbt = re.sub(r'\\+nearrow\b', '↗', raw_bbt)
        raw_bbt = re.sub(r'\\+searrow\b', '↘', raw_bbt)
        raw_bbt = re.sub(r'[\r\n]+\s*earrow\b', ' ↗ ', raw_bbt)
        raw_bbt = raw_bbt.replace('>>', '↗').replace('>', '↗').replace('\\n', '\n').strip()

        lines = [l.strip() for l in raw_bbt.split('\n') if l.strip() and '---' not in l]
        rows = []
        for line in lines:
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if parts:
                rows.append(parts)

        if rows:
            max_cols = max(len(r) for r in rows)
            for r in rows:
                while len(r) < max_cols:
                    r.append("")

            st.caption("📋 **Bảng biến thiên:**")
            html = '<div style="background-color: #0f172a; padding: 6px 10px; border-radius: 8px; border: 1.5px solid #334155; margin: 4px 0 8px 0; overflow-x: auto; max-width: 620px;">'
            html += '<table style="width: 100%; border-collapse: collapse; text-align: center; color: #f8fafc; font-size: 13px; font-family: \'Times New Roman\', serif;">'
            for row in rows:
                html += '<tr style="border-bottom: 1px solid #1e293b;">'
                for c_idx, cell in enumerate(row):
                    c_disp = cell.replace('+\\infty', '+∞').replace('-\\infty', '-∞').replace('+inf', '+∞').replace('-inf', '-∞').replace('$', '').strip()
                    if '||' in c_disp:
                        c_disp = '<span style="color:#f59e0b; font-weight:bold;">||</span>'
                    elif '↗' in c_disp:
                        c_disp = f'<span style="color:#38bdf8; font-weight:bold; font-size:14px;">{c_disp}</span>'
                    elif '↘' in c_disp:
                        c_disp = f'<span style="color:#f87171; font-weight:bold; font-size:14px;">{c_disp}</span>'
                    border_r = "border-right: 1.5px solid #334155;" if c_idx == 0 else "border-right: 1px dashed #1e293b;"
                    bg_h = "background-color: #1e293b; font-weight: bold; width: 45px; color: #38bdf8;" if c_idx == 0 else "min-width: 40px;"
                    html += f'<td style="padding: 4px 8px; {border_r} {bg_h}">{c_disp}</td>'
                html += '</tr>'
            html += '</table></div>'
            st.markdown(html, unsafe_allow_html=True)

    if q.get("f"):
        f_data = q["f"]
        if isinstance(f_data, dict):
            with st.expander("📈 Xem Đồ thị Oxy (Thu gọn chuẩn mực)", expanded=True):
                try:
                    dtype = f_data.get("type")
                    fig_mini = go.Figure()

                    def fmt_c(val):
                        if val is None or np.isnan(val) or np.isinf(val):
                            return ""
                        r = round(val)
                        return str(int(r)) if abs(val - r) < 1e-2 else f"{val:.1f}".rstrip('0').rstrip('.')

                    if dtype == "func_3":
                        fa, fb = float(f_data.get("a", 0)), float(f_data.get("b", 0))
                        fc, fd = float(f_data.get("c", 0)), float(f_data.get("d", 0))

                        delta_prime = fb**2 - 3*fa*fc
                        crit_pts = []
                        if delta_prime > 1e-4 and fa != 0:
                            x1 = (-fb - np.sqrt(delta_prime)) / (3*fa)
                            x2 = (-fb + np.sqrt(delta_prime)) / (3*fa)
                            y1 = fa*(x1**3) + fb*(x1**2) + fc*x1 + fd
                            y2 = fa*(x2**3) + fb*(x2**2) + fc*x2 + fd
                            is_max1 = (6*fa*x1 + 2*fb < 0)
                            crit_pts = [(x1, y1, "CĐ" if is_max1 else "CT", is_max1),
                                        (x2, y2, "CT" if is_max1 else "CĐ", not is_max1)]
                        all_x = [pt[0] for pt in crit_pts] if crit_pts else [0.0]
                        all_y = [pt[1] for pt in crit_pts] if crit_pts else [0.0]
                        x_min, x_max = min(all_x) - 2.5, max(all_x) + 2.5
                        y_min, y_max = min(all_y) - 3.0, max(all_y) + 3.0

                        xv = np.linspace(x_min, x_max, 500)
                        yv = fa*(xv**3) + fb*(xv**2) + fc*xv + fd
                        fig_mini.add_trace(go.Scatter(x=xv, y=yv, mode='lines',
                                                       line=dict(color='#38bdf8', width=2.4),
                                                       hoverinfo='skip', showlegend=False))

                        for x_pt, y_pt, label, is_max in crit_pts:
                            fig_mini.add_trace(go.Scatter(x=[x_pt, x_pt], y=[0, y_pt], mode='lines',
                                                           line=dict(color='#94a3b8', width=1.2, dash='dot'),
                                                           hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[0, x_pt], y=[y_pt, y_pt], mode='lines',
                                                           line=dict(color='#94a3b8', width=1.2, dash='dot'),
                                                           hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[x_pt], y=[y_pt], mode='markers+text',
                                                           marker=dict(size=6, color='#fbbf24', line=dict(color='#ffffff', width=1)),
                                                           text=[f"{label}({fmt_c(x_pt)};{fmt_c(y_pt)})"],
                                                           textposition="top center" if is_max else "bottom center",
                                                           font=dict(color='#fbbf24', size=11), showlegend=False))

                        if abs(fa) > 1e-4:
                            xu = -fb / (3*fa)
                            yu = fa*(xu**3) + fb*(xu**2) + fc*xu + fd
                            fig_mini.add_trace(go.Scatter(x=[xu], y=[yu], mode='markers+text',
                                                           marker=dict(size=5, color='#c084fc'),
                                                           text=[f"U({fmt_c(xu)};{fmt_c(yu)})"],
                                                           textposition="top right",
                                                           font=dict(color='#c084fc', size=10), showlegend=False))
                        setup_pedagogical_oxy(fig_mini, [x_min, x_max], [y_min, y_max])
                        fig_mini.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig_mini, use_container_width=True)

                    elif dtype == "func_1_1":
                        fa, fb = float(f_data.get("a", 0)), float(f_data.get("b", 0))
                        fc, fd = float(f_data.get("c", 0)), float(f_data.get("d", 0))
                        if fc != 0:
                            x_tc = -fd / fc
                            y_tc = fa / fc
                            x_min, x_max = x_tc - 4.5, x_tc + 4.5
                            y_min, y_max = y_tc - 4.5, y_tc + 4.5

                            xl = np.linspace(x_min, x_tc - 0.05, 250)
                            xr = np.linspace(x_tc + 0.05, x_max, 250)
                            yl = (fa*xl + fb)/(fc*xl + fd)
                            yr = (fa*xr + fb)/(fc*xr + fd)
                            yl[np.abs(yl) > 12] = np.nan
                            yr[np.abs(yr) > 12] = np.nan

                            fig_mini.add_trace(go.Scatter(x=xl, y=yl, mode='lines', line=dict(color='#38bdf8', width=2.4), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=xr, y=yr, mode='lines', line=dict(color='#38bdf8', width=2.4), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[x_tc, x_tc], y=[y_min, y_max], mode='lines', line=dict(color='#f59e0b', width=1.4, dash='dash'), hoverinfo='skip', showlegend=False))
                            fig_mini.add_annotation(x=x_tc, y=y_max - 0.5, text=f"x={fmt_c(x_tc)}", showarrow=False, font=dict(color='#f59e0b', size=11))
                            fig_mini.add_trace(go.Scatter(x=[x_min, x_max], y=[y_tc, y_tc], mode='lines', line=dict(color='#10b981', width=1.4, dash='dash'), hoverinfo='skip', showlegend=False))
                            fig_mini.add_annotation(x=x_max - 0.8, y=y_tc + 0.5, text=f"y={fmt_c(y_tc)}", showarrow=False, font=dict(color='#10b981', size=11))
                            fig_mini.add_trace(go.Scatter(x=[x_tc], y=[y_tc], mode='markers+text', marker=dict(size=6, color='#38bdf8'), text=[f"I({fmt_c(x_tc)};{fmt_c(y_tc)})"], textposition="top right", font=dict(size=10, color='#38bdf8'), showlegend=False))

                            setup_pedagogical_oxy(fig_mini, [x_min, x_max], [y_min, y_max])
                            fig_mini.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig_mini, use_container_width=True)

                    elif dtype == "func_2_1":
                        fa, fb, fc = float(f_data.get("a", 0)), float(f_data.get("b", 0)), float(f_data.get("c", 0))
                        fd, fe = float(f_data.get("d", 0)), float(f_data.get("e", 0))
                        if fd != 0:
                            x_tc = -fe / fd
                            m_s = fa / fd
                            n_s = (fb - m_s * fe) / fd
                            x_min, x_max = x_tc - 4.5, x_tc + 4.5
                            y_min = m_s * x_min + n_s - 4.0
                            y_max = m_s * x_max + n_s + 4.0

                            xl = np.linspace(x_min, x_tc - 0.05, 250)
                            xr = np.linspace(x_tc + 0.05, x_max, 250)
                            yl = (fa*xl**2 + fb*xl + fc)/(fd*xl + fe)
                            yr = (fa*xr**2 + fb*xr + fc)/(fd*xr + fe)
                            yl[np.abs(yl) > 15] = np.nan
                            yr[np.abs(yr) > 15] = np.nan

                            fig_mini.add_trace(go.Scatter(x=xl, y=yl, mode='lines', line=dict(color='#38bdf8', width=2.4), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=xr, y=yr, mode='lines', line=dict(color='#38bdf8', width=2.4), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[x_tc, x_tc], y=[y_min, y_max], mode='lines', line=dict(color='#f59e0b', width=1.4, dash='dash'), hoverinfo='skip', showlegend=False))
                            fig_mini.add_annotation(x=x_tc, y=y_max - 0.8, text=f"x={fmt_c(x_tc)}", showarrow=False, font=dict(color='#f59e0b', size=11))

                            xs_line = np.linspace(x_min, x_max, 100)
                            ys_line = m_s * xs_line + n_s
                            fig_mini.add_trace(go.Scatter(x=xs_line, y=ys_line, mode='lines', line=dict(color='#ec4899', width=1.4, dash='dash'), hoverinfo='skip', showlegend=False))

                            setup_pedagogical_oxy(fig_mini, [x_min, x_max], [y_min, y_max])
                            fig_mini.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig_mini, use_container_width=True)

                    elif dtype == "parabola":
                        fa, fb, fc = float(f_data.get("a", 0)), float(f_data.get("b", 0)), float(f_data.get("c", 0))
                        if fa != 0:
                            x_dinh = -fb / (2*fa)
                            y_dinh = fa*(x_dinh**2) + fb*x_dinh + fc
                            x_min, x_max = x_dinh - 3.5, x_dinh + 3.5
                            y_min, y_max = y_dinh - 4.0, y_dinh + 4.0
                            xv = np.linspace(x_min, x_max, 400)
                            yv = fa*(xv**2) + fb*xv + fc
                            fig_mini.add_trace(go.Scatter(x=xv, y=yv, mode='lines', line=dict(color='#38bdf8', width=2.4), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[x_dinh, x_dinh], y=[y_min, y_max], mode='lines', line=dict(color='#f59e0b', width=1.4, dash='dash'), hoverinfo='skip', showlegend=False))
                            fig_mini.add_trace(go.Scatter(x=[x_dinh], y=[y_dinh], mode='markers+text', marker=dict(size=6, color='gold'), text=[f'I({fmt_c(x_dinh)};{fmt_c(y_dinh)})'], textposition="top center", font=dict(size=11, color='gold'), showlegend=False))
                            setup_pedagogical_oxy(fig_mini, [x_min, x_max], [y_min, y_max])
                            fig_mini.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig_mini, use_container_width=True)
                except Exception:
                    pass
        elif isinstance(f_data, str) and f_data.strip():
            clean_str = f_data.replace('**', '^').replace('*', '').replace(' ', '')
            st.latex("y = " + clean_str)


# ==============================================================================
# HELPER: PARSE JSON ĐỀ THI AN TOÀN
# ==============================================================================
def _parse_exam_json_safely(raw_str):
    """Parse JSON đề thi với cơ chế chống vỡ."""
    start_idx = raw_str.find('{')
    if start_idx == -1:
        raise ValueError("AI không phản hồi cấu trúc JSON hợp lệ.")
    s = raw_str[start_idx:].strip()
    s = re.sub(r',\s*([\]}])', r'\1', s)

    res, i, n, in_str = [], 0, len(s), False
    while i < n:
        c = s[i]
        if c == '"':
            k, bs = len(res) - 1, 0
            while k >= 0 and res[k] == '\\':
                bs += 1
                k -= 1
            if bs % 2 == 0:
                in_str = not in_str
            res.append(c); i += 1
        elif c == '\\' and in_str:
            if i + 1 < n:
                nxt = s[i + 1]
                if nxt in ['"', '\\', '/']:
                    res.extend(['\\', nxt]); i += 2
                elif nxt in ['n', 'r', 't', 'b', 'f']:
                    if i + 2 < n and s[i + 2].isalpha():
                        res.extend(['\\\\', nxt])
                    else:
                        res.extend(['\\', nxt])
                    i += 2
                elif nxt == 'u' and i + 5 < n and all(ch in '0123456789abcdefABCDEF' for ch in s[i + 2:i + 6]):
                    res.extend(['\\', 'u']); i += 2
                else:
                    res.extend(['\\\\', nxt]); i += 2
            else:
                res.append('\\\\'); i += 1
        else:
            res.append(c); i += 1

    repaired_str = "".join(res)
    decoder = json.JSONDecoder(strict=False)
    obj, _ = decoder.raw_decode(repaired_str)
    return obj


# ==============================================================================
# HELPER: SANITIZE LATEX
# ==============================================================================
def _sanitize_latex(txt):
    """Escape ký tự đặc biệt LaTeX, giữ nguyên phần trong $...$."""
    if not txt:
        return ""
    pts = re.split(r'(\$.*?\$)', str(txt), flags=re.DOTALL)
    for i in range(0, len(pts), 2):
        pts[i] = re.sub(r'(?<!\\)&', r'\&', pts[i])
        pts[i] = re.sub(r'(?<!\\)%', r'\%', pts[i])
        pts[i] = re.sub(r'(?<!\\)_', r'\_', pts[i])
        pts[i] = re.sub(r'(?<!\\)#', r'\#', pts[i])
    return "".join(pts)


# ==============================================================================
# HÀM CHÍNH: RENDER TAB 3
# ==============================================================================
def render_tab_exam(grade, subject):
    """Render toàn bộ Tab 3 (Khảo thí độc lập)."""
    student_name = st.session_state.get("student_name", "Ẩn danh")
    sheet_webhook_url = st.session_state.get("sheet_webhook_url", "")
    grade_num = int(grade.split()[1])

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📝 Trạm 3: Khảo Thí Độc Lập - Môn {subject} (Lớp {grade_num})")
    st.caption("Cấu trúc Khảo thí 2026 (Theo QĐ 764/QĐ-BGDĐT) • Tối ưu hóa Token 60% • Dựng đồ thị 0-Token • Thang điểm chuẩn Bộ.")

    # ============ STATE MACHINE ============
    if st.session_state.exam_state == "config":
        _render_exam_config(grade, subject, grade_num)
    elif st.session_state.exam_state == "doing":
        _render_exam_doing(grade, subject, grade_num, student_name)
    elif st.session_state.exam_state == "result":
        _render_exam_result(grade, subject, grade_num, student_name, sheet_webhook_url)
    else:
        st.session_state.exam_state = "config"
        st.rerun()


# ==============================================================================
# STATE 1: CONFIG
# ==============================================================================
def _render_exam_config(grade, subject, grade_num):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📊 Cấu hình chuyên đề khảo thí chuẩn CT GDPT 2018:")
    selected_matrix_topics = []

    if grade_num in [10, 11, 12] and subject in BIGDATA_CURRICULUM:
        available_grades = [g for g in [12, 11, 10] if g <= grade_num]
        for g in available_grades:
            if g in BIGDATA_CURRICULUM[subject]:
                is_current = (g == grade_num)
                exp_title = f"🎯 KHỐI LỚP {g} -- TRỌNG TÂM ĐÁNH GIÁ (BẮT BUỘC)" if is_current else f"🔁 KHỐI LỚP {g} -- ÔN TẬP LIÊN KHỐI / NỀN TẢNG (TÙY CHỌN)"
                with st.expander(exp_title, expanded=is_current):
                    topics_g = BIGDATA_CURRICULUM[subject][g]
                    c_chk1, c_chk2 = st.columns(2)
                    for i, top in enumerate(topics_g):
                        with (c_chk1 if i % 2 == 0 else c_chk2):
                            default_val = (is_current and i < 3)
                            chk_key = f"chk_mat_{subject}_{grade_num}_{g}_{i}"
                            if st.checkbox(top, value=default_val, key=chk_key):
                                selected_matrix_topics.append(f"[Lớp {g}] {top}")
    elif subject in BIGDATA_CURRICULUM and grade_num in BIGDATA_CURRICULUM[subject]:
        with st.expander(f"📚 Chuyên đề môn {subject} (Lớp {grade_num} - SGK KNTT)", expanded=True):
            topics_curr = BIGDATA_CURRICULUM[subject][grade_num]
            c_chk1, c_chk2 = st.columns(2)
            for i, top in enumerate(topics_curr):
                with (c_chk1 if i % 2 == 0 else c_chk2):
                    chk_key = f"chk_thcs_{subject}_{grade_num}_{i}"
                    if st.checkbox(top, value=(i < 3), key=chk_key):
                        selected_matrix_topics.append(top)
    else:
        with st.expander(f"📚 Chuyên đề ôn tập Lớp {grade_num}", expanded=True):
            for i in range(1, 5):
                t_name = f"Chuyên đề {i}: Kiến thức trọng tâm Học kỳ {i if i <= 2 else 'Tổng hợp'} môn {subject}"
                if st.checkbox(t_name, value=(i <= 2), key=f"chk_df_{subject}_{grade_num}_{i}"):
                    selected_matrix_topics.append(t_name)

    if subject == "Ngữ văn":
        total_p1, total_p2, total_p3 = 0, 0, 0
        default_time = 120
        st.info(f"📝 **Môn Ngữ văn (Lớp {grade_num}):** Đúng 120 phút. 100% Tự luận (Đọc hiểu 4.0đ + Viết 6.0đ).")
    elif subject == "Tiếng Anh":
        c_en1, c_en2 = st.columns([2, 1])
        with c_en1:
            exam_preset_en = st.radio("Chế độ khảo thí:",
                ["⚡ Luyện phản xạ (15 câu - 20 phút)", "🏆 Chuẩn cấu trúc Bộ 2026 (40 câu - 50 phút)"],
                horizontal=True)
        if "Luyện phản xạ" in exam_preset_en:
            def_p1 = 15
            default_time = 20
        else:
            def_p1 = 40
            default_time = 50
        total_p2, total_p3 = 0, 0
        max_p1 = 10.0
        with c_en2:
            total_p1 = st.number_input(f"Số câu trắc nghiệm (Tổng {max_p1}đ):", 1, 50, def_p1)
        st.info(f"⏱ Thời gian làm bài: **{default_time} phút**. Mỗi câu TN có giá trị tương ứng để tổng là 10.0đ.")
    else:
        if subject == "Toán học":
            moet_time = 90
            def_p1, def_p2, def_p3 = 12, 4, 6
            max_p1, max_p2, max_p3 = 3.0, 4.0, 3.0
            pt_p1, pt_p3 = 0.25, 0.5
        elif subject in ["Vật lý", "Hóa học", "Sinh học", "Khoa học tự nhiên"]:
            moet_time = 50
            def_p1, def_p2, def_p3 = 18, 4, 6
            max_p1, max_p2, max_p3 = 4.5, 4.0, 1.5
            pt_p1, pt_p3 = 0.25, 0.25
        else:
            moet_time = 50
            def_p1, def_p2, def_p3 = 24, 4, 0
            max_p1, max_p2, max_p3 = 6.0, 4.0, 0.0
            pt_p1, pt_p3 = 0.25, 0

        c_mode1, c_mode2 = st.columns([2, 1])
        with c_mode1:
            exam_preset = st.radio(f"Chế độ khảo thí môn {subject}:",
                ["⚡ Luyện phản xạ siêu tốc", "🏆 Chuẩn cấu trúc Bộ 2026 (Đầy đủ 3 phần)"],
                horizontal=True)

        if "Luyện phản xạ" in exam_preset:
            def_p1, def_p2, def_p3 = max(1, def_p1 // 2), max(0, def_p2 // 2), max(0, def_p3 // 2)
            default_time = max(15, moet_time // 2)
        else:
            default_time = moet_time

        st.info(f"⏱ Thời gian: **{default_time} phút**. Cấu trúc: P1 ({def_p1} câu x {pt_p1}đ) | P2 ({def_p2} câu Đ/S x tối đa 1.0đ) | P3 ({def_p3} câu TLN x {pt_p3}đ).")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            total_p1 = st.number_input(f"Số câu TN (Phần I - {max_p1}đ):", 0, 40, def_p1)
        with col_m2:
            total_p2 = st.number_input(f"Số câu Đ/S (Phần II - {max_p2}đ):", 0, 8, def_p2)
        with col_m3:
            total_p3 = st.number_input(f"Số câu TLN (Phần III - {max_p3}đ):", 0, 10, def_p3)

    exam_level = st.select_slider("Mức độ phân hóa đề thi:",
        ["Cơ bản (NB - TH)", "Chuẩn cấu trúc Bộ 2026 (NB - TH - VD)", "Nâng cao (VD - VDC)"],
        value="Chuẩn cấu trúc Bộ 2026 (NB - TH - VD)")

    matrix_notes = st.text_area(
        "✍️ Yêu cầu / Ý đồ ra đề chi tiết (tùy chỉnh của Thầy / Trò):",
        placeholder="Ví dụ: Ưu tiên câu hỏi có đồ thị hoặc bảng biến thiên, tập trung khảo sát hàm phân thức, tích phân thực tế...",
        key=f"exam_custom_notes_{subject}_{grade_num}"
    )

    if st.button(f"🚀 Khởi tạo đề thi ({default_time} phút)"):
        if not selected_matrix_topics and subject not in ["Ngữ văn", "Tiếng Anh"]:
            st.warning("⚠️ Vui lòng tích chọn ít nhất một chuyên đề kiến thức!")
        else:
            topics_str = ", ".join(selected_matrix_topics) if selected_matrix_topics else f"Toàn bộ chương trình môn {subject} Lớp {grade_num}"
            exam_seed = random.randint(1000, 9999)
            now_str = datetime.now(VN_TZ).strftime("%H%M%S")

            with st.spinner("⚡ AI đang nén Token siêu tốc & phân luồng ma trận đề thi..."):
                exam_prompt = _build_exam_prompt(
                    subject, grade_num, topics_str, exam_level, matrix_notes,
                    exam_seed, now_str, total_p1, total_p2, total_p3
                )
                try:
                    raw_json = call_gemini_with_fallback(exam_prompt, json_mode=True)
                    parsed = _parse_exam_json_safely(raw_json)
                    if not isinstance(parsed, dict):
                        raise ValueError("Dữ liệu đề thi không khớp cấu trúc JSON.")

                    st.session_state.exam_data = parsed
                    st.session_state.exam_state = "doing"
                    st.session_state.violation_count = 0
                    st.session_state.exam_answers = {}
                    st.session_state.tram3_chat_messages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khởi tạo đề thi: {e}")


def _build_exam_prompt(subject, grade_num, topics_str, exam_level, matrix_notes,
                       exam_seed, now_str, total_p1, total_p2, total_p3):
    """Sinh prompt đề thi theo môn (dùng cho state config)."""
    if subject == "Ngữ văn":
        return f"""[CHUYÊN GIA KHẢO THÍ NGỮ VĂN GDPT 2018 - LỚP {grade_num}]
[MÃ ĐỀ NGẪU NHIÊN: {exam_seed} - PHIÊN: {now_str}]
Chuyên đề: [{topics_str}]. Mức độ: {exam_level}. Ghi chú riêng: "{matrix_notes}".
QUY ĐỊNH BẮT BUỘC (QĐ 764/QĐ-BGDĐT): Ngữ liệu đọc hiểu lấy NGOÀI SGK theo đúng thể loại KNTT Lớp {grade_num}. 
TỐI ƯU TOKEN: "h" và "exp" từ 15-25 từ.
JSON FORMAT DUY NHẤT:
{{"part_doc_hieu": {{"text": "Đoạn trích ngắn có nguồn...", "questions": [{{"q": "Câu hỏi...", "h": "Gợi ý chi tiết...", "exp": "Đáp án chi tiết..."}}]}}, "part_viet": [{{"type": "NLXH", "q": "Đoạn văn 200 chữ...", "h": "Dàn ý...", "exp": "Tiêu chí"}}, {{"type": "NLVH", "q": "Bài văn nghị luận...", "h": "Dàn ý...", "exp": "Tiêu chí"}}]}}"""

    if subject == "Tiếng Anh":
        return f"""[EXAM CREATOR - ENGLISH GRADE {grade_num} - MOET 2026]
[EXAM SEED: {exam_seed} - SESSION: {now_str}]
Topics: [{topics_str}]. Level: {exam_level}. Notes: "{matrix_notes}". Exact {total_p1} MCQs.
TOKEN-SAVING RULE: 'h' and 'exp' between 15-25 words.
JSON ONLY:
{{"p1": [{{"q": "...", "opt": ["A. ...", "B. ...", "C. ...", "D. ..."], "ans": "A", "h": "...", "exp": "..."}}], "p2": [], "p3": []}}"""

    if subject in ["Lịch sử", "Địa lý", "Giáo dục công dân", "Giáo dục kinh tế và pháp luật", "Tin học"]:
        return f"""[CHUYÊN GIA KHẢO THÍ BGDĐT - ĐỀ THI TỐT NGHIỆP THPT 2026 (Cập nhật QĐ 764/QĐ-BGDĐT & TT 13/2026) - MÔN {subject.upper()} LỚP {grade_num}]
[MÃ ĐỀ NGẪU NHIÊN: {exam_seed} - PHIÊN: {now_str}]
Ma trận chuyên đề: [{topics_str}]. Mức độ: {exam_level}. Ý đồ riêng: "{matrix_notes}". Số lượng yêu cầu: {total_p1} TN, {total_p2} Đ/S.

RÀO CHẮN THÉP PHÁP LÝ & HỌC THUẬT:
1. TUÂN THỦ NGHIÊM NGẶT CHƯƠNG TRÌNH KNTT 2018. KHÔNG sử dụng Đồ thị hay Bảng biến thiên.
2. TỐI ƯU TOKEN: "h" (gợi ý) và "exp" (giải thích) HÀM SÚC, ĐẦY ĐỦ Ý khoảng 15-25 từ.
3. XUẤT DUY NHẤT 1 OBJECT JSON (Cấu trúc KHÔNG có Phần III - p3 rỗng):
{{"p1": [{{"q": "...", "opt": ["A. ...", "B. ...", "C. ...", "D. ..."], "ans": "A", "h": "...", "exp": "..."}}],
 "p2": [{{"q": "...", "stmts": [{{"t": "...", "c": true}}, {{"t": "...", "c": false}}, {{"t": "...", "c": true}}, {{"t": "...", "c": false}}], "h": "...", "exp": "..."}}],
 "p3": []}}"""

    if subject in ["Vật lý", "Hóa học", "Sinh học", "Khoa học tự nhiên"]:
        return f"""[CHUYÊN GIA KHẢO THÍ BGDĐT - ĐỀ THI TỐT NGHIỆP THPT 2026 (Cập nhật QĐ 764/QĐ-BGDĐT & TT 13/2026) - MÔN {subject.upper()} LỚP {grade_num}]
[MÃ ĐỀ NGẪU NHIÊN: {exam_seed} - PHIÊN: {now_str}]
Ma trận chuyên đề: [{topics_str}]. Mức độ: {exam_level}. Ý đồ riêng: "{matrix_notes}". Số lượng yêu cầu: {total_p1} TN, {total_p2} Đ/S, {total_p3} TLN.

RÀO CHẮN THÉP PHÁP LÝ & HỌC THUẬT (KNTT 2018):
1. BẮT BUỘC 100% DANH PHÁP QUỐC TẾ IUPAC. TUYỆT ĐỐI CẤM danh pháp cũ 2006.
2. Mọi công thức kẹp trong $...$. Không sử dụng Bảng biến thiên hay Đồ thị phức tạp.
3. TỐI ƯU TOKEN: "h" (gợi ý) và "exp" (giải thích) HÀM SÚC, ĐẦY ĐỦ Ý khoảng 15-25 từ.
4. XUẤT DUY NHẤT 1 OBJECT JSON:
{{"p1": [{{"q": "...", "opt": ["A. $...$", "B. $...$", "C. $...$", "D. $...$"], "ans": "A", "h": "...", "exp": "..."}}],
 "p2": [{{"q": "...", "stmts": [{{"t": "...", "c": true}}, {{"t": "...", "c": false}}, {{"t": "...", "c": true}}, {{"t": "...", "c": false}}], "h": "...", "exp": "..."}}],
 "p3": [{{"q": "...", "ans": "...", "h": "...", "exp": "..."}}]}}"""

    # Mặc định (Toán học)
    return f"""[CHUYÊN GIA KHẢO THÍ BGDĐT - ĐỀ THI TỐT NGHIỆP THPT 2026 (Cập nhật QĐ 764/QĐ-BGDĐT & TT 13/2026) - MÔN {subject.upper()} LỚP {grade_num}]
[MÃ ĐỀ NGẪU NHIÊN: {exam_seed} - PHIÊN: {now_str}]
Ma trận chuyên đề: [{topics_str}]. Mức độ: {exam_level}. Ý đồ riêng: "{matrix_notes}". Số lượng yêu cầu: {total_p1} TN, {total_p2} Đ/S, {total_p3} TLN.

RÀO CHẮN THÉP PHÁP LÝ & HỌC THUẬT (BỘ SÁCH KẾT NỐI TRI THỨC VỚI CUỘC SỐNG 2018):
1. ĐỘC BẢN VÀ NGẪU NHIÊN HÓA TOÀN PHẦN (CHỐNG TRÙNG LẶP): BẮT BUỘC sinh ngẫu nhiên các hệ số mới mẻ.
2. LƯỚI LỌC CẤM KỴ TOÁN HỌC 2026:
   - TUYỆT ĐỐI CẤM SỬ DỤNG CÁC KIẾN THỨC CŨ (2006) SAU ĐÂY: Hàm số bậc bốn trùng phương, Tích phân từng phần, Tích phân đổi biến số phức tạp. NẾU VI PHẠM SẼ BỊ LỖI HỆ THỐNG!
   - CHỈ ĐƯỢC DÙNG 3 LOẠI HÀM SỐ THEO SGK KNTT 12: Bậc ba, Phân thức 1/1, Phân thức 2/1.
3. QUY ĐỊNH ĐỒ THỊ ("f") VÀ BẢNG BIẾN THIÊN ("bbt"):
   - NẾU LÀ BÀI TOÁN THỰC TẾ (Quãng đường, Vận tốc, Doanh thu...) HOẶC KHÔNG CẦN VẼ ĐỒ THỊ: BẮT BUỘC đặt "f": null và "bbt": null.
   - NẾU CẦN VẼ ĐỒ THỊ HÀM SỐ, trả về OBJECT JSON:
     + Bậc 3 (y=ax^3+bx^2+cx+d): "f": {{"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2}}
     + Phân thức 1/1 y=(ax+b)/(cx+d): "f": {{"type": "func_1_1", "a": 2, "b": 1, "c": 1, "d": -1}}
     + Phân thức 2/1 y=(ax^2+bx+c)/(dx+e): "f": {{"type": "func_2_1", "a": 1, "b": -2, "c": 3, "d": 1, "e": -1}}
     + Parabol y=ax^2+bx+c: "f": {{"type": "parabola", "a": 1, "b": -2, "c": 1}}
4. TỐI ƯU TOKEN: "h" (gợi ý) và "exp" (giải thích) HÀM SÚC, ĐẦY ĐỦ Ý khoảng 15-25 từ.
5. XUẤT DUY NHẤT 1 OBJECT JSON:
{{"p1": [{{"q": "...", "f": null, "bbt": null, "opt": ["A. $...$", "B. $...$", "C. $...$", "D. $...$"], "ans": "A", "h": "...", "exp": "..."}}],
 "p2": [{{"q": "...", "f": null, "bbt": null, "stmts": [{{"t": "...", "c": true}}, {{"t": "...", "c": false}}, {{"t": "...", "c": true}}, {{"t": "...", "c": false}}], "h": "...", "exp": "..."}}],
 "p3": [{{"q": "...", "f": null, "bbt": null, "ans": "...", "h": "...", "exp": "..."}}]}}"""


# ==============================================================================
# STATE 2: DOING (Đang làm bài)
# ==============================================================================
def _render_exam_doing(grade, subject, grade_num, student_name):
    exam = st.session_state.exam_data
    c_w1, c_w2 = st.columns([3, 1])
    with c_w1:
        st.warning(f"⚠️ **Phòng thi môn {subject} (Lớp {grade_num}) - Thí sinh: {student_name}:** Tự giác làm bài! (Rời phòng: {st.session_state.violation_count}/3)")
    with c_w2:
        if st.button("🚨 Nộp bài ngay"):
            st.session_state.exam_state = "result"
            st.rerun()
    st.markdown("---")

    if subject == "Ngữ văn":
        st.markdown("### 📖 PHẦN I. ĐỌC HIỂU (4.0 điểm)")
        dh = exam.get("part_doc_hieu", {})
        st.info(f"**Ngữ liệu đọc hiểu (Nguồn mở ngoài SGK KNTT):**\n\n{dh.get('text', '')}")
        for idx, q in enumerate(dh.get("questions", [])):
            st.markdown(f"**Câu {idx+1}:** {q['q']}")
            with st.expander("💡 Gợi ý tư duy", expanded=False):
                st.info(q.get("h", ""))
            st.session_state.exam_answers[f"van_dh_{idx}"] = st.text_area(f"Trả lời câu {idx+1}:", key=f"van_dh_{idx}")
            st.markdown("---")
        st.markdown("### ✍️ PHẦN II. VIẾT (6.0 điểm)")
        for idx, v in enumerate(exam.get("part_viet", [])):
            st.markdown(f"**{'Câu 1 (2.0đ) - NLXH' if idx == 0 else 'Câu 2 (4.0đ) - NLVH'}:** {v['q']}")
            with st.expander("💡 Dàn ý tư duy", expanded=False):
                st.info(v.get("h", ""))
            st.session_state.exam_answers[f"van_v_{idx}"] = st.text_area("Bài làm:", key=f"van_v_{idx}", height=180)
            st.markdown("---")
    else:
        p1_count = len(exam.get("p1", []))
        p2_count = len(exam.get("p2", []))
        p3_count = len(exam.get("p3", []))

        if subject == "Toán học":
            max_p1, max_p2, max_p3 = 3.0, 4.0, 3.0
        elif subject in ["Vật lý", "Hóa học", "Sinh học", "Khoa học tự nhiên"]:
            max_p1, max_p2, max_p3 = 4.5, 4.0, 1.5
        elif subject == "Tiếng Anh":
            max_p1, max_p2, max_p3 = 10.0, 0.0, 0.0
        else:
            max_p1, max_p2, max_p3 = 6.0, 4.0, 0.0

        p1_score_per_q = round(max_p1 / p1_count, 2) if p1_count > 0 else 0
        p2_score_per_q = round(max_p2 / p2_count, 2) if p2_count > 0 else 0
        p3_score_per_q = round(max_p3 / p3_count, 2) if p3_count > 0 else 0

        if exam.get("p1"):
            st.markdown(f"### 📌 {'PHẦN TRẮC NGHIỆM TIẾNG ANH' if subject == 'Tiếng Anh' else 'PHẦN I. Trắc nghiệm nhiều lựa chọn'} ({p1_score_per_q}đ/câu - Tổng {max_p1} điểm)")
            for idx, q in enumerate(exam["p1"]):
                st.markdown(f"**Câu {idx+1}:** {q['q']}")
                _render_fast_visual(q)
                with st.expander("💡 Gợi ý tư duy", expanded=False):
                    st.info(q.get("h", ""))
                st.session_state.exam_answers[f"p1_{idx}"] = st.radio(
                    "Chọn đáp án:", q["opt"], key=f"p1_{idx}",
                    index=None, label_visibility="collapsed"
                )
                st.markdown("---")

        if exam.get("p2"):
            st.markdown(f"### 📌 PHẦN II. Trắc nghiệm Đúng / Sai (Tối đa {p2_score_per_q}đ/câu - Tổng {max_p2} điểm)")
            for idx, q in enumerate(exam["p2"]):
                st.markdown(f"**Câu {idx+1}:** {q['q']}")
                _render_fast_visual(q)
                with st.expander("💡 Gợi ý tư duy", expanded=False):
                    st.info(q.get("h", ""))
                for s_idx, stmt in enumerate(q.get("stmts", [])):
                    s_key = f"p2_{idx}_{s_idx}"
                    st.markdown(f"*   **{chr(97+s_idx)})** {stmt['t']}")
                    st.session_state.exam_answers[s_key] = st.radio(
                        f"Ý {chr(97+s_idx)}:", ["Đúng", "Sai"],
                        key=s_key, index=None, horizontal=True,
                        label_visibility="collapsed"
                    )
                st.markdown("---")

        if exam.get("p3"):
            st.markdown(f"### 📌 PHẦN III. Trả lời ngắn ({p3_score_per_q}đ/câu - Tổng {max_p3} điểm)")
            for idx, q in enumerate(exam["p3"]):
                st.markdown(f"**Câu {idx+1}:** {q['q']}")
                _render_fast_visual(q)
                with st.expander("💡 Gợi ý tư duy", expanded=False):
                    st.info(q.get("h", ""))
                st.session_state.exam_answers[f"p3_{idx}"] = st.text_input("Đáp án:", key=f"p3_{idx}")
                st.markdown("---")

    if st.button("🏁 NỘP BÀI KHẢO THÍ & CHẤM ĐIỂM", use_container_width=True):
        st.session_state.exam_state = "result"
        st.rerun()


# ==============================================================================
# STATE 3: RESULT (Xem kết quả & chấm điểm)
# ==============================================================================
def _render_exam_result(grade, subject, grade_num, student_name, sheet_webhook_url):
    exam = st.session_state.exam_data
    answers = st.session_state.exam_answers
    final_score = 0.0
    loi_sai_logs = []

    # ========== CHẤM ĐIỂM ==========
    if subject == "Ngữ văn":
        student_submission = ""
        for key, val in answers.items():
            if str(val).strip():
                student_submission += f"- {val}\n"

        if len(student_submission.strip()) < 30:
            final_score = 1.0
            loi_sai_logs.append("Bỏ giấy trắng hoặc làm bài chống đối")
        else:
            with st.spinner("AI đang đọc và phân tích bài luận Ngữ văn của em..."):
                try:
                    grading_prompt = f"""[CHUYÊN GIA CHẤM THI NGỮ VĂN GDPT 2018]
Hãy đọc bài làm sau của học sinh. 
- Nếu học sinh viết bừa bãi (như "asdasd"), không có nghĩa: Cho 1 điểm.
- Nếu có làm bài nhưng sơ sài: Cho 3-5 điểm.
- Nếu viết tốt, đúng trọng tâm: Cho 7-9 điểm.
Bài làm của học sinh:
{student_submission}

YÊU CẦU DUY NHẤT: Trả về ĐÚNG 1 CON SỐ thập phân từ 1.0 đến 10.0 đại diện cho điểm số (KHÔNG VIẾT BẤT KỲ CHỮ NÀO KHÁC)."""
                    score_str = call_gemini_with_fallback(grading_prompt).strip()
                    match = re.search(r'(\d+\.\d+|\d+)', score_str)
                    final_score = float(match.group(1)) if match else 5.0
                except Exception:
                    final_score = 4.5

        final_score = round(min(final_score, 10.0), 2)
        if final_score < 5.0:
            loi_sai_logs.append(f"Kỹ năng Viết và Đọc hiểu quá kém ({final_score}đ)")

    elif subject == "Tiếng Anh":
        p1_tot = len(exam.get("p1", []))
        p1_corr = 0
        if p1_tot > 0:
            for idx, q in enumerate(exam["p1"]):
                u_val = answers.get(f"p1_{idx}")
                u_ans_str = str(u_val).strip()[:1].upper() if u_val else ""
                q_ans_str = str(q.get("ans", "")).strip()[:1].upper()
                if u_ans_str and q_ans_str and (u_ans_str == q_ans_str):
                    p1_corr += 1
                else:
                    loi_sai_logs.append(f"Câu {idx+1}")
            total_score = p1_corr * (10.0 / p1_tot)
            final_score = round(min(total_score, 10.0), 2)
    else:
        if subject == "Toán học":
            max_p1, max_p2, max_p3 = 3.0, 4.0, 3.0
        elif subject in ["Vật lý", "Hóa học", "Sinh học", "Khoa học tự nhiên"]:
            max_p1, max_p2, max_p3 = 4.5, 4.0, 1.5
        else:
            max_p1, max_p2, max_p3 = 6.0, 4.0, 0.0

        total_score = 0.0

        # Phần I
        p1_tot = len(exam.get("p1", []))
        if p1_tot > 0:
            p1_rate = max_p1 / p1_tot
            p1_corr = 0
            for idx, q in enumerate(exam["p1"]):
                u_val = answers.get(f"p1_{idx}")
                u_ans_str = str(u_val).strip()[:1].upper() if u_val else ""
                q_ans_str = str(q.get("ans", "")).strip()[:1].upper()
                if u_ans_str and q_ans_str and (u_ans_str == q_ans_str):
                    p1_corr += 1
                else:
                    loi_sai_logs.append(f"TN Câu {idx+1}")
            total_score += p1_corr * p1_rate

        # Phần II
        p2_tot = len(exam.get("p2", []))
        if p2_tot > 0:
            p2_rate = max_p2 / p2_tot
            p2_earned = 0.0
            for idx, q in enumerate(exam["p2"]):
                q_corr = 0
                for s_idx, stmt in enumerate(q.get("stmts", [])):
                    u_ans = answers.get(f"p2_{idx}_{s_idx}")
                    if (u_ans == "Đúng" and stmt.get("c")) or (u_ans == "Sai" and not stmt.get("c")):
                        q_corr += 1
                if q_corr < 4:
                    loi_sai_logs.append(f"Đ/S Câu {idx+1}")
                sub_val = {1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}.get(q_corr, 0.0)
                p2_earned += sub_val * p2_rate
            total_score += p2_earned

        # Phần III
        p3_tot = len(exam.get("p3", []))
        if p3_tot > 0:
            p3_rate = max_p3 / p3_tot
            p3_corr = 0
            for idx, q in enumerate(exam["p3"]):
                u_short = str(answers.get(f"p3_{idx}") or "").strip().lower()
                q_short = str(q.get("ans", "")).strip().lower()
                if u_short and q_short and (u_short == q_short):
                    p3_corr += 1
                else:
                    loi_sai_logs.append(f"TLN Câu {idx+1}")
            total_score += p3_corr * p3_rate

        final_score = round(min(total_score, 10.0), 2)

    # ========== LƯU LOG ==========
    entry = {"time": get_vn_time(), "name": student_name, "grade": grade,
             "subject": subject, "score": final_score, "type": "EXAM_RESULT"}
    if entry not in st.session_state.analytics_logs:
        st.session_state.analytics_logs.append(entry)
        if sheet_webhook_url:
            try:
                requests.post(sheet_webhook_url, json=entry, timeout=5)
            except Exception:
                pass
        if loi_sai_logs and final_score < 10.0:
            st.session_state.va_loi_logs.append({
                "name": student_name, "subject": subject, "grade": grade_num,
                "score": final_score, "loi_sai": ", ".join(loi_sai_logs)
            })

    # ========== HIỂN THỊ KẾT QUẢ ==========
    st.markdown("---")
    st.success(f"🎉 **KẾT QUẢ KHẢO THÍ CHUẨN BỘ MÔN {subject.upper()} (LỚP {grade_num})!** Điểm số của **{student_name}**: **{final_score} / 10.0 điểm**")
    if final_score >= 8.5:
        st.balloons()
        st.markdown("🌟 **Lời khen từ Thầy:** Xuất sắc tuyệt đối!")
    elif final_score >= 6.5:
        st.markdown("👍 **Lời khen từ Thầy:** Khá tốt! Nắm chắc phần cơ bản.")
    else:
        st.markdown("💪 **Nhắn nhủ từ Thầy:** Cùng Thầy khắc phục lỗ hổng ở khung chat Socratic phía dưới nhé!")

    st.markdown("---")
    st.markdown("### 🔍 ĐỐI CHIẾU ĐÁP ÁN & GIẢI THÍCH CHI TIẾT")

    if subject == "Ngữ văn":
        st.markdown("Hệ thống đã lưu lại bài tự luận. Học sinh trao đổi trực tiếp ở khung chat Socratic phía dưới.")
    else:
        if exam.get("p1"):
            st.markdown("#### 📌 Phần I: Trắc nghiệm")
            for idx, q in enumerate(exam["p1"]):
                u_val = answers.get(f"p1_{idx}")
                u_disp = str(u_val) if u_val else "Chưa chọn"
                u_ans_str = str(u_val).strip()[:1].upper() if u_val else ""
                q_ans_str = str(q.get("ans", "")).strip()[:1].upper()
                ok = (u_ans_str == q_ans_str) if u_ans_str and q_ans_str else False
                st.markdown(f"**Câu {idx+1}:** {q['q']} {'✅' if ok else '❌'}")
                _render_fast_visual(q)
                st.markdown(f"- Bạn chọn: `{u_disp}` | **Đáp án đúng: `{q.get('ans', '')}`**")
                st.info(f"📖 **Giải thích:** {q.get('exp', '')}")
                st.markdown("---")

        if exam.get("p2"):
            st.markdown("#### 📌 Phần II: Đúng / Sai")
            for idx, q in enumerate(exam["p2"]):
                st.markdown(f"**Câu {idx+1}:** {q['q']}")
                _render_fast_visual(q)
                for s_idx, stmt in enumerate(q.get("stmts", [])):
                    u_ans = answers.get(f"p2_{idx}_{s_idx}", "Chưa chọn")
                    act = "Đúng" if stmt.get("c") else "Sai"
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;* Ý **{chr(97+s_idx)}**: Bạn chọn `{u_ans}` — Chuẩn là: `{act}` {'✅' if u_ans == act else '❌'}")
                st.info(f"📖 **Giải thích:** {q.get('exp', '')}")
                st.markdown("---")

        if exam.get("p3"):
            st.markdown("#### 📌 Phần III: Trả lời ngắn")
            for idx, q in enumerate(exam["p3"]):
                u_short = str(answers.get(f"p3_{idx}") or "").strip()
                ok_p3 = (u_short.lower() == str(q.get("ans", "")).strip().lower()) if u_short else False
                st.markdown(f"**Câu {idx+1}:** {q['q']} {'✅' if ok_p3 else '❌'}")
                _render_fast_visual(q)
                st.markdown(f"- Bạn trả lời: `{u_short if u_short else 'Chưa trả lời'}` | **Đáp án đúng: `{q.get('ans', '')}`**")
                st.info(f"📖 **Giải thích:** {q.get('exp', '')}")
                st.markdown("---")

    # ========== GIA SƯ SOCRATIC ĐỒNG HÀNH ==========
    st.markdown("---")
    st.markdown("### 💬 Gia Sư Socratic Khảo Thí: Vấn Đáp & Khắc Phục Lỗ Hổng Tư Duy")
    for chat_msg in st.session_state.tram3_chat_messages:
        with st.chat_message(chat_msg["role"]):
            st.markdown(chat_msg["content"])

    if prompt_socratic := st.chat_input("Hỏi Thầy về bất kỳ câu hỏi nào trong đề thi vừa làm..."):
        st.session_state.tram3_chat_messages.append({"role": "user", "content": prompt_socratic})
        with st.chat_message("user"):
            st.markdown(prompt_socratic)
        with st.chat_message("assistant"):
            with st.spinner("Thầy đang chuẩn bị phản hồi gợi mở..."):
                sys_prompt = f"""Bạn là Thầy giáo Gia sư AI tại THPT Tân Hiệp & Thiện Nhân. Học sinh Lớp {grade_num} ({'THCS' if grade_num <= 9 else 'THPT'}) vừa làm xong đề thi. Tên học sinh là {student_name}.
NGUYÊN TẮC: TUYỆT ĐỐI KHÔNG giải hộ, KHÔNG đưa ngay đáp số. Đặt câu hỏi gợi mở bám sát SGK Kết Nối Tri Thức Lớp {grade_num} để học sinh tự nhận ra điểm sai."""
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.tram3_chat_messages[-4:]])
                rep = call_gemini_with_fallback(
                    f"Lịch sử:\n{history_text}\nHS hỏi: {prompt_socratic}",
                    system_instruction=sys_prompt
                )
                st.markdown(rep)
                st.session_state.tram3_chat_messages.append({"role": "assistant", "content": rep})

    # ========== XUẤT BẢN LATEX ==========
    st.markdown("---")
    st.markdown("### 📄 Xuất Bản Đề Thi LaTeX (Chuẩn Cấu Trúc Bộ GD&ĐT 2026)")
    latex_mode = st.radio("Định dạng xuất:",
                          ["Chỉ xuất Đề thi in ấn", "Xuất Đề thi kèm Bảng đáp án"],
                          horizontal=True)

    latex_code = _build_latex_code(exam, subject, grade_num, latex_mode)
    st.code(latex_code, language="latex")
    st.download_button("📥 Tải tệp .tex cho Overleaf (Chuẩn Bộ)",
                       data=latex_code,
                       file_name=f"DeThi_{subject}_Lop{grade_num}.tex",
                       mime="text/plain")

    st.markdown("---")
    if st.button("🔄 Làm đề khảo thí mới"):
        st.session_state.exam_state = "config"
        st.session_state.exam_data = None
        st.session_state.exam_answers = {}
        st.session_state.tram3_chat_messages = []
        st.rerun()


# ==============================================================================
# HELPER: XÂY DỰNG LATEX
# ==============================================================================
def _build_latex_code(exam, subject, grade_num, latex_mode):
    school_lvl = "THCS" if grade_num <= 9 else "THPT"

    latex_code = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnamese]{babel}
\usepackage{amsmath, amssymb, amsfonts, mathrsfs}
\usepackage[margin=1.5cm]{geometry}
\usepackage{multicol}
\usepackage{enumitem}
\usepackage{tikz, tkz-tab, tkz-euclide}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\lhead{\textbf{Trường """ + school_lvl + r""" TÂN HIỆP \& THIỆN NHÂN}}
\rhead{\textbf{Đề khảo thí môn """ + subject + r""" """ + str(grade_num) + r"""}}
\cfoot{Trang \thepage}

\begin{document}
\begin{center}
    \textbf{\Large ĐỀ KHẢO THÍ CHUẨN CẤU TRÚC KHKT 2026}\\[0.5cm]
\end{center}
"""

    if subject == "Ngữ văn":
        dh = exam.get("part_doc_hieu", {})
        latex_code += r"""\noindent\textbf{PHẦN I. ĐỌC HIỂU (4.0 điểm)}\\
\begin{center}
\fbox{\begin{minipage}{0.9\linewidth}
\itshape """ + _sanitize_latex(dh.get("text", "")) + r"""
\end{minipage}}
\end{center}\vspace{0.2cm}
\begin{enumerate}[label=\textbf{Câu \arabic*.}]
"""
        for idx, q in enumerate(dh.get("questions", [])):
            latex_code += f"\\item {_sanitize_latex(q.get('q', ''))}\n"
        latex_code += r"""\end{enumerate}
\vspace{0.2cm}\noindent\textbf{PHẦN II. VIẾT (6.0 điểm)}\\[0.2cm]
\begin{enumerate}[label=\textbf{Câu \arabic*.}]
"""
        for idx, v in enumerate(exam.get("part_viet", [])):
            latex_code += f"\\item \\textbf{{({'2.0' if idx==0 else '4.0'} điểm).}} {_sanitize_latex(v.get('q', ''))}\n"
        latex_code += r"""\end{enumerate}"""
    else:
        if exam.get("p1"):
            latex_code += r"""\noindent\textbf{PHẦN I. Trắc nghiệm nhiều lựa chọn.}\vspace{0.2cm}
\begin{enumerate}[label=\textbf{Câu \arabic*.}]
"""
            for idx, q in enumerate(exam["p1"]):
                latex_code += f"\\item {_sanitize_latex(q.get('q', ''))}\n"
                opts = [_sanitize_latex(o) for o in q.get("opt", [])]
                latex_code += "\\begin{multicols}{2}\n\\begin{enumerate}[label=\\textbf{\\Alph*.}]\n"
                for opt in opts:
                    opt_clean = re.sub(r'^[A-D]\.\s*', '', opt)
                    latex_code += f"\\item {opt_clean}\n"
                latex_code += "\\end{enumerate}\n\\end{multicols}\n"
            latex_code += r"""\end{enumerate}"""

        if exam.get("p2"):
            latex_code += r"""\vspace{0.2cm}\noindent\textbf{PHẦN II. Trắc nghiệm đúng sai.}\vspace{0.2cm}
\begin{enumerate}[label=\textbf{Câu \arabic*.}]
"""
            for idx, q in enumerate(exam["p2"]):
                latex_code += f"\\item {_sanitize_latex(q.get('q', ''))}\n"
                latex_code += "\\begin{enumerate}[label=\\textbf{\\alph*)}]\n"
                for s_idx, stmt in enumerate(q.get("stmts", [])):
                    latex_code += f"\\item {_sanitize_latex(stmt.get('t', ''))} \\hfill [\\quad] Đúng \\quad [\\quad] Sai\n"
                latex_code += "\\end{enumerate}\n"
            latex_code += r"""\end{enumerate}"""

        if exam.get("p3"):
            latex_code += r"""\vspace{0.2cm}\noindent\textbf{PHẦN III. Trả lời ngắn.}\vspace{0.2cm}
\begin{enumerate}[label=\textbf{Câu \arabic*.}]
"""
            for idx, q in enumerate(exam["p3"]):
                latex_code += f"\\item {_sanitize_latex(q.get('q', ''))} \\hfill \\framebox[2.5cm]{{\\rule{{0pt}}{{1.8ex}}Đáp số:}}\n"
            latex_code += r"""\end{enumerate}"""

    if "kèm Bảng đáp án" in latex_mode and exam.get("p1"):
        latex_code += r"""\newpage\begin{center}\textbf{\Large ĐÁP ÁN NHANH PHẦN I}\end{center}
\noindent\begin{tabular}{|""" + "c|" * len(exam["p1"]) + r"""}\hline
"""
        latex_code += " & ".join([f"\\textbf{{{i+1}}}" for i in range(len(exam["p1"]))]) + r""" \\ \hline
"""
        latex_code += " & ".join([f"\\textbf{{{q.get('ans', '')}}}" for q in exam["p1"]]) + r""" \\ \hline
\end{tabular}
"""
    latex_code += r"""\end{document}"""
    return latex_code

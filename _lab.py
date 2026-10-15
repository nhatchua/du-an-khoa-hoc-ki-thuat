    # ========== HÀM BẬC 3 ==========
    if dtype == "func_3":
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

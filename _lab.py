# ==============================================================================
# _lab.py — Phòng Lab: đồ thị, slider hệ số, text-only
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import numpy as np
import json
import re
import time
import random
import math


# === COPY NGUYÊN XI CÁC HÀM SAU TỪ app.py (theo đúng thứ tự) ===

def render_mermaid(code: str):
    safe_code = code.strip().replace('[[', '[').replace(']]', ']')
    safe_code = re.sub(r'^```(?:mermaid)?', '', safe_code, flags=re.MULTILINE)
    safe_code = re.sub(r'```$', '', safe_code, flags=re.MULTILINE).strip()
    safe_code = re.sub(r'\[(?!\s*")([^\]\n]+)(?<!")\]', r'["\1"]', safe_code)

    safe_code = re.sub(r'^\s*graph\s+TD', 'graph LR', safe_code, flags=re.IGNORECASE)
    safe_code = re.sub(r'^\s*flowchart\s+TD', 'flowchart LR', safe_code, flags=re.IGNORECASE)
    if not safe_code.startswith(("graph", "flowchart")):
        safe_code = "graph LR\n" + safe_code

    json_code_str = json.dumps(safe_code)

    html_template = """
    <div style="background: radial-gradient(circle at center, #0f172a 0%, #020617 100%); border-radius: 14px; border: 1.5px solid #1e293b; padding: 12px; position: relative; font-family: system-ui, -apple-system, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 0 10px; flex-wrap: wrap; gap: 6px;">
            <span style="color: #38bdf8; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;">🎯 SƠ ĐỒ TƯ DUY TƯƠNG TÁC (CLICK ĐỂ SỔ / THU NHÁNH)</span>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                <button onclick="expandAll()" style="background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">➕ Mở tất cả</button>
                <button onclick="collapseAll()" style="background: #1e293b; color: #f43f5e; border: 1px solid #f43f5e; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">➖ Thu gọn</button>
                <button onclick="resetZoom()" style="background: #1e293b; color: #34d399; border: 1px solid #34d399; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">🎯 Căn giữa</button>
                <button onclick="exportSVG()" style="background: #1e293b; color: #fbbf24; border: 1px solid #fbbf24; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">💾 Tải SVG</button>
                <button onclick="exportPNG()" style="background: #1e293b; color: #a78bfa; border: 1px solid #a78bfa; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">🖼️ Tải PNG</button>
            </div>
        </div>
        <div id="mindmap-container" style="width: 100%; height: 520px; overflow: hidden; cursor: grab;"></div>
        <div id="mindmap-loading" style="color: #38bdf8; text-align: center; padding-top: 200px; font-size: 14px;">⏳ Đang tải sơ đồ và font toán học...</div>
    </div>

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"></script>
    <script>
    const rawCode = ___JSON_CODE_PLACEHOLDER___;

    function parseNodePart(part) {
        if (!part) return null;
        part = part.trim().split(':::')[0].trim();
        const openIdx = part.search(/[\\(\\[\\{]/);
        if (openIdx === -1) return { id: part, label: null };
        const id = part.substring(0, openIdx).trim();
        let label = part.substring(openIdx).trim();
        label = label.replace(/^[\\(\\[\\{]+["']?/, '').replace(/["']?[\\)\\]\\}]+$/, '').trim();
        return { id: id, label: label || id };
    }

    function parseMermaidToTree(code) {
        const lines = code.split('\\n');
        const nodeLabels = {};
        const childrenMap = {};
        const parentMap = {};

        lines.forEach(line => {
            line = line.trim();
            if (!line || line.startsWith('graph') || line.startsWith('flowchart') || line.startsWith('classDef') || line.startsWith('style') || line.startsWith('subgraph') || line === 'end') return;
            if (line.includes('-->')) {
                const parts = line.split('-->');
                if (parts.length >= 2) {
                    const src = parseNodePart(parts[0]);
                    const tgt = parseNodePart(parts[1]);
                    if (src && tgt) {
                        if (src.label) nodeLabels[src.id] = src.label;
                        else if (!nodeLabels[src.id]) nodeLabels[src.id] = src.id;
                        if (tgt.label) nodeLabels[tgt.id] = tgt.label;
                        else if (!nodeLabels[tgt.id]) nodeLabels[tgt.id] = tgt.id;
                        if (!childrenMap[src.id]) childrenMap[src.id] = [];
                        if (!childrenMap[src.id].includes(tgt.id)) childrenMap[src.id].push(tgt.id);
                        parentMap[tgt.id] = src.id;
                    }
                }
            } else {
                const node = parseNodePart(line);
                if (node && node.id && node.label) nodeLabels[node.id] = node.label;
            }
        });

        const allIds = Object.keys(nodeLabels);
        if (allIds.length === 0) return null;
        let rootId = allIds.find(id => !parentMap[id]) || allIds[0];

        function build(id, depth) {
            const item = { id: id, name: nodeLabels[id] || id, depth: depth };
            const childIds = childrenMap[id] || [];
            if (childIds.length > 0) item.children = childIds.map(cId => build(cId, depth + 1));
            return item;
        }
        return build(rootId, 0);
    }

    // ===== AUTO WRAP MATH NẾU AI QUÊN $...$ =====
    function autoWrapMath(text) {
        if (!text) return text;
        if (/\\$[^\\$]+\\$/.test(text)) return text;
        const mathHint = /(\\^|\\\\frac|\\\\sqrt|\\\\int|\\\\sum|\\\\lim|\\\\sin|\\\\cos|\\\\tan|\\\\log|\\\\ln|\\\\times)/;
        if (!mathHint.test(text)) return text;

        const colonIdx = text.indexOf(':');
        if (colonIdx > 0 && colonIdx < 40) {
            const label = text.substring(0, colonIdx + 1);
            let formula = text.substring(colonIdx + 1).trim();
            formula = formula.replace(/\\{/g, '\\\\{').replace(/\\}/g, '\\\\}');
            formula = formula.replace(/\\(([^()]+)\\)\\s*\\/\\s*\\(([^()]+)\\)/g, '\\\\frac{$1}{$2}');
            return label + ' $' + formula + '$';
        }
        // Không có dấu ":" → thử tách label và formula bằng pattern "y = " hoặc "f(x) = "
        const eqMatch = text.match(/^(.{2,40}?)\s*([yf]\(?x?\)?\s*=.+)$/i);
        if (eqMatch) {
            const label = eqMatch[1].trim();
            let formula = eqMatch[2].trim();
            formula = formula.replace(/\{/g, '\\{').replace(/\}/g, '\\}');
            formula = formula.replace(/\(([^()]+)\)\s*\/\s*\(([^()]+)\)/g, '\\frac{$1}{$2}');
            return label + ': $' + formula + '$';
        }
        const escaped = text.replace(/\{/g, '\\{').replace(/\}/g, '\\}');
        return '$' + escaped + '$';
    }

    function renderMathInLabel(text) {
        if (!text) return '';
        text = autoWrapMath(text);
        text = text.replace(/([^\s:\$])(\$[^\$]+\$)/g, '$1: $2');
        const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return escaped.replace(/\\$([^\\$]+)\\$/g, function(m, formula) {
            try {
                return katex.renderToString(formula, { throwOnError: false, displayMode: false, output: 'html' });
            } catch(e) { return m; }
        });
    }

    // ===== ĐO KÍCH THƯỚC NODE CHÍNH XÁC (HỖ TRỢ MULTI-LINE + KATEX) =====
    function measureNodeSize(d) {
        const fontSize = d.depth === 0 ? 14 : 13;
        const text = d.data.name;

        // Nhận diện công thức cần nhiều chiều cao (phân số, căn, tổng, tích phân)
        const hasComplexMath = /\\frac|\\sqrt|\\int|\\sum|\\lim|\\overline|\\binom/.test(text);

        const measurer = document.createElement('div');
        measurer.style.cssText = [
            'position: absolute',
            'visibility: hidden',
            'top: -9999px',
            'left: -9999px',
            'display: inline-block',
            'white-space: pre-wrap',
            'word-break: break-word',
            'font-family: system-ui, -apple-system, sans-serif',
            'font-weight: 700',
            'font-size: ' + fontSize + 'px',
            'line-height: 1.4',
            'max-width: 280px'
        ].join(';');
        measurer.innerHTML = renderMathInLabel(text);
        document.body.appendChild(measurer);

        // FORCE REFLOW 2 lần để KaTeX render xong hoàn toàn
        void measurer.offsetHeight;
        void measurer.offsetWidth;
        void measurer.getBoundingClientRect();

        const rect = measurer.getBoundingClientRect();
        const textW = Math.ceil(rect.width);
        const textH = Math.ceil(rect.height);
        document.body.removeChild(measurer);

        // Width: text + 44px padding (circle 20 + trái 14 + phải 10)
        d.boxWidth = Math.max(95, textW + 50);

        // Height: min 48px cho text thường, 68px cho công thức phức tạp
        const minH = hasComplexMath ? 68 : 48;
        d.boxHeight = Math.max(minH, textH + 28);
    }

    const treeData = parseMermaidToTree(rawCode);
    const container = document.getElementById("mindmap-container");
    const loadingEl = document.getElementById("mindmap-loading");
    const height = 520;

    if (!treeData) {
        loadingEl.innerHTML = "⚠️ Không đọc được sơ đồ.";
    } else {
        loadingEl.style.display = 'none';

        const svg = d3.select("#mindmap-container").append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .style("user-select", "none");

        const g = svg.append("g");

        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on("zoom", (e) => g.attr("transform", e.transform));
        svg.call(zoom);

        const treeLayout = d3.tree();
        const root = d3.hierarchy(treeData);
        root.x0 = height / 2;
        root.y0 = 40;

        const palette = ["#818cf8", "#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa"];

        if (root.children) {
            root.children.forEach(c => {
                if (c.children) { c._children = c.children; c.children = null; }
            });
        }

        let i = 0;
        function update(source) {
            // Bước 1: đo kích thước tất cả node
            const allNodes = root.descendants();
            allNodes.forEach(d => measureNodeSize(d));

            // Bước 2: tính khoảng cách dọc động theo chiều cao box lớn nhất
            let maxH = 0;
            allNodes.forEach(d => { if (d.boxHeight > maxH) maxH = d.boxHeight; });
            const verticalGap = maxH + 28;  // +28 để chắc chắn không dính
            treeLayout.nodeSize([verticalGap, 220]);

            // Bước 3: chạy layout
            const treeInfo = treeLayout(root);
            const nodes = treeInfo.descendants();
            const links = treeInfo.links();

            // Bước 4: tính khoảng cách ngang động theo box lớn nhất mỗi depth
            const maxWByDepth = {};
            nodes.forEach(d => {
                if (!maxWByDepth[d.depth] || d.boxWidth > maxWByDepth[d.depth]) {
                    maxWByDepth[d.depth] = d.boxWidth;
                }
            });

            const depthX = [40];
            for (let dep = 1; dep <= 10; dep++) {
                depthX[dep] = depthX[dep - 1] + (maxWByDepth[dep - 1] || 160) + 60;
            }

            nodes.forEach(d => { d.y = depthX[d.depth]; });

            // ===== VẼ NODE =====
            const node = g.selectAll("g.node").data(nodes, d => d.id || (d.id = ++i));

            const nodeEnter = node.enter().append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${source.y0},${source.x0})`)
                .style("cursor", "pointer")
                .on("click", (event, d) => {
                    if (d.children) { d._children = d.children; d.children = null; }
                    else if (d._children) { d.children = d._children; d._children = null; }
                    update(d);
                });

            nodeEnter.append("rect")
                .attr("rx", 8).attr("ry", 8)
                .attr("x", 0)
                .attr("width", d => d.boxWidth)
                .attr("height", d => d.boxHeight)
                .attr("y", d => -d.boxHeight / 2)
                .style("fill", "#0f172a")
                .style("stroke", d => palette[d.depth % palette.length])
                .style("stroke-width", d => d.depth === 0 ? "2.5px" : "1.8px")
                .style("filter", "drop-shadow(0 4px 10px rgba(0,0,0,0.6))");

            nodeEnter.append("circle")
                .attr("cx", 14).attr("cy", 0).attr("r", 5.5)
                .style("fill", d => d._children ? palette[d.depth % palette.length] : (d.children ? "#0f172a" : "#475569"))
                .style("stroke", d => palette[d.depth % palette.length])
                .style("stroke-width", "2px");

            const fo = nodeEnter.append("foreignObject")
                .attr("x", 28)
                .attr("y", d => -d.boxHeight / 2 + 12)
                .attr("width", d => d.boxWidth - 44)
                .attr("height", d => d.boxHeight - 24)
                .style("overflow", "visible");

            fo.append("xhtml:div")
                .attr("class", "label-content")
                .style("display", "flex")
                .style("align-items", "center")
                .style("width", "100%")
                .style("height", "100%")
                .style("color", "#ffffff")
                .style("font-family", "system-ui, -apple-system, sans-serif")
                .style("font-weight", "700")
                .style("line-height", "1.4")
                .style("font-size", d => d.depth === 0 ? "14px" : "13px")
                .html(d => renderMathInLabel(d.data.name));

            const nodeUpdate = node.merge(nodeEnter).transition().duration(350)
                .attr("transform", d => `translate(${d.y},${d.x})`);

            nodeUpdate.select("rect")
                .attr("width", d => d.boxWidth)
                .attr("height", d => d.boxHeight)
                .attr("y", d => -d.boxHeight / 2);

            nodeUpdate.select("foreignObject")
                .attr("width", d => d.boxWidth - 44)
                .attr("height", d => d.boxHeight - 24)
                .attr("y", d => -d.boxHeight / 2 + 12);

            nodeUpdate.select("circle")
                .style("fill", d => d._children ? palette[d.depth % palette.length] : (d.children ? "#0f172a" : "#475569"));

            node.exit().transition().duration(350)
                .attr("transform", d => `translate(${source.y},${source.x})`)
                .remove();

            // ===== VẼ LINK =====
            const link = g.selectAll("path.link").data(links, d => d.target.id);

            const linkPath = d => {
                const startX = d.source.y + d.source.boxWidth;
                const startY = d.source.x;
                const endX = d.target.y;
                const endY = d.target.x;
                return `M ${startX} ${startY} C ${(startX + endX) / 2} ${startY}, ${(startX + endX) / 2} ${endY}, ${endX} ${endY}`;
            };

            const linkEnter = link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", d => {
                    const startX = source.y0 + (source.boxWidth || 145);
                    return `M ${startX} ${source.x0} C ${startX} ${source.x0}, ${startX} ${source.x0}, ${startX} ${source.x0}`;
                })
                .style("fill", "none")
                .style("stroke", d => palette[d.target.depth % palette.length])
                .style("stroke-opacity", 0.75)
                .style("stroke-width", "2px");

            link.merge(linkEnter).transition().duration(350).attr("d", linkPath);

            link.exit().transition().duration(350)
                .attr("d", d => {
                    const startX = source.y + (source.boxWidth || 145);
                    return `M ${startX} ${source.x} C ${startX} ${source.x}, ${startX} ${source.x}, ${startX} ${source.x}`;
                })
                .remove();

            nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
            
            // ===== REMEASURE PASS: đo lại từ DOM thật sau khi KaTeX render =====
            if (!window._remeasureTimer) {
                window._remeasureTimer = setTimeout(function() {
                    window._remeasureTimer = null;
                    let changed = false;
                    g.selectAll("g.node").each(function(d) {
                        const divEl = d3.select(this).select("foreignObject").select("div").node();
                        if (!divEl) return;
                        const r = divEl.getBoundingClientRect();
                        const realW = Math.ceil(r.width) + 50;
                        const realH = Math.ceil(r.height) + 28;
                        if (realW > d.boxWidth + 2 || realH > d.boxHeight + 2) {
                            d.boxWidth = Math.max(d.boxWidth, realW);
                            d.boxHeight = Math.max(d.boxHeight, realH);
                            changed = true;
                        }
                    });
                    if (changed) {
                        update(root);  // vẽ lại 1 lần với kích thước đúng
                    }
                }, 180);
            }
        }

        // Đợi font KaTeX load xong mới vẽ để đo chính xác
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(function() {
                update(root);
                svg.call(zoom.transform, d3.zoomIdentity.translate(50, height / 2.3).scale(0.85));
            });
        } else {
            setTimeout(function() {
                update(root);
                svg.call(zoom.transform, d3.zoomIdentity.translate(50, height / 2.3).scale(0.85));
            }, 300);
        }

        // ===== CÁC NÚT ĐIỀU KHIỂN =====
        window.expandAll = function() {
            function expand(d) {
                if (d._children) { d.children = d._children; d._children = null; }
                if (d.children) d.children.forEach(expand);
            }
            expand(root);
            update(root);
        };

        window.collapseAll = function() {
            if (root.children) {
                root.children.forEach(c => {
                    function collapse(d) {
                        if (d.children) { d._children = d.children; d.children = null; }
                        if (d._children) d._children.forEach(collapse);
                    }
                    collapse(c);
                });
            }
            update(root);
        };

        window.resetZoom = function() {
            svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(50, height / 2.3).scale(0.85));
        };

        // ===== XUẤT SVG =====
        window.exportSVG = function() {
            const svgEl = document.querySelector('#mindmap-container svg');
            if (!svgEl) { alert('Chưa có sơ đồ để tải!'); return; }

            // Clone SVG và set kích thước thật
            const clone = svgEl.cloneNode(true);
            const bbox = g.node().getBBox();
            const pad = 40;
            const w = Math.ceil(bbox.width + pad * 2);
            const h = Math.ceil(bbox.height + pad * 2);

            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            clone.setAttribute('xmlns:xhtml', 'http://www.w3.org/1999/xhtml');
            clone.setAttribute('width', w);
            clone.setAttribute('height', h);
            clone.setAttribute('viewBox', (bbox.x - pad) + ' ' + (bbox.y - pad) + ' ' + w + ' ' + h);

            // Thêm background
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', bbox.x - pad);
            rect.setAttribute('y', bbox.y - pad);
            rect.setAttribute('width', w);
            rect.setAttribute('height', h);
            rect.setAttribute('fill', '#020617');
            clone.insertBefore(rect, clone.firstChild);

            // Nạp KaTeX CSS vào SVG
            const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
            style.textContent = '@import url("https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css");';
            clone.insertBefore(style, clone.firstChild);

            const serializer = new XMLSerializer();
            const svgStr = serializer.serializeToString(clone);
            const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(blob);

            const now = new Date();
            const ts = now.getFullYear() + String(now.getMonth()+1).padStart(2,'0') + String(now.getDate()).padStart(2,'0') + '_' + String(now.getHours()).padStart(2,'0') + String(now.getMinutes()).padStart(2,'0') + String(now.getSeconds()).padStart(2,'0');

            const a = document.createElement('a');
            a.href = url;
            a.download = 'SoDoTuDuy_' + ts + '.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        };

        // ===== XUẤT PNG =====
        window.exportPNG = function() {
            const node = document.getElementById('mindmap-container');
            if (!node) { alert('Chưa có sơ đồ để tải!'); return; }

            if (typeof htmlToImage === 'undefined') {
                alert('Thư viện tải PNG chưa load xong. Vui lòng đợi vài giây rồi thử lại.');
                return;
            }

            const now = new Date();
            const ts = now.getFullYear() + String(now.getMonth()+1).padStart(2,'0') + String(now.getDate()).padStart(2,'0') + '_' + String(now.getHours()).padStart(2,'0') + String(now.getMinutes()).padStart(2,'0') + String(now.getSeconds()).padStart(2,'0');

            htmlToImage.toPng(node, {
                backgroundColor: '#020617',
                pixelRatio: 2,
                cacheBust: true
            }).then(function(dataUrl) {
                const a = document.createElement('a');
                a.href = dataUrl;
                a.download = 'SoDoTuDuy_' + ts + '.png';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }).catch(function(err) {
                console.error('Lỗi xuất PNG:', err);
                alert('Không tạo được PNG. Thử tải SVG rồi chuyển đổi bằng công cụ online nhé!');
            });
        };
    }
    </script>
    """

    final_html = html_template.replace("___JSON_CODE_PLACEHOLDER___", json_code_str)
    components.html(final_html, height=560, scrolling=False)

def setup_pedagogical_oxy(fig, x_range, y_range, equal_aspect=False):
    """
    Vẽ trục Oxy chuẩn sư phạm với tick tự động theo range.

    Tham số:
        equal_aspect: True  → 1 đơn vị x = 1 đơn vị y (parabol, đường tròn).
                      False → tự do (hàm bậc 3, phân thức).
    """
    x_min, x_max = x_range
    y_min, y_max = y_range

    fig.add_trace(go.Scatter(x=[x_min, x_max], y=[0, 0], mode='lines', line=dict(color='#cbd5e1', width=1.5), hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=[0, 0], y=[y_min, y_max], mode='lines', line=dict(color='#cbd5e1', width=1.5), hoverinfo='skip', showlegend=False))

    fig.add_annotation(x=x_max, y=0, ax=-18, ay=0, xref='x', yref='y', axref='pixel', ayref='pixel', showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor='#cbd5e1')
    fig.add_annotation(x=x_max - 0.1, y=-0.5, text='<b>x</b>', showarrow=False, font=dict(color='#f8fafc', size=15, family='Times New Roman'))

    fig.add_annotation(x=0, y=y_max, ax=0, ay=18, xref='x', yref='y', axref='pixel', ayref='pixel', showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor='#cbd5e1')
    fig.add_annotation(x=-0.4, y=y_max - 0.1, text='<b>y</b>', showarrow=False, font=dict(color='#f8fafc', size=15, family='Times New Roman'))

    fig.add_annotation(x=-0.35, y=-0.45, text='<i>O</i>', showarrow=False, font=dict(color='#94a3b8', size=15, family='Times New Roman'))

    fig.update_layout(
        template="plotly_dark",
        xaxis=dict(
            range=[x_min, x_max],
            zeroline=False,
            gridcolor="#1e293b",
            nticks=8,           # ✅ giới hạn tối đa 8 vạch
        ),
        yaxis=dict(
            range=[y_min, y_max],
            zeroline=False,
            gridcolor="#1e293b",
            nticks=8,           # ✅ giới hạn tối đa 8 vạch
        ),
        margin=dict(l=15, r=15, t=30, b=15),
        showlegend=False
    )

    # ✅ Cân tỉ lệ nếu cần
    if equal_aspect:
        fig.update_yaxes(scaleanchor="x", scaleratio=1)

def _fmt_coef_smart(v):
    """Format hệ số: 1 → '', -1 → '-', 2.5 → '2.5'."""
    if abs(v) < 1e-9:
        return "0"
    if abs(v - 1) < 1e-9:
        return ""
    if abs(v + 1) < 1e-9:
        return "-"
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip('0').rstrip('.')

def _format_formula_smart(dtype, c):
    """Sinh công thức đẹp theo dtype. c: dict hệ số."""
    def _num(v):
        """Format số thuần (dùng cho hằng số tự do)."""
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.2f}".rstrip('0').rstrip('.')

    def term(v, suf, first=False):
        if abs(v) < 1e-9:
            return ""
        abs_v = abs(v)
        # Xác định dấu
        if first:
            sign = "-" if v < 0 else ""
        else:
            sign = " + " if v > 0 else " - "

        if suf == "":
            # Hằng số tự do: LUÔN in đầy đủ số (kể cả 1, -1)
            return f"{sign}{_num(abs_v)}"

        # Hệ số của biến: bỏ "1" nếu |v| == 1 (viết x² thay vì 1x²)
        if abs_v == 1:
            body = suf
        else:
            body = f"{_num(abs_v)}{suf}"
        return f"{sign}{body}"

    if dtype == "func_3":
        parts = []
        for v, suf in [(c.get("a", 0), "x³"), (c.get("b", 0), "x²"),
                       (c.get("c", 0), "x"), (c.get("d", 0), "")]:
            if abs(v) < 1e-9:
                continue
            parts.append(term(v, suf, first=(len(parts) == 0)))
        return "y = " + "".join(parts) if parts else "y = 0"

    if dtype == "parabola":
        parts = []
        for v, suf in [(c.get("a", 1), "x²"), (c.get("b", 0), "x"), (c.get("c", 0), "")]:
            if abs(v) < 1e-9:
                continue
            parts.append(term(v, suf, first=(len(parts) == 0)))
        return "y = " + "".join(parts) if parts else "y = 0"

    if dtype == "func_1_1":
        num_parts = []
        for v, suf in [(c.get("a", 0), "x"), (c.get("b", 0), "")]:
            if abs(v) < 1e-9:
                continue
            num_parts.append(term(v, suf, first=(len(num_parts) == 0)))
        num_str = "".join(num_parts) if num_parts else "0"

        den_parts = []
        for v, suf in [(c.get("c", 0), "x"), (c.get("d", 0), "")]:
            if abs(v) < 1e-9:
                continue
            den_parts.append(term(v, suf, first=(len(den_parts) == 0)))
        den_str = "".join(den_parts) if den_parts else "0"

        return f"y = ({num_str}) / ({den_str})"

    if dtype == "func_2_1":
        num_parts = []
        for v, suf in [(c.get("a", 0), "x²"), (c.get("b", 0), "x"), (c.get("c", 0), "")]:
            if abs(v) < 1e-9:
                continue
            num_parts.append(term(v, suf, first=(len(num_parts) == 0)))
        num_str = "".join(num_parts) if num_parts else "0"

        den_parts = []
        for v, suf in [(c.get("d", 0), "x"), (c.get("e", 0), "")]:
            if abs(v) < 1e-9:
                continue
            den_parts.append(term(v, suf, first=(len(den_parts) == 0)))
        den_str = "".join(den_parts) if den_parts else "0"

        return f"y = ({num_str}) / ({den_str})"

    return "y = ?"

def _analyze_features_smart(dtype, c):
    """Trả về list (icon, label, value) đặc trưng đồ thị."""
    feats = []

    def fmt(v):
        if abs(v) < 1e-9:
            return "0"
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.2f}".rstrip('0').rstrip('.')

    if dtype == "func_3":
        a, b, cc, d = c.get("a", 1), c.get("b", 0), c.get("c", 0), c.get("d", 0)
        if abs(a) < 1e-9:
            return feats
        xi = -b / (3 * a)
        yi = a * xi**3 + b * xi**2 + cc * xi + d
        feats.append(("🔄", "Điểm uốn", f"I({fmt(xi)}; {fmt(yi)})"))

        delta = 4 * b * b - 12 * a * cc
        if delta > 1e-9:
            x1 = (-2 * b + np.sqrt(delta)) / (6 * a)
            x2 = (-2 * b - np.sqrt(delta)) / (6 * a)
            y1 = a * x1**3 + b * x1**2 + cc * x1 + d
            y2 = a * x2**3 + b * x2**2 + cc * x2 + d
            if a > 0:
                feats.append(("🔴", "Cực đại", f"({fmt(x2)}; {fmt(y2)})"))
                feats.append(("🔴", "Cực tiểu", f"({fmt(x1)}; {fmt(y1)})"))
            else:
                feats.append(("🔴", "Cực đại", f"({fmt(x1)}; {fmt(y1)})"))
                feats.append(("🔴", "Cực tiểu", f"({fmt(x2)}; {fmt(y2)})"))
        else:
            feats.append(("🔴", "Cực trị", "Không có cực trị"))
        feats.append(("🟢", "Giao Oy", f"(0; {fmt(d)})"))

    elif dtype == "parabola":
        a, b, cc = c.get("a", 1), c.get("b", 0), c.get("c", 0)
        if abs(a) < 1e-9:
            return feats
        xd = -b / (2 * a)
        yd = a * xd**2 + b * xd + cc
        feats.append(("📐", "Đỉnh", f"I({fmt(xd)}; {fmt(yd)})"))
        feats.append(("📏", "Trục đối xứng", f"x = {fmt(xd)}"))

        delta = b * b - 4 * a * cc
        feats.append(("🎯", "Delta (Δ)", fmt(delta)))
        if delta > 1e-9:
            x1 = (-b + np.sqrt(delta)) / (2 * a)
            x2 = (-b - np.sqrt(delta)) / (2 * a)
            feats.append(("⚫", "Giao Ox", f"x₁ = {fmt(x1)}, x₂ = {fmt(x2)}"))
        elif abs(delta) < 1e-9:
            feats.append(("⚫", "Giao Ox", f"x = {fmt(xd)} (nghiệm kép)"))
        else:
            feats.append(("⚫", "Giao Ox", "Không cắt trục Ox"))
        feats.append(("🟢", "Giao Oy", f"(0; {fmt(cc)})"))
        feats.append(("📊", "Bề lõm",
                      "Hướng lên (a > 0)" if a > 0 else "Hướng xuống (a < 0)"))

    elif dtype == "func_1_1":
        a, b = c.get("a", 0), c.get("b", 0)
        cc, d = c.get("c", 0), c.get("d", 0)
        if abs(cc) < 1e-9:
            feats.append(("⚠️", "Lưu ý", "Hệ số c ≠ 0 để hàm xác định!"))
            return feats
        x_tcd = -d / cc
        feats.append(("🔵", "Tiệm cận đứng", f"x = {fmt(x_tcd)}"))
        y_tcn = a / cc
        feats.append(("🔵", "Tiệm cận ngang", f"y = {fmt(y_tcn)}"))
        if abs(d) > 1e-9:
            feats.append(("🟢", "Giao Oy", f"(0; {fmt(b/d)})"))
        if abs(a) > 1e-9:
            x_ox = -b / a
            if abs(cc * x_ox + d) > 1e-9:
                feats.append(("⚫", "Giao Ox", f"x = {fmt(x_ox)}"))
        det = a * d - b * cc
        feats.append(("📊", "Đơn điệu",
                      "Nghịch biến trên từng khoảng" if det < 0
                      else "Đồng biến trên từng khoảng"))

    elif dtype == "func_2_1":
        a, b, cc = c.get("a", 0), c.get("b", 0), c.get("c", 0)
        d, e = c.get("d", 0), c.get("e", 0)
        if abs(d) < 1e-9:
            feats.append(("⚠️", "Lưu ý", "Hệ số d ≠ 0 để hàm xác định!"))
            return feats
        x_tcd = -e / d
        feats.append(("🔵", "Tiệm cận đứng", f"x = {fmt(x_tcd)}"))

        m = a / d
        n = (b * d - a * e) / (d * d)
        if abs(m) < 1e-9:
            feats.append(("🔵", "Tiệm cận ngang", f"y = {fmt(n)}"))
        else:
            m_str = "" if abs(m - 1) < 1e-9 else ("-" if abs(m + 1) < 1e-9 else fmt(m))
            if abs(n) < 1e-9:
                tc_str = f"y = {m_str}x"
            elif n > 0:
                tc_str = f"y = {m_str}x + {fmt(n)}"
            else:
                tc_str = f"y = {m_str}x - {fmt(abs(n))}"
            feats.append(("🔵", "Tiệm cận xiên", tc_str))

        A2 = a * d
        B2 = 2 * a * e
        C2 = b * e - cc * d
        if abs(A2) > 1e-9:
            delta = B2 * B2 - 4 * A2 * C2
            if delta > 1e-9:
                x1 = (-B2 + np.sqrt(delta)) / (2 * A2)
                x2 = (-B2 - np.sqrt(delta)) / (2 * A2)
                y1 = (a * x1 * x1 + b * x1 + cc) / (d * x1 + e)
                y2 = (a * x2 * x2 + b * x2 + cc) / (d * x2 + e)
                if x1 < x2:
                    p1, p2 = (x1, y1), (x2, y2)
                else:
                    p1, p2 = (x2, y2), (x1, y1)
                ypp1 = 2 * a / (d * p1[0] + e)
                if ypp1 > 0:
                    feats.append(("🔴", "Cực tiểu", f"({fmt(p1[0])}; {fmt(p1[1])})"))
                    feats.append(("🔴", "Cực đại", f"({fmt(p2[0])}; {fmt(p2[1])})"))
                else:
                    feats.append(("🔴", "Cực đại", f"({fmt(p1[0])}; {fmt(p1[1])})"))
                    feats.append(("🔴", "Cực tiểu", f"({fmt(p2[0])}; {fmt(p2[1])})"))
            else:
                feats.append(("🔴", "Cực trị", "Không có cực trị"))
        else:
            feats.append(("🔴", "Cực trị", "Không có cực trị (bậc 1/1)"))
        if abs(e) > 1e-9:
            feats.append(("🟢", "Giao Oy", f"(0; {fmt(cc/e)})"))

    return feats

def render_dynamic_python_lab(python_code: str):
    try:
        clean_code = re.sub(r'st\.plotly_chart\(.*?\)', '', python_code)
        local_env = {"go": go, "np": np, "st": st, "math": math, "setup_pedagogical_oxy": setup_pedagogical_oxy}
        exec(clean_code, local_env)
        if "fig" in local_env and isinstance(local_env["fig"], go.Figure):
            unique_plot_id = f"dynamic_plot_{int(time.time() * 1000)}_{random.randint(1, 1000)}"
            st.plotly_chart(local_env["fig"], use_container_width=True, key=unique_plot_id)
    except Exception as e:
        st.error(f"Lỗi biên dịch mô phỏng nâng cao: {e}")

def render_smart_lab(data):
    dtype = data.get("type")
    
    if dtype == "mermaid":
        st.markdown("### 🗺️ Trực quan hóa Sơ Đồ Tư Duy / Chu Trình Mô Phỏng")
        render_mermaid(data.get("code", ""))
        return

    if dtype == "area":
        c1, c2 = st.columns([1.2, 2.8])
        func_str = str(data.get("func", "x**2 - 3*x + 2")).replace('$', '').strip()
        
        clean_f = re.sub(r'\\frac{(.*?)}{(.*?)}', r'((\1)/(\2))', func_str)
        clean_f = clean_f.replace('\\sin', 'np.sin').replace('\\cos', 'np.cos').replace('\\tan', 'np.tan')
        clean_f = clean_f.replace('\\ln', 'np.log').replace('\\pi', 'np.pi')
        clean_f = re.sub(r'e\^\{?(.*?)\}?', r'np.exp(\1)', clean_f)
        
        clean_f = clean_f.replace('^', '**').replace('y=', '').replace('f(x)=', '').strip()
        clean_f = re.sub(r'(\d)\s*([a-zA-Z\(])', r'\1*\2', clean_f)
        clean_f = re.sub(r'(\))\s*([a-zA-Z0-9\(])', r'\1*\2', clean_f)
        clean_f = clean_f.replace('{', '(').replace('}', ')')
        
        math_str = func_str.replace('**', '^').replace('*', '').replace(' ', '')
        
        sa_def = float(data.get("a", 0.0))
        sb_def = float(data.get("b", 3.0))

        with c1:
            st.caption("⚙️ **Thông số Diện tích hình phẳng:**")
            st.info(f"**Hàm số:** $y = {math_str}$")
            sa = st.slider("Cận dưới a:", -10.0, 10.0, sa_def, 0.5, key="lab_area_a")
            sb = st.slider("Cận trên b:", -10.0, 10.0, sb_def, 0.5, key="lab_area_b")

            if sa >= sb:
                st.warning("⚠️ Cận a phải nhỏ hơn cận b!")
                sb = sa + 0.5

            try:
                x_area = np.linspace(sa, sb, 400)
                y_area = eval(clean_f, {"x": x_area, "np": np, "math": math})
                if isinstance(y_area, (int, float)): y_area = np.full_like(x_area, float(y_area))
                area_val = np.trapezoid(np.abs(y_area), x_area)
                st.success(f"📐 **Diện tích (S):**\n\n$$S = \\int_{{{sa}}}^{{{sb}}} |{math_str}| dx \\approx {abs(area_val):.2f}$$")
            except Exception:
                pass

        with c2:
            try:
                fig_area = go.Figure()
                
                x_full = np.linspace(sa - 3, sb + 3, 600)
                y_full = eval(clean_f, {"x": x_full, "np": np, "math": math})
                if isinstance(y_full, (int, float)): y_full = np.full_like(x_full, float(y_full))
                
                fig_area.add_trace(go.Scatter(x=x_full, y=y_full, mode='lines', line=dict(color='#38bdf8', width=3), name='Đồ thị hàm số'))
                
                y_area_fill = eval(clean_f, {"x": x_area, "np": np, "math": math})
                if isinstance(y_area_fill, (int, float)): y_area_fill = np.full_like(x_area, float(y_area_fill))
                
                fig_area.add_trace(go.Scatter(x=np.concatenate([x_area, x_area[::-1]]), 
                                              y=np.concatenate([y_area_fill, np.zeros_like(y_area_fill)]), 
                                              fill='toself', fillcolor='rgba(236, 72, 153, 0.4)', 
                                              line=dict(color='rgba(255,255,255,0)'), hoverinfo="skip", name='Diện tích (S)'))
                
                y_view_min, y_view_max = min(y_full), max(y_full)
                y_pad = (y_view_max - y_view_min) * 0.15 
                if y_pad == 0: y_pad = 2
                y_min, y_max = y_view_min - y_pad, y_view_max + y_pad
                if y_min > 0: y_min = -y_pad
                if y_max < 0: y_max = y_pad

                y_sa = eval(clean_f, {"x": sa, "np": np, "math": math})
                y_sb = eval(clean_f, {"x": sb, "np": np, "math": math})
                fig_area.add_trace(go.Scatter(x=[sa, sa], y=[0, float(y_sa)], mode='lines', line=dict(color='#f59e0b', width=2, dash='dash'), name='Cận a'))
                fig_area.add_trace(go.Scatter(x=[sb, sb], y=[0, float(y_sb)], mode='lines', line=dict(color='#10b981', width=2, dash='dash'), name='Cận b'))
                
                setup_pedagogical_oxy(fig_area, [min(x_full), max(x_full)], [y_min, y_max])
                fig_area.update_layout(title="Mô phỏng Diện tích hình phẳng (Tích phân)", height=500, showlegend=True)
                st.plotly_chart(fig_area, use_container_width=True)
            except Exception as err:
                st.error(f"Lỗi vẽ đồ thị diện tích: {err}")
        return
        
    if dtype == "revolve_ox":
        func_str = str(data.get("func", "2*x + 1")).replace('$', '').strip()
        
        clean_f = re.sub(r'\\frac{(.*?)}{(.*?)}', r'((\1)/(\2))', func_str)
        clean_f = clean_f.replace('\\sin', 'np.sin').replace('\\cos', 'np.cos').replace('\\tan', 'np.tan')
        clean_f = clean_f.replace('\\ln', 'np.log').replace('\\pi', 'np.pi')
        clean_f = re.sub(r'e\^\{?(.*?)\}?', r'np.exp(\1)', clean_f)
        
        clean_f = clean_f.replace('^', '**').replace('y=', '').replace('f(x)=', '').strip()
        clean_f = re.sub(r'(\d)\s*([a-zA-Z\(])', r'\1*\2', clean_f)
        clean_f = re.sub(r'(\))\s*([a-zA-Z0-9\(])', r'\1*\2', clean_f)
        clean_f = clean_f.replace('{', '(').replace('}', ')')

        a_def = float(data.get("a", 2.0))
        b_def = float(data.get("b", 5.0))

        c1, c2 = st.columns([1.2, 2.8])
        with c1:
            st.caption("⚙️ **Thông số Khối tròn xoay quanh trục Ox:**")
            math_str = func_str.replace('**', '^').replace('*', '')
            st.info(f"**Đường giới hạn:** $y = {math_str}$")
            sa = st.slider("Cận dưới a:", -8.0, 8.0, a_def, 0.5, key="lab_revolve_a")
            sb = st.slider("Cận trên b:", -8.0, 8.0, b_def, 0.5, key="lab_revolve_b")
            angle_deg = st.slider("Góc quay quanh trục Ox:", 30, 360, 360, 15, key="lab_revolve_angle")

            if sa >= sb:
                st.warning("⚠️ Cận a phải nhỏ hơn cận b!")
                sb = sa + 0.5

            try:
                x_num = np.linspace(sa, sb, 400)
                y_num = eval(clean_f, {"x": x_num, "np": np, "math": math})
                if isinstance(y_num, (int, float)): y_num = np.full_like(x_num, float(y_num))
                vol_val = np.trapezoid(y_num**2, x_num) * np.pi
                st.success(f"📐 **Thể tích khối tròn xoay:**\n\n$$V = \\pi \\int_{{{sa}}}^{{{sb}}} [{math_str}]^2 dx \\approx {abs(vol_val):.2f}\\text{{ (đvtt)}}$$")
            except Exception:
                pass

        with c2:
            try:
                u = np.linspace(sa, sb, 60)
                v = np.linspace(0, np.radians(angle_deg), 60)
                U, V = np.meshgrid(u, v)

                R = eval(clean_f, {"x": U, "np": np, "math": math})
                if isinstance(R, (int, float)): R = np.full_like(U, float(R))

                X_3d = U
                Y_3d = R * np.cos(V)
                Z_3d = R * np.sin(V)

                fig_3d = go.Figure()
                fig_3d.add_trace(go.Surface(x=X_3d, y=Y_3d, z=Z_3d, colorscale='Viridis', opacity=0.82, showscale=False, name='Khối tròn xoay'))

                ox_min, ox_max = min(sa - 1.5, -2), max(sb + 1.5, 2)
                fig_3d.add_trace(go.Scatter3d(x=[ox_min, ox_max], y=[0, 0], z=[0, 0], mode='lines+text', line=dict(color='#ffffff', width=4), text=["", "Trục Ox"], textposition="top right", name="Trục Ox"))

                y_gen = eval(clean_f, {"x": u, "np": np, "math": math})
                if isinstance(y_gen, (int, float)): y_gen = np.full_like(u, float(y_gen))
                fig_3d.add_trace(go.Scatter3d(x=u, y=y_gen, z=np.zeros_like(u), mode='lines', line=dict(color='#f43f5e', width=5), name='Đường sinh y=f(x)'))

                fig_3d.update_layout(
                    title=f"Mô hình 3D Khối tròn xoay: $y = {math_str}$ quay quanh Ox",
                    template="plotly_dark",
                    scene=dict(
                        xaxis=dict(title="Trục Ox", backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        yaxis=dict(title="Trục Oy", backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        zaxis=dict(title="Trục Oz", backgroundcolor="#0f172a", gridcolor="#1e293b"),
                        aspectmode='data'
                    ),
                    height=520,
                    margin=dict(l=10, r=10, t=35, b=10)
                )
                st.plotly_chart(fig_3d, use_container_width=True)
            except Exception as err:
                st.error(f"Lỗi tính toán mô phỏng 3D: {err}")
        return

    if dtype == "dynamic_code":
        st.markdown("### 🎨 Mô Phỏng Đồ Họa Động / Không Gian Nâng Cao")
        render_dynamic_python_lab(data.get("python_code", ""))
        return

    fig = go.Figure()

    # ========== HELPER NỘI BỘ ==========
    def _render_formula_and_features(_dtype, _coeffs):
        """Render hộp công thức + panel đặc trưng cho cột trái."""
        _formula = _format_formula_smart(_dtype, _coeffs)
        st.markdown(
            f"<div style='background: linear-gradient(135deg, #4a90e2, #357abd); color: white; "
            f"padding: 14px 18px; border-radius: 10px; font-size: 1.05rem; "
            f"font-weight: 600; margin: 20px 0; text-align: center;'>"
            f"<i>{_formula}</i></div>",
            unsafe_allow_html=True
        )
        _feats = _analyze_features_smart(_dtype, _coeffs)
        if _feats:
            st.markdown("<div class='feature-title'>📋 Đặc trưng đồ thị:</div>",
                        unsafe_allow_html=True)
            for _icon, _label, _value in _feats:
                st.markdown(
                    f"<div class='feature-item'>{_icon} <b>{_label}:</b> {_value}</div>",
                    unsafe_allow_html=True)

    # ========== HÀM BẬC 3 ==========
    if dtype == "func_3":
        c1, c2 = st.columns([1.2, 2.8])
        with c1:
            st.caption("⚙️ **Thay đổi hệ số hàm bậc 3:**")
            fa = st.slider("Hệ số a:", -3.0, 3.0, float(data.get("a", 1.0)), 0.5, key="lab_f3_a")
            if fa == 0: fa = 0.5
            fb = st.slider("Hệ số b:", -5.0, 5.0, float(data.get("b", -3.0)), 0.5, key="lab_f3_b")
            fc = st.slider("Hệ số c:", -5.0, 5.0, float(data.get("c", 0.0)), 0.5, key="lab_f3_c")
            fd = st.slider("Hệ số d:", -5.0, 5.0, float(data.get("d", 2.0)), 0.5, key="lab_f3_d")

            _render_formula_and_features("func_3", {"a": fa, "b": fb, "c": fc, "d": fd})

        with c2:
            # ===== TỰ ĐỘNG ZOOM QUANH CỰC TRỊ / ĐIỂM UỐN =====
            delta_cp = 4 * fb * fb - 12 * fa * fc
            xu = -fb / (3 * fa)
            if delta_cp > 1e-9:
                # Có 2 cực trị → mở rộng quanh 2 cực trị + điểm uốn
                x1 = (-2 * fb + np.sqrt(delta_cp)) / (6 * fa)
                x2 = (-2 * fb - np.sqrt(delta_cp)) / (6 * fa)
                x_min_view = min(x1, x2, xu) - 2.5
                x_max_view = max(x1, x2, xu) + 2.5
            else:
                # Không có cực trị → quanh điểm uốn ±4
                x_min_view = xu - 4
                x_max_view = xu + 4

            x_vals = np.linspace(x_min_view, x_max_view, 800)
            y_vals = fa * (x_vals**3) + fb * (x_vals**2) + fc * x_vals + fd

            y_min_plot = float(np.min(y_vals))
            y_max_plot = float(np.max(y_vals))
            y_pad = max((y_max_plot - y_min_plot) * 0.12, 1.0)
            y_min_view = y_min_plot - y_pad
            y_max_view = y_max_plot + y_pad

            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                      line=dict(color='#38bdf8', width=3), name='Đồ thị'))

            setup_pedagogical_oxy(fig, [x_min_view, x_max_view], [y_min_view, y_max_view])
            fig.update_layout(title="Đồ thị Hàm số Bậc 3", height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ========== HÀM PHÂN THỨC 1/1 ==========
    elif dtype == "func_1_1":
        c1, c2 = st.columns([1.2, 2.8])
        with c1:
            st.caption("⚙️ **Thay đổi hệ số hàm phân thức bậc 1/1:**")
            fa = st.slider("Hệ số a:", -4.0, 4.0, float(data.get("a", 1.0)), 0.5, key="lab_f11_a")
            fb = st.slider("Hệ số b:", -5.0, 5.0, float(data.get("b", 1.0)), 0.5, key="lab_f11_b")
            fc = st.slider("Hệ số c:", -4.0, 4.0, float(data.get("c", 1.0)), 0.5, key="lab_f11_c")
            if fc == 0: fc = 1.0
            fd = st.slider("Hệ số d:", -5.0, 5.0, float(data.get("d", -1.0)), 0.5, key="lab_f11_d")

            _render_formula_and_features("func_1_1", {"a": fa, "b": fb, "c": fc, "d": fd})

        with c2:
            x_tc_dung = -fd / fc
            y_tc_ngang = fa / fc
            x_left = np.linspace(-7, x_tc_dung - 0.05, 400)
            x_right = np.linspace(x_tc_dung + 0.05, 7, 400)
            y_left = (fa * x_left + fb) / (fc * x_left + fd)
            y_right = (fa * x_right + fb) / (fc * x_right + fd)
            y_left[np.abs(y_left) > 15] = np.nan
            y_right[np.abs(y_right) > 15] = np.nan

            fig.add_trace(go.Scatter(x=x_left, y=y_left, mode='lines', line=dict(color='#38bdf8', width=3), name='Nhánh trái'))
            fig.add_trace(go.Scatter(x=x_right, y=y_right, mode='lines', line=dict(color='#38bdf8', width=3), name='Nhánh phải'))
            fig.add_trace(go.Scatter(x=[x_tc_dung, x_tc_dung], y=[-15, 15], mode='lines', line=dict(color='#f59e0b', width=1.8, dash='dash'), name='TC Đứng'))
            fig.add_trace(go.Scatter(x=[-7, 7], y=[y_tc_ngang, y_tc_ngang], mode='lines', line=dict(color='#10b981', width=1.8, dash='dash'), name='TC Ngang'))
            setup_pedagogical_oxy(fig, [-7, 7], [-8, 8])
            fig.update_layout(title="Đồ thị Hàm phân thức Bậc 1 / Bậc 1 (Kèm Tiệm cận)", height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ========== HÀM PHÂN THỨC 2/1 ==========
    elif dtype == "func_2_1":
        c1, c2 = st.columns([1.2, 2.8])
        with c1:
            st.caption("⚙️ **Hệ số hàm phân thức bậc 2/1:**")
            fa = st.slider("a:", -3.0, 3.0, float(data.get("a", 1.0)), 0.5, key="lab_f21_a")
            if fa == 0: fa = 1.0
            fb = st.slider("b:", -5.0, 5.0, float(data.get("b", -2.0)), 0.5, key="lab_f21_b")
            fc = st.slider("c:", -5.0, 5.0, float(data.get("c", 2.0)), 0.5, key="lab_f21_c")
            fd = st.slider("d:", -3.0, 3.0, float(data.get("d", 1.0)), 0.5, key="lab_f21_d")
            if fd == 0: fd = 1.0
            fe = st.slider("e:", -5.0, 5.0, float(data.get("e", -1.0)), 0.5, key="lab_f21_e")

            _render_formula_and_features("func_2_1", {"a": fa, "b": fb, "c": fc, "d": fd, "e": fe})

        with c2:
            x_tc_dung = -fe / fd
            m_slope = fa / fd
            n_intercept = (fb - m_slope * fe) / fd
            x_left = np.linspace(-7, x_tc_dung - 0.05, 400)
            x_right = np.linspace(x_tc_dung + 0.05, 7, 400)
            y_left = (fa * x_left**2 + fb * x_left + fc) / (fd * x_left + fe)
            y_right = (fa * x_right**2 + fb * x_right + fc) / (fd * x_right + fe)
            y_left[np.abs(y_left) > 18] = np.nan
            y_right[np.abs(y_right) > 18] = np.nan

            fig.add_trace(go.Scatter(x=x_left, y=y_left, mode='lines', line=dict(color='#38bdf8', width=3), name='Đồ thị'))
            fig.add_trace(go.Scatter(x=x_right, y=y_right, mode='lines', line=dict(color='#38bdf8', width=3), name='Đồ thị'))
            fig.add_trace(go.Scatter(x=[x_tc_dung, x_tc_dung], y=[-18, 18], mode='lines', line=dict(color='#f59e0b', width=1.8, dash='dash'), name='TC Đứng'))
            
            x_slant = np.linspace(-7, 7, 100)
            y_slant = m_slope * x_slant + n_intercept
            fig.add_trace(go.Scatter(x=x_slant, y=y_slant, mode='lines', line=dict(color='#ec4899', width=1.8, dash='dash'), name='TC Xiên'))
            setup_pedagogical_oxy(fig, [-7, 7], [-10, 10])
            fig.update_layout(title="Đồ thị Hàm phân thức Bậc 2 / Bậc 1 (Kèm Tiệm cận xiên)", height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ========== PARABOL BẬC 2 ==========
    elif dtype in ["parabola", "func_2"]:
        c1, c2 = st.columns([1.2, 2.8])
        with c1:
            st.caption("⚙️ **Hệ số Parabol bậc 2 ($y = ax^2 + bx + c$):**")
            fa = st.slider("Hệ số a:", -4.0, 4.0, float(data.get("a", 1.0)), 0.5, key="lab_p2_a")
            if fa == 0: fa = 1.0
            fb = st.slider("Hệ số b:", -6.0, 6.0, float(data.get("b", -2.0)), 0.5, key="lab_p2_b")
            fc = st.slider("Hệ số c:", -6.0, 6.0, float(data.get("c", -1.0)), 0.5, key="lab_p2_c")

            _render_formula_and_features("parabola", {"a": fa, "b": fb, "c": fc})

        with c2:
            x_dinh = -fb / (2 * fa)
            y_dinh = fa * x_dinh**2 + fb * x_dinh + fc

            # ===== TỰ ĐỘNG ZOOM VỪA PHẢI QUANH ĐỈNH =====
            delta = fb**2 - 4*fa*fc
            if delta > 1e-9:
                # Có 2 nghiệm → mở rộng 1.5 đơn vị quanh 2 nghiệm
                x1 = (-fb - np.sqrt(delta)) / (2*fa)
                x2 = (-fb + np.sqrt(delta)) / (2*fa)
                x_min_view = min(x1, x2) - 1.5
                x_max_view = max(x1, x2) + 1.5
            else:
                # Không có nghiệm → mở rộng ±3 đơn vị quanh đỉnh
                x_min_view = x_dinh - 3
                x_max_view = x_dinh + 3

            # Đảm bảo width tối thiểu 5 đơn vị để đồ thị không quá hẹp
            if (x_max_view - x_min_view) < 5:
                center = (x_max_view + x_min_view) / 2
                x_min_view = center - 2.5
                x_max_view = center + 2.5

            x_vals = np.linspace(x_min_view, x_max_view, 500)
            y_vals = fa * x_vals**2 + fb * x_vals + fc

            # Y range bao quanh đỉnh + 2 biên
            y_min_plot = min(y_dinh, float(np.min(y_vals)))
            y_max_plot = max(y_dinh, float(np.max(y_vals)))
            y_pad = max((y_max_plot - y_min_plot) * 0.15, 0.5)
            y_min_view = y_min_plot - y_pad
            y_max_view = y_max_plot + y_pad

            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                      line=dict(color='#38bdf8', width=3), name='Parabol'))
            fig.add_trace(go.Scatter(x=[x_dinh, x_dinh], y=[y_min_view, y_max_view],
                                      mode='lines', line=dict(color='#f59e0b', width=1.5, dash='dash'),
                                      name='Trục đối xứng'))
            fig.add_trace(go.Scatter(x=[x_dinh], y=[y_dinh], mode='markers+text',
                                      marker=dict(size=8, color='gold'),
                                      text=[f'I({x_dinh:.1f}; {y_dinh:.1f})'],
                                      textposition="top center"))

            setup_pedagogical_oxy(fig, [x_min_view, x_max_view], [y_min_view, y_max_view])
            fig.update_layout(title="Đồ thị Parabol Bậc 2 (Toán Lớp 10)", height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ========== KHÔNG GIAN OXYZ ==========
    elif dtype == "oxyz":
        c1, c2 = st.columns([1, 3])
        with c1:
            st.caption("⚙️ **Thay đổi tọa độ điểm M(x; y; z):**")
            mx = st.slider("x:", -4.0, 5.0, float(data.get("x", 2.0)), 0.5, key="lab_3d_x")
            my = st.slider("y:", -4.0, 5.0, float(data.get("y", 3.0)), 0.5, key="lab_3d_y")
            mz = st.slider("z:", -4.0, 5.0, float(data.get("z", 4.0)), 0.5, key="lab_3d_z")
            st.info(f"**Điểm $M({mx}; {my}; {mz})$**")
        with c2:
            fig.add_trace(go.Scatter3d(x=[mx], y=[my], z=[mz], mode='markers+text', marker=dict(size=9, color='#38bdf8'), text=[f'M({mx}; {my}; {mz})'], textposition="top center"))
            fig.add_trace(go.Scatter3d(x=[0, mx, mx], y=[0, 0, my], z=[0, 0, 0], mode='lines', line=dict(color='#94a3b8', width=3, dash='dash'), hoverinfo='skip'))
            fig.add_trace(go.Scatter3d(x=[mx, mx], y=[my, my], z=[0, mz], mode='lines', line=dict(color='#f59e0b', width=3, dash='dash'), hoverinfo='skip'))
            fig.update_layout(
                title="Không gian Oxyz: Biểu diễn toạ độ điểm",
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(range=[-5, 5], backgroundcolor="#0f172a"),
                    yaxis=dict(range=[-5, 5], backgroundcolor="#0f172a"),
                    zaxis=dict(range=[-5, 5], backgroundcolor="#0f172a"),
                    aspectmode='cube'
                ),
                height=500,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("💡 Đã tiếp nhận yêu cầu. Kéo thanh trượt hoặc nhập tham số để mô phỏng tương tác!")

def _build_text_only_prompt(lab_request, subject, grade_num):
    """Prompt riêng cho Hóa, Sinh, Sử-Địa: chỉ trả về văn bản, KHÔNG sinh code plot."""
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

    else:  # Lịch sử & Địa lý
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

def render_lab_text_block(text):
    """Render text Phòng Lab: tách heading riêng, style nổi bật."""
    if not text or not text.strip():
        return

    # Nhận diện heading: "1. ...", "2. ...", "I. ...", "II. ..."
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
            # Heading = dòng ngắn, bắt đầu bằng "số." hoặc "I."
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

def clean_ai_response(text: str) -> str:
    """Lọc sạch phản hồi AI: bỏ dấu #, bỏ suy luận nội tâm, bỏ tiếng Anh."""
    if not text:
        return ""
    pattern = re.compile(
        r"(#{1,3}\s*)?📌?\s*1\.\s*KIẾN\s*THỨC\s*CỐT\s*LÕI",
        re.IGNORECASE | re.UNICODE
    )
    match = pattern.search(text)
    if match:
        text = text[match.start():]

    # Bỏ dấu # ở đầu dòng
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

def strip_plot_section_from_text(text):
    """Cắt bỏ mục 'MÃ VẼ ĐỒ THỊ' và mọi nội dung sau nó (phòng AI vẫn sinh)."""
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

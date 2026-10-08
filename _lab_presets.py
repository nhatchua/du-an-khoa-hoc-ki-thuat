"""
_lab_presets.py — Thư viện mô phỏng có sẵn cho Phòng Lab.
Tách riêng khỏi _lab.py để giữ file _lab.py gọn gàng.

Cấu trúc:
    PRESET_LABS = {
        "<Môn>": {
            <lớp>: [ {id, name, desc, tags, data}, ... ],
        },
    }

Mỗi preset có:
    - id:      mã duy nhất (dùng làm key)
    - name:    tên hiển thị trên nút
    - desc:    mô tả ngắn
    - tags:    danh sách từ khóa để search không dấu
    - data:    dict cùng format với output AI (type + tham số)
"""

PRESET_LABS = {
    # ==========================================================================
    # TOÁN HỌC
    # ==========================================================================
    "Toán học": {
        10: [
            {
                "id": "toan10_parabola_1",
                "name": "📐 Parabol cơ bản",
                "desc": "y = x² − 2x + 1 (nghiệm kép)",
                "tags": ["parabol", "bac hai", "do thi", "nghiem kep"],
                "data": {"type": "parabola", "a": 1, "b": -2, "c": 1},
            },
            {
                "id": "toan10_parabola_2",
                "name": "📉 Parabol hướng xuống",
                "desc": "y = −x² + 4x − 3 (2 nghiệm phân biệt)",
                "tags": ["parabol", "bac hai", "do thi", "huong xuong"],
                "data": {"type": "parabola", "a": -1, "b": 4, "c": -3},
            },
            {
                "id": "toan10_parabola_3",
                "name": "🎯 Parabol vô nghiệm",
                "desc": "y = x² + x + 1 (Δ < 0)",
                "tags": ["parabol", "bac hai", "vo nghiem"],
                "data": {"type": "parabola", "a": 1, "b": 1, "c": 1},
            },
        ],
        12: [
            {
                "id": "toan12_func3_2cuc",
                "name": "🎯 Hàm bậc 3 (2 cực trị)",
                "desc": "y = x³ − 3x + 2 — có CĐ, CT và điểm uốn",
                "tags": ["ham bac 3", "bac ba", "khao sat", "cuc tri"],
                "data": {"type": "func_3", "a": 1, "b": -3, "c": 0, "d": 2},
            },
            {
                "id": "toan12_func3_vo_cuc",
                "name": "🎯 Hàm bậc 3 (vô cực trị)",
                "desc": "y = x³ + x + 1 — không có CĐ, CT",
                "tags": ["ham bac 3", "bac ba", "khao sat", "vo cuc tri"],
                "data": {"type": "func_3", "a": 1, "b": 0, "c": 1, "d": 1},
            },
            {
                "id": "toan12_func11",
                "name": "📈 Phân thức 1/1",
                "desc": "y = (x+1)/(x−1) — có TCĐ x=1, TCN y=1",
                "tags": ["phan thuc", "bac 1/1", "khao sat", "tiem can"],
                "data": {"type": "func_1_1", "a": 1, "b": 1, "c": 1, "d": -1},
            },
            {
                "id": "toan12_func21",
                "name": "📊 Phân thức 2/1",
                "desc": "y = (x²−2x+3)/(x−1) — có TCĐ và TCX",
                "tags": ["phan thuc", "bac 2/1", "khao sat", "tiem can xien"],
                "data": {"type": "func_2_1", "a": 1, "b": -2, "c": 3, "d": 1, "e": -1},
            },
            {
                "id": "toan12_area_1",
                "name": "🌊 Diện tích hình phẳng",
                "desc": "S = ∫|x²−3x+2|dx từ 0 đến 3",
                "tags": ["tich phan", "dien tich", "hinh phang"],
                "data": {"type": "area", "func": "x**2 - 3*x + 2", "a": 0.0, "b": 3.0},
            },
            {
                "id": "toan12_revolve_1",
                "name": "🌀 Khối tròn xoay Ox",
                "desc": "y = 2x + 1 quay quanh trục Ox (a=2, b=5)",
                "tags": ["tich phan", "khoi tron", "the tich", "3d"],
                "data": {"type": "revolve_ox", "func": "2*x + 1", "a": 2.0, "b": 5.0},
            },
            {
                "id": "toan12_oxyz_1",
                "name": "🧊 Không gian Oxyz",
                "desc": "Biểu diễn điểm M(2; 3; 4) trong hệ trục Oxyz",
                "tags": ["oxyz", "khong gian", "toa do", "3d"],
                "data": {"type": "oxyz", "x": 2, "y": 3, "z": 4},
            },
            {
                "id": "toan12_mindmap_ham_so",
                "name": "🗺️ Sơ đồ các loại hàm số",
                "desc": "Mindmap 4 nhóm hàm: Đa thức, Phân thức, Mũ, Lượng giác",
                "tags": ["so do", "mindmap", "ham so", "phan loai"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CÁC LOẠI HÀM SỐ"] --> A["📌 Hàm Đa Thức"]\n'
                        '   Root --> B["📌 Hàm Phân Thức"]\n'
                        '   Root --> C["📌 Hàm Mũ và Logarit"]\n'
                        '   Root --> D["📌 Hàm Lượng Giác"]\n'
                        '   A --> A1["Bậc nhất: $y = ax + b$"]\n'
                        '   A --> A2["Bậc hai: $y = ax^2 + bx + c$"]\n'
                        '   A --> A3["Bậc ba: $y = ax^3 + bx^2 + cx + d$"]\n'
                        '   B --> B1["Bậc 1/1: $y = \\\\frac{ax+b}{cx+d}$"]\n'
                        '   B --> B2["Bậc 2/1: $y = \\\\frac{ax^2+bx+c}{dx+e}$"]\n'
                        '   C --> C1["Hàm mũ: $y = a^x$"]\n'
                        '   C --> C2["Hàm logarit: $y = \\\\log_a x$"]\n'
                        '   D --> D1["$y = \\\\sin x$, $y = \\\\cos x$"]\n'
                        '   D --> D2["$y = \\\\tan x$, $y = \\\\cot x$"]'
                    ),
                },
            },
        ],
    },

    # ==========================================================================
    # VẬT LÝ
    # ==========================================================================
    "Vật lý": {
        10: [
            {
                "id": "ly10_mindmap_newton",
                "name": "🗺️ Sơ đồ 3 định luật Newton",
                "desc": "Mindmap tóm tắt 3 định luật Newton",
                "tags": ["newton", "dinh luat", "dong luc hoc", "so do"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 3 ĐỊNH LUẬT NEWTON"] --> A["📌 ĐL 1 — Quán tính"]\n'
                        '   Root --> B["📌 ĐL 2 — $F = ma$"]\n'
                        '   Root --> C["📌 ĐL 3 — Tác dụng & phản tác dụng"]\n'
                        '   A --> A1["Vật giữ nguyên trạng thái"]\n'
                        '   A --> A2["Khi không có lực tác dụng"]\n'
                        '   B --> B1["Gia tốc tỉ lệ với lực"]\n'
                        '   B --> B2["Tỉ lệ nghịch với khối lượng"]\n'
                        '   C --> C1["Lực và phản lực"]\n'
                        '   C --> C2["Cùng độ lớn, ngược chiều"]'
                    ),
                },
            },
            {
                "id": "ly10_mindmap_nang_luong",
                "name": "🗺️ Sơ đồ bảo toàn cơ năng",
                "desc": "Mindmap các dạng năng lượng và định luật bảo toàn",
                "tags": ["nang luong", "co nang", "bao toan"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 NĂNG LƯỢNG & BẢO TOÀN"] --> A["📌 Động năng"]\n'
                        '   Root --> B["📌 Thế năng"]\n'
                        '   Root --> C["📌 Cơ năng"]\n'
                        '   A --> A1["$W_đ = \\\\frac{1}{2}mv^2$"]\n'
                        '   B --> B1["Thế năng trọng trường"]\n'
                        '   B --> B2["Thế năng đàn hồi"]\n'
                        '   C --> C1["$W = W_đ + W_t$"]\n'
                        '   C --> C2["Bảo toàn khi không có ma sát"]'
                    ),
                },
            },
        ],
        11: [
            {
                "id": "ly11_mindmap_dao_dong",
                "name": "🗺️ Sơ đồ các loại dao động",
                "desc": "Mindmap phân loại dao động: điều hòa, tắt dần, cưỡng bức, cộng hưởng",
                "tags": ["dao dong", "dieu hoa", "tat dan", "cong huong"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CÁC LOẠI DAO ĐỘNG"] --> A["📌 Dao động điều hòa"]\n'
                        '   Root --> B["📌 Dao động tắt dần"]\n'
                        '   Root --> C["📌 Dao động cưỡng bức"]\n'
                        '   Root --> D["📌 Hiện tượng cộng hưởng"]\n'
                        '   A --> A1["Con lắc đơn"]\n'
                        '   A --> A2["Con lắc lò xo"]\n'
                        '   B --> B1["Biên độ giảm dần"]\n'
                        '   B --> B2["Do ma sát"]\n'
                        '   C --> C1["Ngoại lực tuần hoàn"]\n'
                        '   D --> D1["Tần số ngoại lực = tần số riêng"]'
                    ),
                },
            },
            {
                "id": "ly11_mindmap_song_co",
                "name": "🗺️ Sơ đồ sóng cơ",
                "desc": "Mindmap các hiện tượng sóng cơ",
                "tags": ["song co", "giao thoa", "song dung", "song am"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 SÓNG CƠ"] --> A["📌 Sóng ngang"]\n'
                        '   Root --> B["📌 Sóng dọc"]\n'
                        '   Root --> C["📌 Giao thoa sóng"]\n'
                        '   Root --> D["📌 Sóng dừng"]\n'
                        '   Root --> E["📌 Sóng âm"]\n'
                        '   C --> C1["Tăng cường / triệt tiêu"]\n'
                        '   D --> D1["Nút và bụng sóng"]\n'
                        '   E --> E1["Độ cao, độ to, âm sắc"]'
                    ),
                },
            },
        ],
        12: [
            {
                "id": "ly12_mindmap_song_dt",
                "name": "🗺️ Sơ đồ thang sóng điện từ",
                "desc": "Mindmap phân loại sóng điện từ theo bước sóng",
                "tags": ["song dien tu", "thang song", "tan so"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 THANG SÓNG ĐIỆN TỪ"] --> A["📻 Sóng vô tuyến"]\n'
                        '   Root --> B["📡 Vi ba"]\n'
                        '   Root --> C["🔥 Hồng ngoại"]\n'
                        '   Root --> D["👁️ Ánh sáng khả kiến"]\n'
                        '   Root --> E["🟣 Tử ngoại"]\n'
                        '   Root --> F["☢️ Tia X"]\n'
                        '   Root --> G["💥 Tia gamma"]\n'
                        '   A --> A1["Bước sóng dài nhất"]\n'
                        '   G --> G1["Bước sóng ngắn nhất"]'
                    ),
                },
            },
            {
                "id": "ly12_mindmap_hat_nhan",
                "name": "🗺️ Sơ đồ vật lý hạt nhân",
                "desc": "Mindmap các loại phóng xạ và phản ứng hạt nhân",
                "tags": ["hat nhan", "phong xa", "phan hach", "nhiet hach"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 VẬT LÝ HẠT NHÂN"] --> A["📌 Cấu tạo hạt nhân"]\n'
                        '   Root --> B["📌 Phóng xạ"]\n'
                        '   Root --> C["📌 Phản ứng hạt nhân"]\n'
                        '   B --> B1["Alpha (α)"]\n'
                        '   B --> B2["Beta (β)"]\n'
                        '   B --> B3["Gamma (γ)"]\n'
                        '   C --> C1["Phân hạch"]\n'
                        '   C --> C2["Nhiệt hạch"]'
                    ),
                },
            },
        ],
    },

    # ==========================================================================
    # HÓA HỌC
    # ==========================================================================
    "Hóa học": {
        10: [
            {
                "id": "hoa10_mindmap_nguyen_tu",
                "name": "🗺️ Sơ đồ cấu tạo nguyên tử",
                "desc": "Mindmap các thành phần cấu tạo nguyên tử",
                "tags": ["nguyen tu", "cau tao", "proton", "electron"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CẤU TẠO NGUYÊN TỬ"] --> A["📌 Hạt nhân"]\n'
                        '   Root --> B["📌 Vỏ electron"]\n'
                        '   A --> A1["Proton (p, +1)"]\n'
                        '   A --> A2["Neutron (n, 0)"]\n'
                        '   B --> B1["Electron (e, −1)"]\n'
                        '   B --> B2["Phân lớp: s, p, d, f"]'
                    ),
                },
            },
            {
                "id": "hoa10_mindmap_lien_ket",
                "name": "🗺️ Sơ đồ các loại liên kết hóa học",
                "desc": "Mindmap phân loại liên kết hóa học",
                "tags": ["lien ket", "ion", "cong hoa tri", "hydrogen"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 LIÊN KẾT HÓA HỌC"] --> A["📌 Liên kết ion"]\n'
                        '   Root --> B["📌 Liên kết cộng hóa trị"]\n'
                        '   Root --> C["📌 Liên kết kim loại"]\n'
                        '   Root --> D["📌 Tương tác yếu"]\n'
                        '   B --> B1["Phân cực"]\n'
                        '   B --> B2["Không phân cực"]\n'
                        '   D --> D1["Liên kết Hydrogen"]\n'
                        '   D --> D2["Van der Waals"]'
                    ),
                },
            },
        ],
        11: [
            {
                "id": "hoa11_mindmap_n_s",
                "name": "🗺️ Sơ đồ chuyển hóa N và S",
                "desc": "Mindmap các hợp chất của Nitrogen và Sulfur",
                "tags": ["nitrogen", "sulfur", "chuyen hoa"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CHUYỂN HÓA N & S"] --> A["📌 Nitrogen (N)"]\n'
                        '   Root --> B["📌 Sulfur (S)"]\n'
                        '   A --> A1["N₂ → NH₃"]\n'
                        '   A --> A2["NH₃ → NO → NO₂"]\n'
                        '   A --> A3["NO₂ → HNO₃"]\n'
                        '   B --> B1["S → SO₂"]\n'
                        '   B --> B2["SO₂ → SO₃"]\n'
                        '   B --> B3["SO₃ → H₂SO₄"]'
                    ),
                },
            },
            {
                "id": "hoa11_mindmap_huu_co",
                "name": "🗺️ Sơ đồ Hydrocarbon",
                "desc": "Mindmap phân loại hydrocarbon",
                "tags": ["hydrocarbon", "alkane", "alkene", "arene"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 HYDROCARBON"] --> A["📌 No (Alkane)"]\n'
                        '   Root --> B["📌 Không no"]\n'
                        '   Root --> C["📌 Thơm (Arene)"]\n'
                        '   B --> B1["Alkene (1 nối đôi)"]\n'
                        '   B --> B2["Alkyne (1 nối ba)"]\n'
                        '   C --> C1["Benzen và đồng đẳng"]'
                    ),
                },
            },
        ],
        12: [
            {
                "id": "hoa12_mindmap_carb",
                "name": "🗺️ Sơ đồ chuyển hóa Carbohydrate",
                "desc": "Mindmap chuyển hóa giữa các loại carbohydrate",
                "tags": ["carbohydrate", "glucose", "tinh bot", "chuyen hoa"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CARBOHYDRATE"] --> A["📌 Monosaccharide"]\n'
                        '   Root --> B["📌 Disaccharide"]\n'
                        '   Root --> C["📌 Polysaccharide"]\n'
                        '   A --> A1["Glucose"]\n'
                        '   A --> A2["Fructose"]\n'
                        '   B --> B1["Saccharose"]\n'
                        '   B --> B2["Maltose"]\n'
                        '   C --> C1["Tinh bột"]\n'
                        '   C --> C2["Cellulose"]'
                    ),
                },
            },
            {
                "id": "hoa12_mindmap_polymer",
                "name": "🗺️ Sơ đồ Polymer",
                "desc": "Mindmap phân loại polymer và ứng dụng",
                "tags": ["polymer", "vật liệu", "ứng dụng"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 POLYMER"] --> A["📌 Thiên nhiên"]\n'
                        '   Root --> B["📌 Tổng hợp"]\n'
                        '   A --> A1["Tinh bột"]\n'
                        '   A --> A2["Cellulose"]\n'
                        '   A --> A3["Protein"]\n'
                        '   B --> B1["PE, PVC, PS"]\n'
                        '   B --> B2["Tơ nilon, tơ lapsan"]\n'
                        '   B --> B3["Cao su buna"]'
                    ),
                },
            },
        ],
    },

    # ==========================================================================
    # SINH HỌC
    # ==========================================================================
    "Sinh học": {
        10: [
            {
                "id": "sinh10_mindmap_te_bao",
                "name": "🗺️ Sơ đồ cấu trúc tế bào",
                "desc": "Mindmap các bào quan trong tế bào nhân thực",
                "tags": ["te bao", "bao quan", "nhan thuc"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 CẤU TRÚC TẾ BÀO"] --> A["📌 Màng sinh chất"]\n'
                        '   Root --> B["📌 Tế bào chất"]\n'
                        '   Root --> C["📌 Nhân"]\n'
                        '   B --> B1["Ti thể"]\n'
                        '   B --> B2["Lục lạp"]\n'
                        '   B --> B3["Ribosome"]\n'
                        '   B --> B4["Lưới nội chất"]\n'
                        '   B --> B5["Golgi"]\n'
                        '   C --> C1["Màng nhân"]\n'
                        '   C --> C2["Chất nhiễm sắc"]'
                    ),
                },
            },
            {
                "id": "sinh10_mindmap_dai_phan_tu",
                "name": "🗺️ Sơ đồ các đại phân tử sinh học",
                "desc": "Mindmap 4 nhóm đại phân tử sinh học",
                "tags": ["dai phan tu", "protein", "lipid", "nucleic"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 ĐẠI PHÂN TỬ SINH HỌC"] --> A["📌 Carbohydrate"]\n'
                        '   Root --> B["📌 Lipid"]\n'
                        '   Root --> C["📌 Protein"]\n'
                        '   Root --> D["📌 Nucleic Acid"]\n'
                        '   A --> A1["Đường đơn, đôi, đa"]\n'
                        '   B --> B1["Mỡ, dầu, steroid"]\n'
                        '   C --> C1["20 axit amin"]\n'
                        '   D --> D1["DNA và RNA"]'
                    ),
                },
            },
        ],
        11: [
            {
                "id": "sinh11_mindmap_quang_hop",
                "name": "🗺️ Sơ đồ quang hợp",
                "desc": "Mindmap 2 pha của quá trình quang hợp",
                "tags": ["quang hop", "pha sang", "pha toi"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 QUANG HỢP"] --> A["📌 Pha sáng"]\n'
                        '   Root --> B["📌 Pha tối (Calvin)"]\n'
                        '   A --> A1["Xảy ra ở màng tilacoit"]\n'
                        '   A --> A2["Sản phẩm: ATP, NADPH, O₂"]\n'
                        '   B --> B1["Xảy ra ở chất nền lục lạp"]\n'
                        '   B --> B2["Sản phẩm: Glucose"]'
                    ),
                },
            },
            {
                "id": "sinh11_mindmap_ho_hap",
                "name": "🗺️ Sơ đồ hô hấp tế bào",
                "desc": "Mindmap 3 giai đoạn hô hấp tế bào",
                "tags": ["ho hap", "duong phan", "krebs", "chuoi truyen e"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 HÔ HẤP TẾ BÀO"] --> A["📌 Đường phân"]\n'
                        '   Root --> B["📌 Chu trình Krebs"]\n'
                        '   Root --> C["📌 Chuỗi truyền electron"]\n'
                        '   A --> A1["Tế bào chất"]\n'
                        '   A --> A2["Glucose → 2 Pyruvate"]\n'
                        '   B --> B1["Chất nền ti thể"]\n'
                        '   C --> C1["Màng trong ti thể"]\n'
                        '   C --> C2["Tạo nhiều ATP nhất"]'
                    ),
                },
            },
        ],
        12: [
            {
                "id": "sinh12_mindmap_mendel",
                "name": "🗺️ Sơ đồ quy luật Mendel",
                "desc": "Mindmap 2 quy luật Mendel cơ bản",
                "tags": ["mendel", "di truyen", "quy luat"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 QUY LUẬT MENDEL"] --> A["📌 Quy luật phân li"]\n'
                        '   Root --> B["📌 Quy luật phân li độc lập"]\n'
                        '   A --> A1["Mỗi tính trạng do 1 cặp alen"]\n'
                        '   A --> A2["F₁ dị hợp → F₂ tỉ lệ 3:1"]\n'
                        '   B --> B1["Các cặp alen phân li độc lập"]\n'
                        '   B --> B2["F₂ tỉ lệ 9:3:3:1"]'
                    ),
                },
            },
            {
                "id": "sinh12_mindmap_dna",
                "name": "🗺️ Sơ đồ di truyền phân tử",
                "desc": "Mindmap cơ chế di truyền phân tử",
                "tags": ["dna", "rna", "nhan doi", "phien ma", "dich ma"],
                "data": {
                    "type": "mermaid",
                    "code": (
                        'graph LR\n'
                        '   Root["🎯 DI TRUYỀN PHÂN TỬ"] --> A["📌 Nhân đôi DNA"]\n'
                        '   Root --> B["📌 Phiên mã"]\n'
                        '   Root --> C["📌 Dịch mã"]\n'
                        '   Root --> D["📌 Đột biến gen"]\n'
                        '   A --> A1["DNA → DNA"]\n'
                        '   B --> B1["DNA → mRNA"]\n'
                        '   C --> C1["mRNA → Protein"]\n'
                        '   D --> D1["Thay, thêm, mất cặp nu"]'
                    ),
                },
            },
        ],
    },
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def get_presets_for(subject: str, grade_num: int) -> list:
    """Lấy danh sách preset theo môn + lớp (chỉ lớp hiện tại)."""
    return list(PRESET_LABS.get(subject, {}).get(grade_num, []))


def get_all_presets_for_subject_grade_range(
    subject: str, grade_num: int, include_lower: bool = False
) -> list:
    """
    Lấy preset theo môn + lớp.
    - include_lower=True → thêm cả preset lớp thấp hơn.
    - Mỗi preset được bổ sung key 'grade' để biết lớp gốc.
    """
    result = []
    for g, presets in PRESET_LABS.get(subject, {}).items():
        if g == grade_num or (include_lower and g < grade_num):
            for p in presets:
                result.append({**p, "grade": g})
    return result


def has_presets_for_subject(subject: str) -> bool:
    """Kiểm tra môn có preset nào không."""
    return bool(PRESET_LABS.get(subject))

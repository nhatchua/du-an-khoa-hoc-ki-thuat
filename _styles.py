# ==============================================================================
# _styles.py — CSS giao diện
# ==============================================================================
import streamlit as st


def apply_styles():
    """Áp dụng toàn bộ CSS cho app."""
    st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }

    .brand-container {
        display: flex; align-items: center; justify-content: center; gap: 12px;
        margin-bottom: 20px; padding: 10px;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .school-icon { width: 45px; height: auto; transition: transform 0.3s ease; }
    .school-icon:hover { transform: scale(1.1); }
    .thiennhan-logo {
        width: 115px; height: auto; border-radius: 6px;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4); border: 1.5px solid #38bdf8;
    }

    .main-header { text-align: center; padding: 0px 0 15px 0; border-bottom: 1px dashed #475569; margin-bottom: 25px; }
    .main-title {
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1.5px;
    }
    .sub-title { color: #cbd5e1; font-size: 1.15rem; font-weight: 500;}
    .badge-tag {
        background: rgba(15, 23, 42, 0.7); border: 1px solid #38bdf8; color: #38bdf8;
        padding: 5px 15px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
        display: inline-block; margin-top: 8px; margin-right: 8px; box-shadow: 0 2px 5px rgba(56, 189, 248, 0.2);
    }

    .stButton > button {
        background: linear-gradient(135deg, #0284c7, #3b82f6) !important; color: white !important;
        border-radius: 10px !important; border: none !important; box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3) !important;
        transition: all 0.3s ease !important; font-weight: 700 !important; padding: 0.5rem 1rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(56, 189, 248, 0.6) !important;
        background: linear-gradient(135deg, #0369a1, #2563eb) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(10px);
        border-radius: 12px; padding: 5px; gap: 8px; border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 8px; border: none; color: #94a3b8; font-weight: 600; transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important; color: #38bdf8 !important;
        border-bottom: 3px solid #38bdf8 !important; box-shadow: inset 0 -3px 10px rgba(56, 189, 248, 0.1);
    }

    .feature-title {
        color: #38bdf8 !important;
        margin: 20px 0 10px 0;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .feature-item {
        margin: 5px 0;
        padding: 8px 12px;
        background: rgba(56, 189, 248, 0.12);
        border-left: 3px solid #38bdf8;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #cbd5e1 !important;
        line-height: 1.5;
    }
    .feature-item b {
        color: #38bdf8 !important;
        font-weight: 700;
    }
    .lab-box-container {
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border: 2px solid #0ea5e9;
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.2), inset 0 0 15px rgba(14, 165, 233, 0.05);
        padding: 25px; border-radius: 15px; margin-top: 25px; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lab-box-container::before {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, transparent, #38bdf8, transparent);
    }
    [data-testid="stChatMessage"] {
        border-radius: 15px; padding: 15px; margin-bottom: 12px;
        background: rgba(30, 41, 59, 0.6); border: 1px solid #475569; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    .stRadio > div { background-color: rgba(30, 41, 59, 0.6); padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    .short-link-badge { background-color: #1e293b; border: 1px dashed #38bdf8; padding: 8px 12px; border-radius: 8px; font-family: 'Courier New', Courier, monospace; font-size: 0.8rem; color: #38bdf8; text-align: center; margin: 10px 0; word-break: break-all; }

    /* Bảng biến thiên LaTeX (KaTeX display) — không tràn viền */
    .katex-display {
        overflow-x: auto !important;
        overflow-y: hidden !important;
        padding: 12px 0 !important;
        margin: 16px 0 !important;
    }
    .katex-display > .katex {
        font-size: 1.05em !important;
    }
    
    @media (max-width: 768px) {
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
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        [data-testid="column"], [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 12px !important;
        }
        .main-title { font-size: 1.4rem !important; line-height: 1.3 !important; }
        .sub-title { font-size: 0.9rem !important; }
        h1 { font-size: 1.3rem !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1.0rem !important; }
        .feature-item { font-size: 0.82rem !important; padding: 6px 10px !important; }
        .feature-title { font-size: 0.9rem !important; margin: 12px 0 6px 0 !important; }
        [data-testid="stSlider"] [role="slider"] {
            width: 22px !important; height: 22px !important;
        }
        [data-testid="stTextInput"] input { font-size: 0.9rem !important; }
        [data-testid="stButton"] button {
            font-size: 0.85rem !important;
            width: 100% !important;
        }
        [data-testid="stChatMessage"] {
            font-size: 0.9rem !important;
            padding: 10px !important;
        }
        [data-testid="stPlotlyChart"] {
            border-radius: 8px !important;
            overflow: hidden !important;
        }
        .main-header { padding: 0 !important; }
        .badge-tag { font-size: 0.7rem !important; padding: 4px 10px !important; }
    }
</style>
""", unsafe_allow_html=True)

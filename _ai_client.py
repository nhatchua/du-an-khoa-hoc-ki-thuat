# ==============================================================================
# _ai_client.py — Gọi Gemini API với fallback đa tầng
# ==============================================================================
import streamlit as st
import time
from google import genai
from google.genai import types
from _config import ALL_GEMINI_MODELS


def call_gemini_with_fallback(prompt_or_contents, system_instruction=None, json_mode=False):
    """
    Gọi Gemini với cơ chế fallback: model_queue × active_keys_pool.
    Đọc key từ st.session_state.active_keys_pool (do sidebar set).
    """
    active_keys_pool = st.session_state.get("active_keys_pool", [])
    working_model = st.session_state.get("working_model")

    model_queue = (
        [working_model] + [m for m in ALL_GEMINI_MODELS if m != working_model]
        if working_model else ALL_GEMINI_MODELS
    )
    last_error_msg = ""

    with st.status("Gia sư AI đang tiếp nhận yêu cầu...", expanded=True) as status_box:
        for current_model in model_queue:
            status_box.update(
                label=f"Đang thử kết nối AI qua kênh {current_model}...",
                state="running",
            )
            for current_key in active_keys_pool:
                try:
                    client = genai.Client(api_key=current_key)
                    cfg = types.GenerateContentConfig()
                    if system_instruction:
                        cfg.system_instruction = system_instruction
                    if json_mode:
                        cfg.response_mime_type = "application/json"

                    response = client.models.generate_content(
                        model=current_model,
                        contents=prompt_or_contents,
                        config=cfg,
                    )
                    st.session_state.working_model = current_model
                    status_box.update(label="Tuyệt vời, kết nối thành công!", state="complete")
                    return response.text

                except Exception as e:
                    err_str = str(e)
                    last_error_msg = err_str

                    if "404" in err_str or "NOT_FOUND" in err_str:
                        st.session_state.working_model = None
                        status_box.write(f"Kênh `{current_model}` đã bị chặn, chuyển kênh...")
                        break
                    elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        status_box.write("Kênh đang nghẽn, tự động đổi API Key...")
                        continue
                    elif any(err in err_str for err in ["503", "UNAVAILABLE", "high demand", "overloaded"]):
                        status_box.write(f"Máy chủ `{current_model}` bận, thử kênh khác...")
                        time.sleep(1)
                        break
                    else:
                        break

    status_box.update(
        label="Tất cả các kết nối hiện đang quá tải. Hãy nghỉ ngơi 1 phút nhé!",
        state="error",
    )
    raise Exception(f"Hệ thống đang quá tải. Lỗi kỹ thuật: {last_error_msg}")

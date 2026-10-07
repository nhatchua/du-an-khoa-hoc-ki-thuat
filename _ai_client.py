# ==============================================================================
# _ai_client.py — Gọi Gemini API với TỰ ĐỘNG QUÉT MODEL
# ==============================================================================
import streamlit as st
import time
from google import genai
from google.genai import types


# ==============================================================================
# QUÉT MODEL — Cache trong session
# ==============================================================================
def _scan_available_models(api_key: str):
    """Quét TẤT CẢ model khả dụng từ Google API."""
    try:
        client = genai.Client(api_key=api_key)
        all_models = []

        for m in client.models.list():
            name = m.name.replace("models/", "")
            actions = str(getattr(m, "supported_actions", "") or "")
            if "generateContent" in actions or "generateContent" in str(m):
                all_models.append(name)

        def priority(name):
            n = name.lower()
            if "3.8-flash" in n and "lite" not in n: return 1
            if "3.8" in n: return 2
            if "3.5-flash" in n: return 3
            if "3.5" in n: return 4
            if "3.1-flash-lite" in n: return 5
            if "gemini-3-flash" in n: return 6
            if "gemini-3" in n: return 7
            if "2.5-flash" in n and "lite" not in n: return 10
            if "2.5-flash-lite" in n: return 11
            if "2.5-pro" in n: return 12
            if "2.0-flash" in n and "lite" not in n and "exp" not in n: return 13
            if "2.0-flash" in n: return 14
            if "flash-latest" in n: return 15
            if "1.5" in n: return 30
            return 99

        all_models.sort(key=priority)
        return all_models

    except Exception as e:
        st.session_state["_scan_error"] = str(e)
        return []


def _get_model_pool():
    """
    Danh sách model ƯU TIÊN HARD-CODE — không quét API.
    Nếu tất cả fail → mới quét lại từ API.
    """
    # ===== DANH SÁCH ƯU TIÊN (đã test OK) =====
    PREFERRED_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
    ]

    # Chỉ quét API nếu cache rỗng VÀ đã thử hết PREFERRED fail
    cached = st.session_state.get("_available_models_cache")
    if cached:
        return cached

    return PREFERRED_MODELS

# ==============================================================================
# HÀM CHÍNH
# ==============================================================================
def call_gemini_with_fallback(prompt_or_contents, system_instruction=None, json_mode=False):
    active_keys_pool = st.session_state.get("active_keys_pool", [])
    if not active_keys_pool:
        raise Exception("Chưa có API Key. Vui lòng dán key ở thanh bên trái.")

    working_model = st.session_state.get("working_model")
    model_pool = _get_model_pool()

    if not model_pool:
        scan_err = st.session_state.get("_scan_error", "")
        raise Exception(f"Không quét được model khả dụng. Chi tiết: {scan_err}")

    model_queue = (
        [working_model] + [m for m in model_pool if m != working_model]
        if working_model and working_model in model_pool
        else model_pool
    )

    last_error_msg = ""

    with st.status("Gia sư AI đang tiếp nhận yêu cầu...", expanded=True) as status_box:
        status_box.write(f"🔍 Đã quét được **{len(model_pool)} model** khả dụng")

        for current_model in model_queue:
            status_box.update(
                label=f"Đang thử kết nối qua kênh {current_model}...",
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
                    status_box.update(
                        label=f"✅ Kết nối thành công qua {current_model}!",
                        state="complete",
                    )
                    return response.text

                except Exception as e:
                    err_str = str(e)
                    last_error_msg = err_str

                    if "404" in err_str or "NOT_FOUND" in err_str:
                        status_box.write(f"⏭️ `{current_model}` không khả dụng, chuyển kênh...")
                        cache = st.session_state.get("_available_models_cache", [])
                        if current_model in cache:
                            cache.remove(current_model)
                            st.session_state["_available_models_cache"] = cache
                        if st.session_state.get("working_model") == current_model:
                            st.session_state.working_model = None
                        break

                    elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        status_box.write("⚠️ Kênh nghẽn, đổi API Key...")
                        continue

                    elif any(x in err_str for x in ["503", "UNAVAILABLE", "high demand", "overloaded"]):
                        status_box.write(f"⏳ Máy chủ `{current_model}` bận...")
                        time.sleep(1)
                        break

                    elif "403" in err_str or "PERMISSION_DENIED" in err_str:
                        status_box.write(f"🚫 Key không có quyền `{current_model}`")
                        break

                    else:
                        status_box.write(f"❌ Lỗi `{current_model}`: {err_str[:120]}")
                        break

        # ===== QUÉT LẠI NẾU TẤT CẢ FAIL =====
        status_box.update(label="Đang quét lại danh sách model...", state="running")
        st.session_state.pop("_available_models_cache", None)
        new_pool = _get_model_pool()

        if new_pool:
            status_box.write(f"🔄 Quét lại {len(new_pool)} model, thử lại...")
            for new_model in new_pool:
                try:
                    client = genai.Client(api_key=active_keys_pool[0])
                    cfg = types.GenerateContentConfig()
                    if system_instruction:
                        cfg.system_instruction = system_instruction
                    if json_mode:
                        cfg.response_mime_type = "application/json"

                    response = client.models.generate_content(
                        model=new_model,
                        contents=prompt_or_contents,
                        config=cfg,
                    )
                    st.session_state.working_model = new_model
                    status_box.update(
                        label=f"✅ Kết nối thành công qua {new_model}!",
                        state="complete",
                    )
                    return response.text
                except Exception:
                    continue

    status_box.update(
        label="❌ Tất cả kênh thất bại. Vui lòng kiểm tra API Key!",
        state="error",
    )
    raise Exception(
        f"Không thể kết nối AI. Đã quét {len(model_pool)} model. "
        f"Lỗi cuối: {last_error_msg}"
    )


def reset_model_cache():
    """Xóa cache model — gọi khi user thay đổi API key."""
    st.session_state.pop("_available_models_cache", None)
    st.session_state.pop("_scan_error", None)
    st.session_state["working_model"] = None

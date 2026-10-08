# ==============================================================================
# _ai_client.py — Gọi Gemini API với TỰ ĐỘNG QUÉT MODEL THEO TỪNG KEY
# ==============================================================================
import streamlit as st
import time
import hashlib
from google import genai
from google.genai import types
from _config import FALLBACK_MODELS, get_model_priority


# ==============================================================================
# HELPER: HASH API KEY (không lưu key thô vào cache key)
# ==============================================================================
def _key_hash(api_key: str) -> str:
    """Hash ngắn của API key — dùng làm cache key an toàn."""
    return hashlib.md5(api_key.encode()).hexdigest()[:10]


# ==============================================================================
# QUÉT MODEL — Cache theo TỪNG API KEY
# ==============================================================================
def _scan_available_models(api_key: str):
    """
    Quét TẤT CẢ model khả dụng từ Google API cho key cụ thể.
    Cache theo hash của key — mỗi học sinh có cache riêng.
    """
    h = _key_hash(api_key)
    cache_key = f"_model_cache_{h}"
    scan_flag = f"_model_scanned_{h}"
    err_key = f"_model_scan_error_{h}"

    # Nếu đã quét cho key này → trả cache
    if st.session_state.get(scan_flag):
        return st.session_state.get(cache_key, [])

    try:
        client = genai.Client(api_key=api_key)
        all_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            actions = str(getattr(m, "supported_actions", "") or "")
            if "generateContent" in actions or "generateContent" in str(m):
                all_models.append(name)

        # Sắp xếp theo priority THẬT (model 2.0, 1.5 lên đầu)
        all_models.sort(key=get_model_priority)

        st.session_state[scan_flag] = True
        st.session_state[cache_key] = all_models
        st.session_state.pop(err_key, None)
        return all_models

    except Exception as e:
        st.session_state[err_key] = str(e)
        return []


def _get_model_pool(api_key: str):
    """
    Lấy danh sách model khả dụng cho key cụ thể.
    - Ưu tiên cache.
    - Nếu chưa có → quét API thật.
    - Nếu quét lỗi → fallback danh sách an toàn.
    """
    h = _key_hash(api_key)
    cache_key = f"_model_cache_{h}"

    cached = st.session_state.get(cache_key)
    if cached:
        return cached

    scanned = _scan_available_models(api_key)
    if scanned:
        return scanned

    # Fallback khi không quét được
    return list(FALLBACK_MODELS)


# ==============================================================================
# HÀM CHÍNH
# ==============================================================================
def call_gemini_with_fallback(prompt_or_contents, system_instruction=None, json_mode=False):
    active_keys_pool = st.session_state.get("active_keys_pool", [])
    if not active_keys_pool:
        raise Exception("Chưa có API Key. Vui lòng dán key ở thanh bên trái.")

    primary_key = active_keys_pool[0]
    h = _key_hash(primary_key)
    working_model = st.session_state.get("working_model")

    # Lấy model pool cho key này
    model_pool = _get_model_pool(primary_key)
    if not model_pool:
        scan_err = st.session_state.get(f"_model_scan_error_{h}", "")
        raise Exception(f"Không quét được model khả dụng cho key này. Chi tiết: {scan_err}")

    # working_model ưu tiên lên đầu nếu còn trong pool
    if working_model and working_model in model_pool:
        model_queue = [working_model] + [m for m in model_pool if m != working_model]
    else:
        model_queue = list(model_pool)

    last_error_msg = ""
    tried_models = []

    with st.status("Gia sư AI đang tiếp nhận yêu cầu...", expanded=True) as status_box:
        status_box.write(f"🔍 Đã quét được **{len(model_pool)} model** khả dụng cho key của em")

        for current_model in model_queue:
            tried_models.append(current_model)
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
                        # Model không tồn tại cho key này → xóa khỏi cache
                        status_box.write(f"⏭️ `{current_model}` không khả dụng, chuyển model...")
                        cache_key = f"_model_cache_{h}"
                        cache = st.session_state.get(cache_key, [])
                        if current_model in cache:
                            cache.remove(current_model)
                            st.session_state[cache_key] = cache
                        if st.session_state.get("working_model") == current_model:
                            st.session_state.working_model = None
                        break  # next model

                    elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        status_box.write("⚠️ Kênh nghẽn quota, đổi key khác...")
                        continue  # next key

                    elif any(x in err_str for x in
                             ["503", "UNAVAILABLE", "high demand", "overloaded",
                              "500", "INTERNAL"]):
                        status_box.write(f"⏳ Máy chủ `{current_model}` bận, chuyển model...")
                        time.sleep(0.5)
                        break  # next model

                    elif "403" in err_str or "PERMISSION_DENIED" in err_str:
                        status_box.write(f"🚫 Key không có quyền dùng `{current_model}`")
                        break  # next model

                    elif "400" in err_str or "INVALID_ARGUMENT" in err_str:
                        status_box.write(f"❌ Request sai với `{current_model}`")
                        break  # next model

                    else:
                        status_box.write(f"❌ Lỗi `{current_model}`: {err_str[:150]}")
                        break  # next model

        # ===== TẤT CẢ FAIL → QUÉT LẠI 1 LẦN =====
        status_box.update(label="🔄 Đang quét lại danh sách model...", state="running")
        cache_key = f"_model_cache_{h}"
        scan_flag = f"_model_scanned_{h}"
        st.session_state.pop(cache_key, None)
        st.session_state.pop(scan_flag, None)
        new_pool = _get_model_pool(primary_key)

        if new_pool and set(new_pool) != set(model_pool):
            status_box.write(f"🔄 Phát hiện {len(new_pool)} model mới, thử lại...")
            for new_model in new_pool:
                if new_model in tried_models:
                    continue
                try:
                    client = genai.Client(api_key=primary_key)
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
        f"Không thể kết nối AI. Đã thử {len(tried_models)} model. "
        f"Lỗi cuối: {last_error_msg[:300]}"
    )


# ==============================================================================
# RESET CACHE
# ==============================================================================
def reset_model_cache():
    """Xóa TOÀN BỘ cache model (mọi key)."""
    keys_to_remove = [
        k for k in list(st.session_state.keys())
        if k.startswith("_model_cache_")
        or k.startswith("_model_scanned_")
        or k.startswith("_model_scan_error_")
    ]
    for k in keys_to_remove:
        st.session_state.pop(k, None)
    st.session_state["working_model"] = None


def reset_model_cache_for_key(api_key: str):
    """Xóa cache model cho 1 key cụ thể (khi user đổi key)."""
    h = _key_hash(api_key)
    for prefix in ["_model_cache_", "_model_scanned_", "_model_scan_error_"]:
        st.session_state.pop(f"{prefix}{h}", None)
    st.session_state["working_model"] = None

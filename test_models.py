# ==============================================================================
# test_models.py — QUÉT & TEST TOÀN BỘ MODEL GEMINI
# Chạy: python test_models.py
# ==============================================================================
import sys
from google import genai
from google.genai import types


# ====== DÁN API KEY CỦA BẠN VÀO ĐÂY ======
API_KEY = "AIzaSy..."   # ← ĐỔI THÀNH KEY THẬT
# ==========================================


# ==============================================================================
# DANH SÁCH MODEL CẦN TEST — CẬP NHẬT 2026
# ==============================================================================
MODELS_TO_TEST = [
    # ===== Dòng Gemini 3.x (MỚI NHẤT - 2026) =====
    "gemini-3.8-flash",                # Flagship flash mới nhất
    "gemini-3.5-flash",                # Phiên bản kế tiếp
    "gemini-3.1-flash-lite",           # Bản nhẹ, nhanh
    "gemini-3.8-flash-cyber",          # Chuyên an ninh mạng
    "gemini-3.8-live",                 # Live streaming
    "gemini-3-flash-preview",          # Preview
    "gemini-3-flash",                  # Bản 3.0 gốc
    "gemini-3-pro",                    # Pro

    # ===== Dòng Gemini 2.x (ỔN ĐỊNH - 2024-2025) =====
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-exp",

    # ===== Alias trỏ tới bản mới nhất =====
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",

    # ===== Dòng 1.5 (CÓ THỂ ĐÃ BỎ) =====
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]


# ==============================================================================
# HÀM TEST 1 MODEL
# ==============================================================================
def test_one_model(client, model_name):
    """Test 1 model, trả về (ok, message, latency)."""
    import time
    t0 = time.time()
    try:
        cfg = types.GenerateContentConfig()
        response = client.models.generate_content(
            model=model_name,
            contents="Trả lời đúng 1 chữ: OK",
            config=cfg,
        )
        latency = time.time() - t0
        text = (response.text or "").strip()
        return True, f"✅ OK — Trả lời: {text[:30]}", latency
    except Exception as e:
        latency = time.time() - t0
        err = str(e)
        if "404" in err or "NOT_FOUND" in err:
            return False, "❌ 404 — Model không tồn tại", latency
        elif "429" in err or "RESOURCE_EXHAUSTED" in err:
            return False, "⚠️ 429 — Hết quota", latency
        elif "403" in err or "PERMISSION_DENIED" in err:
            return False, "🚫 403 — Key không có quyền", latency
        elif "400" in err or "INVALID_ARGUMENT" in err:
            return False, "❌ 400 — Request sai", latency
        elif "503" in err or "UNAVAILABLE" in err:
            return False, "⏳ 503 — Server bận", latency
        else:
            return False, f"❓ Lỗi: {err[:120]}", latency


# ==============================================================================
# XẾP HẠNG ƯU TIÊN MODEL (dùng để sort khi in kết quả)
# ==============================================================================
def priority(name):
    n = name.lower()
    # Dòng 3.x mới nhất
    if "3.8-flash" in n and "lite" not in n and "cyber" not in n: return 1
    if "3.8" in n: return 2
    if "3.5-flash" in n: return 3
    if "3.5" in n: return 4
    if "3.1-flash-lite" in n: return 5
    if "3.1" in n: return 6
    if "gemini-3-flash" in n: return 7
    if "gemini-3" in n: return 8
    # Dòng 2.x ổn định
    if "2.5-flash" in n and "lite" not in n: return 10
    if "2.5-flash-lite" in n: return 11
    if "2.5-pro" in n: return 12
    if "2.0-flash" in n and "lite" not in n and "exp" not in n: return 13
    if "2.0-flash" in n: return 14
    if "flash-latest" in n: return 15
    if "flash-lite-latest" in n: return 16
    if "pro-latest" in n: return 17
    # Dòng 1.5 cũ
    if "1.5" in n: return 30
    return 99


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("=" * 75)
    print("🧪 QUÉT & TEST TOÀN BỘ MODEL GEMINI")
    print("=" * 75)

    # ===== Kiểm tra API key =====
    if not API_KEY or API_KEY == "AIzaSy..." or len(API_KEY) < 20:
        print("❌ CHƯA ĐIỀN API KEY!")
        print("   Mở file test_models.py, sửa dòng API_KEY = \"...\"")
        print("   thành key thật của bạn.")
        sys.exit(1)

    print(f"🔑 API Key: {API_KEY[:15]}...{API_KEY[-5:]}")
    print()

    # ===== Khởi tạo client =====
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"❌ Không tạo được client: {e}")
        sys.exit(1)

    # ==========================================================================
    # BƯỚC A: QUÉT TẤT CẢ MODEL TỪ GOOGLE API
    # ==========================================================================
    print("=" * 75)
    print("📜 BƯỚC A — QUÉT TẤT CẢ MODEL TỪ GOOGLE API")
    print("=" * 75)

    api_models = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            actions = str(getattr(m, "supported_actions", "") or "")
            supports_gen = "generateContent" in actions or "generateContent" in str(m)
            marker = "✅" if supports_gen else "  "
            print(f"  {marker} {name}")
            if supports_gen:
                api_models.append(name)
    except Exception as e:
        print(f"⚠️ Không list được models: {e}")

    print(f"\n→ Tìm thấy {len(api_models)} model hỗ trợ generateContent\n")

    # ==========================================================================
    # BƯỚC B: TEST TỪNG MODEL
    # ==========================================================================
    print("=" * 75)
    print("🧪 BƯỚC B — TEST TỪNG MODEL")
    print("=" * 75)

    # Gộp danh sách: ưu tiên model trong MODELS_TO_TEST, thêm model mới từ API
    test_list = list(MODELS_TO_TEST)
    for m in api_models:
        if m not in test_list:
            test_list.append(m)

    working = []
    for model in test_list:
        print(f"\n▶️  {model}")
        ok, msg, latency = test_one_model(client, model)
        print(f"   {msg}  ({latency:.2f}s)")
        if ok:
            working.append((model, latency))

    # ==========================================================================
    # BƯỚC C: TỔNG KẾT
    # ==========================================================================
    print("\n" + "=" * 75)
    print("📊 BƯỚC C — TỔNG KẾT")
    print("=" * 75)

    if working:
        # Sắp xếp theo priority + latency
        working.sort(key=lambda x: (priority(x[0]), x[1]))

        print(f"\n✅ CÓ {len(working)} MODEL HOẠT ĐỘNG (đã xếp theo ưu tiên):\n")
        for m, lat in working:
            print(f"   ✅ {m:45s} ({lat:.2f}s)")

        print("\n" + "=" * 75)
        print("👉 COPY DANH SÁCH NÀY VÀO _config.py:")
        print("=" * 75)
        print("\nALL_GEMINI_MODELS = [")
        for m, _ in working:
            print(f'    "{m}",')
        print("]\n")

        print("=" * 75)
        print("👉 HOẶC COPY DANH SÁCH NÀY VÀO _ai_client.py (hàm priority):")
        print("=" * 75)
        print()
        for idx, (m, _) in enumerate(working, 1):
            print(f'    if "{m}" in n: return {idx}')

    else:
        print("\n❌ KHÔNG CÓ MODEL NÀO HOẠT ĐỘNG!")
        print("\n💡 Kiểm tra:")
        print("   1. API key đúng chưa? (https://aistudio.google.com/apikey)")
        print("   2. Key có bị Google khóa không? (thử tạo key mới)")
        print("   3. Mạng có ổn không? (thử tắt/bật VPN)")
        print("   4. Google AI Studio có bị chặn ở khu vực của bạn không?")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()

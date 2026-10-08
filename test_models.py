# ==============================================================================
# test_models.py — QUÉT & TEST MODEL GEMINI CHO KEY CỦA BẠN
# Chạy: python test_models.py
# ==============================================================================
import sys
import time
from google import genai
from google.genai import types


# ====== DÁN API KEY CỦA BẠN VÀO ĐÂY ======
API_KEY = "AIzaSy..."   # ← ĐỔI THÀNH KEY THẬT
# ==========================================


# ==============================================================================
# DANH SÁCH MODEL ỨNG VIÊN — CHỈ CÁC MODEL THẬT (2024-2025)
# (Dùng để test khi API không list được, hoặc để xác nhận model hoạt động)
# ==============================================================================
CANDIDATE_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-flash-latest",
    "gemini-pro-latest",
]


def get_model_priority(name: str) -> int:
    """Xếp hạng ưu tiên — số nhỏ = ưu tiên cao."""
    n = (name or "").lower()
    if "2.0-flash-exp" in n:               return 1
    if "2.0-flash-lite" in n:              return 2
    if "2.0-flash" in n:                   return 3
    if "2.0-pro" in n:                     return 4
    if "2.0" in n:                         return 5
    if "flash-latest" in n:                return 6
    if "pro-latest" in n:                  return 7
    if "1.5-flash" in n and "8b" not in n: return 10
    if "1.5-flash-8b" in n:                return 11
    if "1.5-pro" in n:                     return 12
    if "1.5" in n:                         return 13
    if "exp" in n:                         return 20
    return 99


def test_one_model(client, model_name):
    """Test 1 model, trả về (ok, message, latency)."""
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
            return False, "❌ 404 — Model không tồn tại cho key này", latency
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


def main():
    print("=" * 75)
    print("🧪 QUÉT & TEST MODEL GEMINI CHO API KEY CỦA BẠN")
    print("=" * 75)

    if not API_KEY or API_KEY == "AIzaSy..." or len(API_KEY) < 20:
        print("❌ CHƯA ĐIỀN API KEY!")
        print("   Mở file test_models.py, sửa dòng API_KEY = \"...\"")
        sys.exit(1)

    print(f"🔑 API Key: {API_KEY[:15]}...{API_KEY[-5:]}")
    print()

    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"❌ Không tạo được client: {e}")
        sys.exit(1)

    # ==========================================================================
    # BƯỚC A: QUÉT MODEL TỪ API
    # ==========================================================================
    print("=" * 75)
    print("📜 BƯỚC A — QUÉT MODEL KHẢ DỤNG TỪ GOOGLE API")
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

    print(f"\n→ API báo cáo {len(api_models)} model hỗ trợ generateContent\n")

    # ==========================================================================
    # BƯỚC B: TEST TỪNG MODEL
    # ==========================================================================
    print("=" * 75)
    print("🧪 BƯỚC B — TEST TỪNG MODEL")
    print("=" * 75)

    # Gộp: model từ API trước, sau đó model ứng viên (tránh trùng)
    test_list = list(api_models)
    for m in CANDIDATE_MODELS:
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
        working.sort(key=lambda x: (get_model_priority(x[0]), x[1]))

        print(f"\n✅ CÓ {len(working)} MODEL HOẠT ĐỘNG (xếp theo ưu tiên):\n")
        for m, lat in working:
            print(f"   ✅ {m:45s} ({lat:.2f}s)")

        print("\n" + "=" * 75)
        print("👉 COPY DANH SÁCH NÀY VÀO _config.py (biến FALLBACK_MODELS):")
        print("=" * 75)
        print("\nFALLBACK_MODELS = [")
        for m, _ in working[:6]:  # tối đa 6 model tốt nhất
            print(f'    "{m}",')
        print("]\n")
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

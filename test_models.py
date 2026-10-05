# ==============================================================================
# test_models.py — TEST TOÀN BỘ MODEL GEMINI
# Chạy: python test_models.py
# ==============================================================================
import sys
from google import genai
from google.genai import types

# ====== DÁN API KEY CỦA BẠN VÀO ĐÂY ======
API_KEY = "AIzaSy..."   # ← ĐỔI THÀNH KEY THẬT CỦA BẠN
# ==========================================


# Danh sách model CẦN TEST (gồm cả model cũ và model mới)
MODELS_TO_TEST = [
    # ===== Model trong _config.py hiện tại (có thể sai) =====
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",

    # ===== Model Gemini thật (2024-2025) =====
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",

    # ===== Model cũ nhưng ổn định =====
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
]


def test_one_model(client, model_name):
    """Test 1 model, trả về (ok, message)."""
    try:
        cfg = types.GenerateContentConfig()
        response = client.models.generate_content(
            model=model_name,
            contents="Trả lời đúng 1 chữ: OK",
            config=cfg,
        )
        text = (response.text or "").strip()
        return True, f"✅ OK — Trả lời: {text[:50]}"
    except Exception as e:
        err = str(e)
        if "404" in err or "NOT_FOUND" in err:
            return False, "❌ 404 — Model không tồn tại"
        elif "429" in err or "RESOURCE_EXHAUSTED" in err:
            return False, "⚠️ 429 — Hết quota / key bị giới hạn"
        elif "403" in err or "PERMISSION_DENIED" in err:
            return False, "🚫 403 — Key không có quyền"
        elif "400" in err or "INVALID_ARGUMENT" in err:
            return False, "❌ 400 — Request sai"
        elif "503" in err or "UNAVAILABLE" in err:
            return False, "⏳ 503 — Server bận"
        else:
            return False, f"❓ Lỗi khác: {err[:120]}"


def main():
    print("=" * 70)
    print("🧪 TEST TOÀN BỘ MODEL GEMINI")
    print("=" * 70)

    # Kiểm tra API key
    if not API_KEY or API_KEY == "AIzaSy..." or len(API_KEY) < 20:
        print("❌ CHƯA ĐIỀN API KEY!")
        print("   Mở file test_models.py, sửa dòng API_KEY = \"...\"")
        print("   thành key thật của bạn.")
        sys.exit(1)

    print(f"🔑 API Key: {API_KEY[:15]}...{API_KEY[-5:]}")
    print(f"📋 Sẽ test {len(MODELS_TO_TEST)} model\n")

    # Khởi tạo client
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"❌ Không tạo được client: {e}")
        sys.exit(1)

    # Bước A: Liệt kê model thật mà key có thể dùng
    print("=" * 70)
    print("📜 DANH SÁCH MODEL THẬT (từ Google API)")
    print("=" * 70)
    real_models = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            real_models.append(name)
            print(f"   • {name}")
    except Exception as e:
        print(f"⚠️ Không list được models: {e}")
    print()

    if not real_models:
        print("⚠️ Không lấy được danh sách model. Vẫn tiếp tục test thủ công...\n")

    # Bước B: Test từng model
    print("=" * 70)
    print("🧪 KẾT QUẢ TEST TỪNG MODEL")
    print("=" * 70)

    working = []
    for model in MODELS_TO_TEST:
        print(f"\n▶️  Đang test: {model}")
        ok, msg = test_one_model(client, model)
        print(f"   {msg}")
        if ok:
            working.append(model)

    # Bước C: Tổng kết
    print("\n" + "=" * 70)
    print("📊 TỔNG KẾT")
    print("=" * 70)

    if working:
        print(f"\n✅ CÓ {len(working)} MODEL HOẠT ĐỘNG:\n")
        for m in working:
            print(f"   ✅ {m}")
        print("\n" + "=" * 70)
        print("👉 COPY DANH SÁCH NÀY VÀO _config.py:")
        print("=" * 70)
        print("\nALL_GEMINI_MODELS = [")
        for m in working:
            print(f'    "{m}",')
        print("]\n")
    else:
        print("\n❌ KHÔNG CÓ MODEL NÀO HOẠT ĐỘNG!")
        print("\n💡 Gợi ý kiểm tra:")
        print("   1. API key có đúng không? (vào https://aistudio.google.com/apikey)")
        print("   2. Key có bị Google khóa không? (thử tạo key mới)")
        print("   3. Mạng có ổn không? (thử tắt VPN / bật VPN)")
        print("   4. Google AI Studio có bị chặn ở khu vực của bạn không?")

    print("=" * 70)


if __name__ == "__main__":
    main()

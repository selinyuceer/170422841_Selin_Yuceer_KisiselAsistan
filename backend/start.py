#!/usr/bin/env python3
"""
Kişisel Asistan Backend Başlatma Scripti
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

def main():
    """Ana fonksiyon"""
    # Environment variables yükle
    load_dotenv()
    
    # Gerekli environment variables kontrolü
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Eksik environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 .env dosyasını oluşturun ve gerekli değerleri ekleyin.")
        print("   README.md dosyasındaki örneğe bakın.")
        sys.exit(1)
    
    # Sunucu ayarları
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🚀 Kişisel Asistan Backend başlatılıyor...")
    print(f"📍 Adres: http://{host}:{port}")
    print(f"🔧 Debug modu: {'Açık' if debug else 'Kapalı'}")
    print(f"📚 API Dokümantasyonu: http://{host}:{port}/docs")
    print("-" * 50)
    
    try:
        # FastAPI uygulamasını başlat
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if debug else "warning"
        )
    except KeyboardInterrupt:
        print("\n👋 Sunucu kapatılıyor...")
    except Exception as e:
        print(f"❌ Sunucu başlatılırken hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
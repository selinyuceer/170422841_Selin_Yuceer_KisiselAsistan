#!/usr/bin/env python3
"""
Basit Gemini API Test Scripti
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Environment variables yükle
load_dotenv()

def test_gemini():
    """Gemini API'yi test et"""
    try:
        # API anahtarını al
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY bulunamadı!")
            return False
        
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # Gemini'yi yapılandır
        genai.configure(api_key=api_key)
        
        # Model oluştur
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test mesajı gönder
        print("📤 Test mesajı gönderiliyor...")
        response = model.generate_content("Merhaba, nasılsın? Kısa bir yanıt ver.")
        
        if response.text:
            print(f"✅ Başarılı! Yanıt: {response.text}")
            return True
        else:
            print("❌ Yanıt boş!")
            return False
            
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Gemini API Test Başlıyor...")
    success = test_gemini()
    print(f"🏁 Test {'başarılı' if success else 'başarısız'}!") 
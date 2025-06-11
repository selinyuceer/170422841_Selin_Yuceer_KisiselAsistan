#!/usr/bin/env python3
"""
API Test Scripti
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Sağlık kontrolü testi"""
    print("🔍 Sağlık kontrolü testi...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Sağlık kontrolü başarılı")
            print(f"   Yanıt: {response.json()}")
        else:
            print(f"❌ Sağlık kontrolü başarısız: {response.status_code}")
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")

def test_chat():
    """Chat API testi"""
    print("\n💬 Chat API testi...")
    try:
        data = {
            "message": "Merhaba, nasılsın?",
            "message_type": "text",
            "user_id": "test_user_123"
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/message", json=data)
        if response.status_code == 200:
            print("✅ Chat testi başarılı")
            result = response.json()
            print(f"   AI Yanıtı: {result['response']}")
        else:
            print(f"❌ Chat testi başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
    except Exception as e:
        print(f"❌ Chat test hatası: {e}")

def test_notes():
    """Notes API testi"""
    print("\n📝 Notes API testi...")
    try:
        # Not oluştur
        data = {
            "title": "Test Notu",
            "content": "Bu bir test notudur.",
            "user_id": "test_user_123",
            "is_voice_note": False
        }
        
        response = requests.post(f"{BASE_URL}/api/notes/create", json=data)
        if response.status_code == 200:
            print("✅ Not oluşturma testi başarılı")
            note = response.json()
            note_id = note['id']
            print(f"   Not ID: {note_id}")
            
            # Notları listele
            response = requests.get(f"{BASE_URL}/api/notes/list/test_user_123")
            if response.status_code == 200:
                notes = response.json()
                print(f"✅ Not listeleme başarılı: {len(notes)} not bulundu")
            else:
                print(f"❌ Not listeleme başarısız: {response.status_code}")
        else:
            print(f"❌ Not oluşturma başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
    except Exception as e:
        print(f"❌ Notes test hatası: {e}")

def test_weather():
    """Weather API testi"""
    print("\n🌤️ Weather API testi...")
    try:
        data = {
            "city": "Istanbul",
            "country_code": "TR"
        }
        
        response = requests.post(f"{BASE_URL}/api/weather/current", json=data)
        if response.status_code == 200:
            print("✅ Hava durumu testi başarılı")
            weather = response.json()
            print(f"   Şehir: {weather['city']}")
            print(f"   Sıcaklık: {weather['temperature']}°C")
            print(f"   Durum: {weather['description']}")
        else:
            print(f"❌ Hava durumu testi başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
    except Exception as e:
        print(f"❌ Weather test hatası: {e}")

def test_reminders():
    """Reminders API testi"""
    print("\n⏰ Reminders API testi...")
    try:
        # Yarın için hatırlatıcı oluştur
        tomorrow = datetime.now() + timedelta(days=1)
        
        data = {
            "title": "Test Hatırlatıcısı",
            "description": "Bu bir test hatırlatıcısıdır.",
            "reminder_time": tomorrow.isoformat(),
            "user_id": "test_user_123"
        }
        
        response = requests.post(f"{BASE_URL}/api/reminders/create", json=data)
        if response.status_code == 200:
            print("✅ Hatırlatıcı oluşturma testi başarılı")
            reminder = response.json()
            print(f"   Hatırlatıcı ID: {reminder['id']}")
            
            # Hatırlatıcıları listele
            response = requests.get(f"{BASE_URL}/api/reminders/list/test_user_123")
            if response.status_code == 200:
                reminders = response.json()
                print(f"✅ Hatırlatıcı listeleme başarılı: {len(reminders)} hatırlatıcı bulundu")
            else:
                print(f"❌ Hatırlatıcı listeleme başarısız: {response.status_code}")
        else:
            print(f"❌ Hatırlatıcı oluşturma başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
    except Exception as e:
        print(f"❌ Reminders test hatası: {e}")

def test_calendar():
    """Calendar API testi"""
    print("\n📅 Calendar API testi...")
    try:
        # Yarın için etkinlik oluştur
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_end = tomorrow + timedelta(hours=2)
        
        data = {
            "title": "Test Etkinliği",
            "description": "Bu bir test etkinliğidir.",
            "start_time": tomorrow.isoformat(),
            "end_time": tomorrow_end.isoformat(),
            "user_id": "test_user_123"
        }
        
        response = requests.post(f"{BASE_URL}/api/calendar/create-event", json=data)
        if response.status_code == 200:
            print("✅ Etkinlik oluşturma testi başarılı")
            event = response.json()
            print(f"   Etkinlik ID: {event['id']}")
            
            # Etkinlikleri listele
            response = requests.get(f"{BASE_URL}/api/calendar/events/test_user_123")
            if response.status_code == 200:
                events = response.json()
                print(f"✅ Etkinlik listeleme başarılı: {len(events)} etkinlik bulundu")
            else:
                print(f"❌ Etkinlik listeleme başarısız: {response.status_code}")
        else:
            print(f"❌ Etkinlik oluşturma başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
    except Exception as e:
        print(f"❌ Calendar test hatası: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🧪 API Test Süreci Başlıyor...")
    print("=" * 50)
    
    # Tüm testleri çalıştır
    test_health()
    test_chat()
    test_notes()
    test_weather()
    test_reminders()
    test_calendar()
    
    print("\n" + "=" * 50)
    print("🏁 Test süreci tamamlandı!")

if __name__ == "__main__":
    main() 
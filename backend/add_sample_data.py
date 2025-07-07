#!/usr/bin/env python3
"""
Firebase'e örnek notlar ve toplantılar eklemek için script
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Current directory'yi path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.firebase_service import FirebaseService

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_notes():
    """Örnek notlar ekle"""
    firebase_service = FirebaseService()
    
    if not firebase_service.is_available():
        logger.error("Firebase kullanılamıyor! Lütfen Firebase ayarlarını kontrol edin.")
        return False
    
    sample_notes = [
        {
            "title": "Bitirme Projesi",
            "content": "AI asistan uygulaması geliştiriliyor. React Native + Python backend kullanılıyor.",
            "user_id": "default"
        },
        {
            "title": "Market Listesi",
            "content": "Süt, ekmek, peynir, domates, yumurta, makarna, salatalık",
            "user_id": "default"
        },
        {
            "title": "Toplantı Notları",
            "content": "Proje ilerlemesi: %85 tamamlandı. Kalan işler: UI düzenlemeleri, test edilmesi",
            "user_id": "default"
        },
        {
            "title": "Günlük Hedefler",
            "content": "1. Kod review yap\n2. Hata düzeltmeleri\n3. Dokümantasyon güncelle\n4. Test senaryoları hazırla",
            "user_id": "default"
        },
        {
            "title": "Kitap Önerileri",
            "content": "Clean Code - Robert Martin\nDesign Patterns - Gang of Four\nRefactoring - Martin Fowler",
            "user_id": "default"
        },
        {
            "title": "Fitness Planı",
            "content": "Pazartesi: Göğüs\nSalı: Sırt\nÇarşamba: Dinlenme\nPerşembe: Bacak\nCuma: Omuz ve kol",
            "user_id": "default"
        },
        {
            "title": "Önemli Linkler",
            "content": "GitHub repo: https://github.com/...\nFirebase console: https://console.firebase.google.com/\nAPI docs: https://docs.api.com/",
            "user_id": "default"
        }
    ]
    
    logger.info("Örnek notlar ekleniyor...")
    
    for note in sample_notes:
        note_id = firebase_service.create_note(
            title=note["title"],
            content=note["content"],
            user_id=note["user_id"]
        )
        
        if note_id:
            logger.info(f"✓ Not eklendi: {note['title']} (ID: {note_id})")
        else:
            logger.error(f"✗ Not eklenemedi: {note['title']}")
    
    return True

def add_sample_events():
    """Örnek toplantılar ekle"""
    firebase_service = FirebaseService()
    
    if not firebase_service.is_available():
        logger.error("Firebase kullanılamıyor! Lütfen Firebase ayarlarını kontrol edin.")
        return False
    
    today = datetime.now()
    
    sample_events = [
        {
            "title": "Bitirme Projesi Sunumu",
            "datetime": (today + timedelta(days=3)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat(),
            "description": "Final sunumu için hazırlık. Sunum 30 dakika sürecek.",
            "user_id": "default"
        },
        {
            "title": "Takım Toplantısı",
            "datetime": (today + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
            "description": "Haftalık takım toplantısı. Proje ilerlemesi değerlendirilecek.",
            "user_id": "default"
        },
        {
            "title": "Doktor Randevusu",
            "datetime": (today + timedelta(days=5)).replace(hour=15, minute=30, second=0, microsecond=0).isoformat(),
            "description": "Genel sağlık kontrolü. Dr. Ahmet Yılmaz ile.",
            "user_id": "default"
        },
        {
            "title": "Kod Review",
            "datetime": (today + timedelta(days=2)).replace(hour=16, minute=0, second=0, microsecond=0).isoformat(),
            "description": "Backend kodlarının incelenmesi. Erencan ve Selin katılacak.",
            "user_id": "default"
        },
        {
            "title": "Öğle Yemeği",
            "datetime": (today + timedelta(days=4)).replace(hour=12, minute=30, second=0, microsecond=0).isoformat(),
            "description": "Arkadaşlarla öğle yemeği. Restoran: Sultanahmet Köftecisi",
            "user_id": "default"
        },
        {
            "title": "Spor Antrenmanı",
            "datetime": (today + timedelta(days=6)).replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
            "description": "Haftalık fitness antrenmanı. Bacak günü.",
            "user_id": "default"
        },
        {
            "title": "Proje Teslimi",
            "datetime": (today + timedelta(days=7)).replace(hour=17, minute=0, second=0, microsecond=0).isoformat(),
            "description": "Bitirme projesi final teslimi. Tüm belgeler hazır olmalı.",
            "user_id": "default"
        }
    ]
    
    logger.info("Örnek toplantılar ekleniyor...")
    
    for event in sample_events:
        event_id = firebase_service.create_event(
            title=event["title"],
            datetime_str=event["datetime"],
            description=event["description"],
            user_id=event["user_id"]
        )
        
        if event_id:
            logger.info(f"✓ Etkinlik eklendi: {event['title']} (ID: {event_id})")
        else:
            logger.error(f"✗ Etkinlik eklenemedi: {event['title']}")
    
    return True

def main():
    """Ana fonksiyon"""
    logger.info("Firebase örnek veri ekleme başlatılıyor...")
    
    # Örnek notlar ekle
    notes_success = add_sample_notes()
    
    # Örnek toplantılar ekle
    events_success = add_sample_events()
    
    if notes_success and events_success:
        logger.info("✓ Tüm örnek veriler başarıyla eklendi!")
    else:
        logger.error("✗ Bazı veriler eklenemedi.")
    
    return notes_success and events_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
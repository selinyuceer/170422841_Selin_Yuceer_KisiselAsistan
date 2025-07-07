import google.generativeai as genai
import os
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Gemini AI servisini başlat"""
        self.api_key = "AIzaSyDO8rY2ZBQrntwkxWH2ZmPucr1IM8dvyT4"  # Çalışan API anahtarı
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Gemini'yi yapılandır
        genai.configure(api_key=self.api_key)
        
        # Model yapılandırması - daha hızlı ayarlar
        self.generation_config = {
            "temperature": 0.1,  # Daha tutarlı sonuçlar için çok düşük
            "top_p": 0.8,
            "top_k": 20,
            "max_output_tokens": 512,
        }
        
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Model oluştur
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
    def _smart_entity_extraction(self, user_message: str, intent: str) -> Dict[str, Any]:
        """Akıllı entity extraction"""
        entities = {}
        message_lower = user_message.lower()
        
        if intent == "note":
            # Not için akıllı parsing
            
            # "başlık: X" ve/veya "açıklama: Y" formatını kontrol et
            baslik_match = re.search(r'başlık:\s*([^\n\r]+?)(?:\n|$)', user_message, re.IGNORECASE)
            
            if baslik_match:
                title = baslik_match.group(1).strip().title()
                entities["title"] = title
                
                # Açıklama arayışı - etiketli veya etiketli olmayan
                aciklama_match = re.search(r'(?:açıklama|detay|içerik):\s*([^\n\r]+.*?)$', user_message, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                
                if aciklama_match:
                    # Etiketli açıklama bulundu
                    content = aciklama_match.group(1).strip()
                    entities["content"] = content
                else:
                    # Etiketli açıklama yoksa, başlık satırından sonraki her şeyi içerik yap
                    lines = user_message.split('\n')
                    baslik_line_found = False
                    content_lines = []
                    
                    for line in lines:
                        if 'başlık:' in line.lower():
                            baslik_line_found = True
                            continue
                        elif baslik_line_found and line.strip():
                            content_lines.append(line.strip())
                    
                    if content_lines:
                        content = ' '.join(content_lines)
                        entities["content"] = content
                    else:
                        entities["content"] = title
            elif ":" in user_message and not baslik_match:
                # Basit iki nokta üst üste formatı
                parts = user_message.split(":", 1)
                if len(parts) == 2:
                    # "not oluştur: X" formatı
                    content = parts[1].strip()
                    # Başlık olarak ilk satırı al
                    lines = content.split('\n')
                    title = lines[0].strip().title() if lines else content.title()
                    entities["title"] = title
                    entities["content"] = content
            else:
                # Sesli komut formatı: "not oluştur başlık X açıklama Y"
                baslik_aciklama_match = re.search(r'başlık\s+([^,]+?)(?:\s+açıklama\s+(.+))?$', user_message, re.IGNORECASE)
                if baslik_aciklama_match:
                    title = baslik_aciklama_match.group(1).strip().title()
                    content = baslik_aciklama_match.group(2).strip() if baslik_aciklama_match.group(2) else title
                    entities["title"] = title
                    entities["content"] = content
                else:
                    # Türkçe ses komutu formatı: "not oluştur ismi X içerik Y"
                    ismi_icerik_match = re.search(r'ismi\s+([^,]+?)(?:\s+içerik\s+(.+))?$', user_message, re.IGNORECASE)
                    if ismi_icerik_match:
                        title = ismi_icerik_match.group(1).strip().title()
                        content = ismi_icerik_match.group(2).strip() if ismi_icerik_match.group(2) else title
                        entities["title"] = title
                        entities["content"] = content
                    else:
                        # "başlığı X olsun yapılacaklar Y" formatı
                        baslik_olsun_match = re.search(r'başlığ?[ıi]?\s+([^,]+?)\s+olsun\s+yapılacaklar\s+(.+)$', user_message, re.IGNORECASE)
                        if baslik_olsun_match:
                            title = baslik_olsun_match.group(1).strip().title()
                            content = baslik_olsun_match.group(2).strip()
                            entities["title"] = title
                            entities["content"] = content
                        else:
                            # Başlık içerik ayrımı: "not al başlık X içerik Y" or "not al başlığı X içerik Y"
                            baslik_icerik_match = re.search(r'başlığ?[ıi]?\s+([^,]+?)(?:\s+içerik\s+(.+))?$', user_message, re.IGNORECASE)
                            if baslik_icerik_match:
                                title = baslik_icerik_match.group(1).strip().title()
                                content = baslik_icerik_match.group(2).strip() if baslik_icerik_match.group(2) else title
                                entities["title"] = title
                                entities["content"] = content
                            else:
                                # Anahtar kelimeleri temizle
                                patterns = ["not al", "not oluştur", "not ekle", "not yaz", "not et", "kaydet", "not olarak", "bunu not"]
                                clean_message = user_message
                                for pattern in patterns:
                                    clean_message = re.sub(pattern, "", clean_message, flags=re.IGNORECASE).strip()
                                
                                if clean_message:
                                    entities["title"] = clean_message
                                    entities["content"] = clean_message
                                else:
                                    entities["title"] = "Yeni Not"
                                    entities["content"] = user_message
        
        elif intent == "calendar":
            # Tarih/saat parsing
            entities["datetime"] = self._parse_datetime(user_message)
            
            # Akıllı başlık çıkarma
            entities["title"] = self._extract_meeting_title(user_message)
            
            # Açıklama çıkarma
            entities["description"] = self._extract_description(user_message)
        
        return entities
    
    def _parse_datetime(self, message: str) -> str:
        """Akıllı tarih/saat parsing"""
        message_lower = message.lower()
        now = datetime.now()
        
        # Türkçe ay isimleri
        turkish_months = {
            'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
            'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
        }
        
        # Önce spesifik tarih formatlarını kontrol et
        # "15 Temmuz", "21 Haziran" gibi formatlar
        for month_name, month_num in turkish_months.items():
            # "15 temmuz" formatı
            pattern = rf'\b(\d{{1,2}})\s+{month_name}\b'
            match = re.search(pattern, message_lower)
            if match:
                day = int(match.group(1))
                year = now.year
                
                # Geçmiş tarih ise bir sonraki yıl
                try:
                    test_date = datetime(year, month_num, day)
                    if test_date < now.replace(hour=0, minute=0, second=0, microsecond=0):
                        year += 1
                except ValueError:
                    # Geçersiz tarih
                    continue
                
                # Saat parsing
                hour, minute = self._parse_time(message)
                
                try:
                    target_datetime = datetime(year, month_num, day, hour, minute)
                    logger.info(f"Turkish date parsed: {day} {month_name} {year} {hour}:{minute:02d} → {target_datetime.isoformat()}")
                    return target_datetime.isoformat()
                except ValueError:
                    logger.warning(f"Invalid Turkish date: {day} {month_name} {year}")
                    continue
        
        # DD/MM/YYYY veya DD.MM.YYYY formatı
        date_patterns = [
            r'\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b',  # 15/07/2025, 15.07.2025
            r'\b(\d{1,2})/(\d{1,2})\b',  # 15/07
            r'\b(\d{1,2})\.(\d{1,2})\b'  # 15.07
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                day, month = int(match.group(1)), int(match.group(2))
                year = int(match.group(3)) if len(match.groups()) == 3 else now.year
                
                # 2 haneli yılı 4 haneye çevir
                if year < 100:
                    year += 2000
                
                # Geçmiş tarih ise bir sonraki yıl
                try:
                    test_date = datetime(year, month, day)
                    if test_date < now.replace(hour=0, minute=0, second=0, microsecond=0):
                        year += 1
                except ValueError:
                    continue
                
                # Saat parsing
                hour, minute = self._parse_time(message)
                
                try:
                    target_datetime = datetime(year, month, day, hour, minute)
                    logger.info(f"Numeric date parsed: {day}/{month}/{year} {hour}:{minute:02d} → {target_datetime.isoformat()}")
                    return target_datetime.isoformat()
                except ValueError:
                    logger.warning(f"Invalid numeric date: {day}/{month}/{year}")
                    continue
        
        # Yarın kontrolü
        if "yarın" in message_lower:
            base_date = now + timedelta(days=1)
        elif "bugün" in message_lower:
            base_date = now
        else:
            # Varsayılan: yarın
            base_date = now + timedelta(days=1)
        
        # Saat parsing
        hour, minute = self._parse_time(message)
        
        # Sonucu oluştur
        target_datetime = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        logger.info(f"Default date used: {target_datetime.isoformat()}")
        return target_datetime.isoformat()
    
    def _parse_time(self, message: str) -> tuple:
        """Saat parsing - (hour, minute) döndürür"""
        message_lower = message.lower()
        
        # "X:XX" formatı
        time_match = re.search(r'(\d{1,2}):(\d{2})', message)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            return (hour, minute)
        
        # "X.XX" formatı (16.00, 10.30 gibi)
        time_dot_match = re.search(r'(\d{1,2})\.(\d{2})', message)
        if time_dot_match:
            hour = int(time_dot_match.group(1))
            minute = int(time_dot_match.group(2))
            return (hour, minute)
        
        # "saat X" formatı
        saat_match = re.search(r'saat\s+(\d{1,2})', message_lower)
        if saat_match:
            hour = int(saat_match.group(1))
            return (hour, 0)
        
        # "Xa" formatı (10a = 10:00)
        a_match = re.search(r'(\d{1,2})a\b', message_lower)
        if a_match:
            hour = int(a_match.group(1))
            return (hour, 0)
        
        # "X'da" formatı (10'da = 10:00)
        da_match = re.search(r"(\d{1,2})'da", message_lower)
        if da_match:
            hour = int(da_match.group(1))
            return (hour, 0)
        
        # Varsayılan: 10:00
        return (10, 0)
    
    def _extract_meeting_title(self, message: str) -> str:
        """Toplantı başlığını akıllı şekilde çıkar"""
        message_lower = message.lower()
        
        # Öncelikle "başlık: X" formatını kontrol et (açıklama, detay vb. kelimelerde dur)
        baslik_colon_match = re.search(r'başlık:\s*([^,\n\r]+?)(?:\s+(?:açıklama|detay|not|hakkında|içerik|oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if baslik_colon_match:
            title = baslik_colon_match.group(1).strip()
            # Temizle ve düzelt
            title = self._clean_title(title)
            if title and title != "Yeni Toplantı":
                return title
        
        # SESLİ KOMUT PATTERNLERİ - En öncelikli
        # "başlığının ismi X olsun" formatını kontrol et
        basliginismi_match = re.search(r'başlığının\s+ismi\s+([a-zA-ZçÇğĞıİöÖşŞüÜ\s\']+?)\s+olsun', message_lower)
        if basliginismi_match:
            title = basliginismi_match.group(1).strip()
            # Saf metni al ve temizle
            words = title.split()
            clean_words = []
            for word in words:
                # Türkçe karakterler ve apostrof içeren kelimeleri kabul et
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ\']+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e', 'oluştur', 'toplantı', 'etkinlik']):
                    clean_words.append(word)
            
            if clean_words:
                result = ' '.join(clean_words)
                return self._format_title_with_apostrophes(result)
        
        # "başlığı X olsun" formatını kontrol et
        basligiolsun_match = re.search(r'başlığı\s+([a-zA-ZçÇğĞıİöÖşŞüÜ\s\']+?)\s+olsun', message_lower)
        if basligiolsun_match:
            title = basligiolsun_match.group(1).strip()
            words = title.split()
            clean_words = []
            for word in words:
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ\']+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e', 'oluştur', 'toplantı', 'etkinlik']):
                    clean_words.append(word)
            
            if clean_words:
                result = ' '.join(clean_words)
                return self._format_title_with_apostrophes(result)
        
        # "ismi X olsun" formatını kontrol et
        ismi_olsun_match = re.search(r'ismi\s+([a-zA-ZçÇğĞıİöÖşŞüÜ\s\']+?)\s+olsun', message_lower)
        if ismi_olsun_match:
            title = ismi_olsun_match.group(1).strip()
            words = title.split()
            clean_words = []
            for word in words:
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ\']+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e', 'oluştur', 'toplantı', 'etkinlik']):
                    clean_words.append(word)
            
            if clean_words:
                result = ' '.join(clean_words)
                return self._format_title_with_apostrophes(result)
        
        # "konusu X olsun" formatını kontrol et
        konusu_match = re.search(r'konusu\s+([a-zA-ZçÇğĞıİöÖşŞüÜ\s]+?)\s+olsun', message_lower)
        if konusu_match:
            title = konusu_match.group(1).strip()
            # Sadece saf metni al
            words = title.split()
            clean_words = []
            for word in words:
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ]+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e', 'oluştur', 'toplantı', 'konusu']):
                    clean_words.append(word)
            
            if clean_words:
                return ' '.join(clean_words).title()
        
        # "X toplantısı olsun" formatını kontrol et
        toplantisi_olsun_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*)\s+toplantısı\s+olsun', message_lower)
        if toplantisi_olsun_match:
            title = toplantisi_olsun_match.group(1).strip()
            # Sadece saf metni al (sayı ve özel karakterleri çıkar)
            words = title.split()
            clean_words = []
            for word in words:
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ]+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e', 'oluştur', 'toplantı']):
                    clean_words.append(word)
            
            if clean_words:
                return ' '.join(clean_words).title()
        
        # "X başlıklı toplantı" formatını kontrol et - ters yaklaşım
        baslikli_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+){0,3})\s+başlıklı\s+(?:toplantı|etkinlik)', message_lower)
        if baslikli_match:
            title = baslikli_match.group(1).strip()
            # Sadece saf metni al (sayı ve özel karakterleri çıkar)
            words = title.split()
            clean_words = []
            for word in words:
                if (re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ]+$', word) and 
                    len(word) > 1 and
                    word not in ['saat', 'sabah', 'akşam', 'öğlen', 'da', 'de', 'a', 'e']):
                    clean_words.append(word)
            
            if clean_words:
                return ' '.join(clean_words).title()
        
        # "X toplantısı" formatını kontrol et 
        toplantisi_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*)\s+toplantısı(?:\s|$)', message_lower)
        if toplantisi_match:
            title = toplantisi_match.group(1).strip()
            return self._clean_title(title)
        
        # "toplantı oluştur X" formatını kontrol et
        olustur_match = re.search(r'toplantı\s+oluştur\s+([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*?)(?:\s+(?:yarın|bugün|saat|\d|olsun|başlık)|$)', message_lower)
        if olustur_match:
            title = olustur_match.group(1).strip()
            return self._clean_title(title)
        
        # "etkinlik oluştur X" formatını kontrol et
        etkinlik_match = re.search(r'etkinlik\s+oluştur\s+([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*?)(?:\s+(?:yarın|bugün|saat|\d|olsun|başlık)|$)', message_lower)
        if etkinlik_match:
            title = etkinlik_match.group(1).strip()
            return self._clean_title(title)
        
        # "X için toplantı" formatını kontrol et
        icin_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*)\s+için\s+(?:toplantı|etkinlik)', message_lower)
        if icin_match:
            title = icin_match.group(1).strip()
            return self._clean_title(title)
        
        # "X adlı toplantı" formatını kontrol et
        adli_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*)\s+adlı\s+(?:toplantı|etkinlik)', message_lower)
        if adli_match:
            title = adli_match.group(1).strip()
            return self._clean_title(title)
        
        # "X isimli toplantı" formatını kontrol et
        isimli_match = re.search(r'([a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:\s+[a-zA-ZçÇğĞıİöÖşŞüÜ]+)*)\s+isimli\s+(?:toplantı|etkinlik)', message_lower)
        if isimli_match:
            title = isimli_match.group(1).strip()
            return self._clean_title(title)
        
        # Hiçbir pattern bulamazsa mesajın ilk birkaç kelimesini al
        words = message.split()
        # Zaman ifadelerini ve gereksiz kelimeleri filtrele
        filtered_words = []
        skip_words = {
            'yarın', 'bugün', 'saat', 'saatte', 'da', 'de', 'oluştur', 'koy', 'yap', 
            'toplantı', 'etkinlik', 'randevu', 'a', 'e', 'için', 'ile', 'olsun', 'ismi',
            'temmuz', 'haziran', 'ocak', 'şubat', 'mart', 'nisan', 'mayıs', 
            'ağustos', 'eylül', 'ekim', 'kasım', 'aralık', 'sabah', 'akşam', 'öğlen',
            'sabahı', 'akşamı', 'öğleni', 'başlık', 'için', 'başlığının', 'başlığı'
        }
        
        for word in words:
            clean_word = word.strip('.,!?:;\'\"').lower()
            # Sayı değilse ve skip listesinde değilse ve 2 karakterden uzunsa
            if (not clean_word.isdigit() and 
                clean_word not in skip_words and 
                len(clean_word) > 2 and
                not re.match(r'\d+[:\.]?\d*[a-z]*', clean_word)):  # 10:00, 10a gibi formatları filtrele
                filtered_words.append(word.strip('.,!?:;\'\"'))
                
                # En fazla 3 kelime al
                if len(filtered_words) >= 3:
                    break
        
        if filtered_words:
            title = ' '.join(filtered_words)
            return self._clean_title(title)
        
        # Hiçbir şey bulamazsa varsayılan
        return "Yeni Toplantı"
    
    def _extract_description(self, message: str) -> str:
        """Açıklama/detayı akıllı şekilde çıkar"""
        message_lower = message.lower()
        
        # "açıklama: X" veya "açıklama X" formatını kontrol et
        aciklama_match = re.search(r'açıklama[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if aciklama_match:
            description = aciklama_match.group(1).strip()
            # Gereksiz kelimeleri temizle
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # "detay: X" veya "detay X" formatını kontrol et
        detay_match = re.search(r'detay[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if detay_match:
            description = detay_match.group(1).strip()
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # "not: X" veya "not X" formatını kontrol et (takvim açıklamasında)
        not_match = re.search(r'not[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if not_match:
            description = not_match.group(1).strip()
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # "hakkında: X" veya "hakkında X" formatını kontrol et
        hakkinda_match = re.search(r'hakkında[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if hakkinda_match:
            description = hakkinda_match.group(1).strip()
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # "içerik: X" veya "içerik X" formatını kontrol et
        icerik_match = re.search(r'içerik[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if icerik_match:
            description = icerik_match.group(1).strip()
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # "konusu X" formatını kontrol et (sadece açıklama kısmı için)
        konusu_desc_match = re.search(r'konusu\s+(.+?)\s+(?:açıklama|detay|not|hakkında)[:,]?\s*([^\n\r]+?)(?:\s+(?:oluştur|yap|koy|kaydet|ekle)|$)', message, re.IGNORECASE)
        if konusu_desc_match:
            description = konusu_desc_match.group(2).strip()
            description = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
            if description and len(description) > 2:
                return description
        
        # Varsayılan: boş açıklama
        return ""
    
    def _format_title_with_apostrophes(self, title: str) -> str:
        """Apostrof içeren başlıkları düzgün formatla"""
        words = title.split()
        title_words = []
        for word in words:
            if word:
                if "'" in word:  # Apostrof içeren kelimeler için özel işlem
                    # "eren'in" -> "Eren'in", "can'ın" -> "Can'ın"
                    if word.count("'") == 1:  # Tek apostrof durumu
                        parts = word.split("'")
                        if len(parts) == 2 and parts[0] and parts[1]:
                            # İlk kısmı büyük harfle başlat, ikinci kısmı küçük bırak  
                            formatted_word = parts[0].capitalize() + "'" + parts[1].lower()
                            title_words.append(formatted_word)
                        else:
                            title_words.append(word.capitalize())
                    else:
                        # Çoklu apostrof durumu - sadece ilk harfi büyük yap
                        title_words.append(word.capitalize())
                else:
                    title_words.append(word.capitalize())
        
        return ' '.join(title_words)
    
    def _clean_title(self, title: str) -> str:
        """Başlığı temizle ve düzelt"""
        # Küçük harflerden başlıyorsa büyük harfle başlat
        title = title.strip()
        if title:
            # Türkçe karakter desteği ile her kelimenin ilk harfini büyük yap
            words = title.split()
            title_case_words = []
            for word in words:
                if word:
                    title_case_words.append(word[0].upper() + word[1:].lower())
            title = ' '.join(title_case_words)
        
        # Gereksiz kelimeleri temizle
        title = re.sub(r'\b(toplantı|etkinlik|oluştur|koy|yap|başlıklı|için|ile|olsun|başlık)\b', '', title, flags=re.IGNORECASE)
        
        # Tarih ve saat ifadelerini temizle
        title = re.sub(r'\b\d{1,2}[:\.]?\d{0,2}[a-z]*\b', '', title)  # 10:00, 10a
        # Sadece tek başına kullanılan zaman ifadelerini temizle (yemek isimleri için değil)
        title = re.sub(r'\b(yarın|bugün)\b', '', title, flags=re.IGNORECASE)
        # "sabah/akşam/öğlen saat", "sabah/akşam/öğlen yarın" gibi kombinasyonları temizle 
        title = re.sub(r'\b(sabah|akşam|öğlen)\s+(saat|yarın|bugün|\d)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\b\d{1,2}\s+(temmuz|haziran|ocak|şubat|mart|nisan|mayıs|ağustos|eylül|ekim|kasım|aralık)\b', '', title, flags=re.IGNORECASE)
        
        # Birden fazla boşluğu tek boşlukla değiştir
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Boşsa varsayılan değer
        if not title or len(title) < 2:
            return "Yeni Toplantı"
        
        return title
    
    def _simple_intent_analysis(self, user_message: str) -> Dict[str, Any]:
        """Basit kural-tabanlı intent analizi"""
        message_lower = user_message.lower()
        
        # Önce soru kalıplarını kontrol et
        question_patterns = [
            "var mı", "var mi", "ne zaman", "hangi gün", "kaçta", 
            "ne var", "toplantım var", "etkinlik var", "randevum var",
            "bugün ne", "yarın ne", "ne yapacağım", "programım ne"
        ]
        
        # Soru kalıpları varsa chat intent olarak bırak
        for pattern in question_patterns:
            if pattern in message_lower:
                return {
                    "intent": "chat",
                    "confidence": 0.9,
                    "entities": {}
                }
        
        # Basit şablonlar
        simple_templates = {
            "note_patterns": [
                "not al", "not oluştur", "not ekle", "not yaz", "not et", 
                "kaydet", "not olarak", "bunu not"
            ],
            "calendar_patterns": [
                "toplantı oluştur", "etkinlik oluştur", "randevu kur", "takvim ekle",
                "toplantı yap", "etkinlik yap", "randevu ayarla"
            ],
            "weather_patterns": [
                "hava", "hava durumu", "weather", "sıcaklık", "yağmur"
            ]
        }
        
        # Intent belirleme
        intent = "chat"  # varsayılan
        
        for pattern in simple_templates["note_patterns"]:
            if pattern in message_lower:
                intent = "note"
                break
        
        if intent == "chat":
            for pattern in simple_templates["calendar_patterns"]:
                if pattern in message_lower:
                    intent = "calendar"
                    break
        
        if intent == "chat":
            for pattern in simple_templates["weather_patterns"]:
                if pattern in message_lower:
                    intent = "weather"
                    break
        
        # Akıllı entity extraction
        entities = self._smart_entity_extraction(user_message, intent)
        
        return {
            "intent": intent,
            "confidence": 0.9,
            "entities": entities
        }

    async def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """Intent analizi - hızlı kural-tabanlı + AI fallback"""
        try:
            # Önce basit kural-tabanlı analiz
            simple_result = self._simple_intent_analysis(user_message)
            
            # Eğer kural-tabanlı analiz yeterli güvende değilse AI'ya sor
            if simple_result["confidence"] < 0.8:
                try:
                    ai_result = await self._ai_intent_analysis(user_message)
                    return ai_result
                except Exception as e:
                    # AI analizi başarısız olursa basit analizle devam et
                    logger.warning(f"AI intent analysis failed, using rule-based: {e}")
                    return simple_result
            
            return simple_result
            
        except Exception as e:
            logger.error(f"Intent analysis error: {e}")
            # Tüm analizler başarısız olursa güvenli varsayılan döndür
            return {
                "intent": "chat",
                "confidence": 0.5,
                "entities": {}
            }
    
    async def _ai_intent_analysis(self, user_message: str) -> Dict[str, Any]:
        """AI tabanlı intent analizi"""
        try:
            prompt = f"""
            Kullanıcı mesajını analiz et ve intent belirle:
            
            Mesaj: "{user_message}"
            
            Mümkün intentler:
            - note: Not alma (not al, not oluştur, kaydet)
            - calendar: Takvim etkinliği (toplantı, etkinlik, randevu)
            - weather: Hava durumu (hava, weather, sıcaklık)
            - reminder: Hatırlatma (hatırlat, alarm)
            - chat: Genel sohbet
            
            JSON formatında yanıt ver:
            {{
                "intent": "intent_name",
                "confidence": 0.9,
                "entities": {{}}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # JSON parse et
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # JSON parse edilemezse basit analiz kullan
                return self._simple_intent_analysis(user_message)
                
        except Exception as e:
            logger.error(f"AI intent analysis error: {e}")
            # Hata durumunda basit analiz kullan
            return self._simple_intent_analysis(user_message)
    
    async def generate_response(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Kullanıcı mesajına yanıt oluştur"""
        try:
            # Context'ten intent bilgisini al
            if context and "intent" in context:
                intent = context["intent"]
                if intent == "note":
                    return "✅ Notunuz başarıyla kaydedildi!"
                elif intent == "calendar":
                    return "📅 Takvim etkinliğiniz oluşturuldu!"
                elif intent == "weather":
                    return "🌤️ Hava durumu bilgisi alınıyor..."
                elif intent == "reminder":
                    return "⏰ Hatırlatıcınız ayarlandı!"
            
            # Genel yanıt oluştur
            try:
                response = self.model.generate_content(f"Kullanıcı mesajına kısa ve yardımcı bir yanıt ver: {user_message}")
                return response.text
            except Exception as e:
                logger.error(f"Response generation error: {e}")
                # Gemini API hatası durumunda basit yanıt ver
                return self._generate_fallback_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._generate_fallback_response(user_message, context)
    
    def _generate_fallback_response(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """API hatası durumunda basit yanıt oluştur"""
        message_lower = user_message.lower()
        
        # Context'ten intent bilgisini al
        if context and "intent" in context:
            intent = context["intent"]
            if intent == "note":
                return "✅ Notunuz başarıyla kaydedildi!"
            elif intent == "calendar":
                return "📅 Takvim etkinliğiniz oluşturuldu!"
            elif intent == "weather":
                return "🌤️ Hava durumu bilgisi alınıyor..."
            elif intent == "reminder":
                return "⏰ Hatırlatıcınız ayarlandı!"
        
        # Anahtar kelimeler ile basit yanıt
        if any(word in message_lower for word in ["teşekkür", "sağol", "thanks"]):
            return "Rica ederim! Size yardımcı olabildiğim için mutluyum."
        elif any(word in message_lower for word in ["merhaba", "selam", "hello"]):
            return "Merhaba! Size nasıl yardımcı olabilirim?"
        elif any(word in message_lower for word in ["var mı", "ne zaman", "hangi gün"]):
            return "Takvim bilgilerinizi kontrol ediyorum..."
        else:
            return "Anladım. Size nasıl yardımcı olabilirim?"
    
    async def generate_smart_response(self, user_message: str, intent_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Akıllı yanıt oluşturma"""
        try:
            intent = intent_data.get("intent", "chat")
            
            # Intent'e göre özel yanıtlar
            if intent == "note":
                return "✅ Notunuz başarıyla kaydedildi!"
            elif intent == "calendar":
                return "📅 Takvim etkinliğiniz oluşturuldu!"
            elif intent == "weather":
                # Context'teki weather data'yı kontrol et
                if context and "weather" in context:
                    weather_data = context["weather"]
                    city = weather_data.get('city', 'İstanbul')
                    temp = weather_data.get('temperature', 'N/A')
                    condition = weather_data.get('condition', 'Bilinmiyor')
                    humidity = weather_data.get('humidity', 'N/A')
                    feels_like = weather_data.get('feels_like', 'N/A')
                    wind_speed = weather_data.get('wind_speed', 'N/A')
                    
                    return f"🌤️ **{city} Hava Durumu:**\n🌡️ Sıcaklık: {temp}°C (Hissedilen: {feels_like}°C)\n☁️ Durum: {condition}\n💧 Nem: %{humidity}\n🌬️ Rüzgar: {wind_speed} m/s"
                else:
                    return "🌤️ Hava durumu bilgisi alınamadı. Lütfen tekrar deneyin."
            elif intent == "reminder":
                return "⏰ Hatırlatıcınız ayarlandı!"
            elif intent == "chat":
                # Chat intent'i için context'e göre özel yanıtlar
                if context and "calendar" in context:
                    calendar_data = context["calendar"]
                    events = calendar_data.get("events", [])
                    
                    if events:
                        event_list = []
                        for event in events:
                            title = event.get("title", "Başlıksız etkinlik")
                            datetime_str = event.get("datetime", "")
                            
                            if datetime_str:
                                try:
                                    # ISO format'ını parse et
                                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                                    time_str = dt.strftime('%H:%M')
                                    date_str = dt.strftime('%d.%m.%Y')
                                except:
                                    time_str = "Saat belirsiz"
                                    date_str = "Tarih belirsiz"
                            else:
                                time_str = "Saat belirsiz"
                                date_str = "Tarih belirsiz"
                            
                            event_list.append(f"• {title} - {time_str}")
                        
                        events_text = "\n".join(event_list)
                        
                        # Tarih bilgisini de ekle
                        if "13 temmuz" in user_message.lower():
                            date_info = "13 Temmuz'da"
                        elif "bugün" in user_message.lower():
                            date_info = "Bugün"
                        elif "yarın" in user_message.lower():
                            date_info = "Yarın"
                        else:
                            date_info = "Belirtilen tarihte"
                        
                        return f"📅 {date_info} {len(events)} etkinliğiniz var:\n\n{events_text}"
                    else:
                        # Tarih bilgisini kontrol et
                        if "13 temmuz" in user_message.lower():
                            return "📅 13 Temmuz'da herhangi bir etkinliğiniz bulunmuyor."
                        elif "bugün" in user_message.lower():
                            return "📅 Bugün herhangi bir etkinliğiniz bulunmuyor."
                        elif "yarın" in user_message.lower():
                            return "📅 Yarın herhangi bir etkinliğiniz bulunmuyor."
                        else:
                            return "📅 Belirtilen tarihte herhangi bir etkinliğiniz bulunmuyor."
                
                elif context and "weather" in context:
                    weather_data = context["weather"]
                    city = weather_data.get('city', 'İstanbul')
                    temp = weather_data.get('temperature', 'N/A')
                    condition = weather_data.get('condition', 'Bilinmiyor')
                    humidity = weather_data.get('humidity', 'N/A')
                    feels_like = weather_data.get('feels_like', 'N/A')
                    wind_speed = weather_data.get('wind_speed', 'N/A')
                    
                    return f"🌤️ **{city} Hava Durumu:**\n🌡️ Sıcaklık: {temp}°C (Hissedilen: {feels_like}°C)\n☁️ Durum: {condition}\n💧 Nem: %{humidity}\n🌬️ Rüzgar: {wind_speed} m/s"
            
            # Genel sohbet için AI yanıt
            try:
                response = self.model.generate_content(f"Bu mesaja kısa ve yardımcı bir yanıt ver: {user_message}")
                return response.text
            except Exception as e:
                logger.error(f"Smart response generation error: {e}")
                return self._generate_fallback_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Smart response generation error: {e}")
            return self._generate_fallback_response(user_message, context)

def get_gemini_service():
    """Gemini servisini al"""
    return GeminiService() 
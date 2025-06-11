import google.generativeai as genai
import os
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Gemini AI servisini başlat"""
        self.api_key = "AIzaSyDO8rY2ZBQrntwkxWH2ZmPucr1IM8dvyT4"  # Çalışan API anahtarı
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Gemini'yi yapılandır
        genai.configure(api_key=self.api_key)
        
        # Model yapılandırması
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
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
        
        # Sistem promptu
        self.system_prompt = """
        Sen Türkçe konuşan, yardımsever bir kişisel asistansın. Adın "Asistan".
        
        Görevlerin:
        1. Kullanıcıların sorularını Türkçe olarak yanıtlamak
        2. Günlük görevlerde yardım etmek
        3. Not alma, hatırlatıcı kurma, takvim etkinlikleri konularında rehberlik etmek
        4. Hava durumu bilgisi sağlamak
        5. Genel bilgi ve sohbet desteği sunmak
        
        Özellikler:
        - Her zaman kibar ve yardımsever ol
        - Türkçe dilbilgisi kurallarına uy
        - Kısa ve net yanıtlar ver
        - Eğer bir şeyi bilmiyorsan, bilmediğini söyle
        - Kullanıcının taleplerini anlamaya çalış ve uygun önerilerde bulun
        
        Önemli: Sadece güvenli ve yararlı bilgiler paylaş.
        """
    
    async def generate_response(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Kullanıcı mesajına Gemini ile yanıt üret
        
        Args:
            user_message: Kullanıcı mesajı
            context: Ek bağlam bilgileri
            
        Returns:
            AI yanıtı
        """
        try:
            # Bağlam bilgilerini ekle
            full_prompt = self.system_prompt + "\n\n"
            
            if context:
                full_prompt += f"Bağlam bilgileri: {context}\n\n"
            
            full_prompt += f"Kullanıcı: {user_message}\nAsistan:"
            
            # Gemini'den yanıt al
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return "Üzgünüm, şu anda yanıt üretemiyorum. Lütfen tekrar deneyin."
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
    
    async def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Kullanıcı mesajının amacını analiz et
        
        Args:
            user_message: Kullanıcı mesajı
            
        Returns:
            Intent analizi sonucu
        """
        try:
            intent_prompt = f"""
            Aşağıdaki kullanıcı mesajını analiz et ve amacını belirle:
            
            Mesaj: "{user_message}"
            
            Lütfen şu formatda JSON yanıtı ver:
            {{
                "intent": "chat|note|reminder|calendar|weather",
                "confidence": 0.0-1.0,
                "entities": {{
                    "title": "başlık varsa",
                    "datetime": "tarih/saat varsa",
                    "location": "konum varsa"
                }}
            }}
            
            Intent türleri:
            - chat: Genel sohbet
            - note: Not alma (örnekler: "not al", "kaydet", "not olarak kaydet", "bunu not et")
            - reminder: Hatırlatıcı kurma
            - calendar: Takvim etkinliği (örnekler: "etkinlik oluştur", "toplantı kur", "randevu al")
            - weather: Hava durumu
            
            Not alma örnekleri:
            - "Bunu not olarak kaydet"
            - "Not al: toplantı yarın"
            - "Kaydet: market listesi"
            - "Bunu not et"
            - "not olarak ekle"
            - "Test notu not olarak ekle"
            - "Market listesi not ekle"
            - "Toplantı notları not olarak ekle"
            
            Etkinlik oluşturma örnekleri:
            - "Yarın saat 10:00'da toplantı kur"
            - "Etkinlik oluştur: Proje sunumu 15/06/2025 14:00"
            - "Bugün 16:00'da randevu al"
            - "Toplantı: Müşteri görüşmesi yarın"
            """
            
            response = self.model.generate_content(intent_prompt)
            
            # JSON parse etmeye çalış
            import json
            try:
                result = json.loads(response.text)
                return result
            except:
                # JSON parse edilemezse varsayılan değer dön
                return {
                    "intent": "chat",
                    "confidence": 0.5,
                    "entities": {}
                }
                
        except Exception as e:
            logger.error(f"Intent analysis error: {str(e)}")
            return {
                "intent": "chat",
                "confidence": 0.0,
                "entities": {}
            }
    
    async def generate_smart_response(self, user_message: str, intent_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """
        Intent bilgisine göre akıllı yanıt üret
        
        Args:
            user_message: Kullanıcı mesajı
            intent_data: Intent analizi sonucu
            context: Ek bağlam bilgileri (takvim, hava durumu vb.)
            
        Returns:
            Akıllı yanıt
        """
        try:
            intent = intent_data.get("intent", "chat")
            entities = intent_data.get("entities", {})
            
            # Bağlam bilgilerini kontrol et
            if context:
                # Etkinlik oluşturma kontrolü (önce kontrol et)
                if "event_created" in context:
                    created_event = context["event_created"]
                    event_datetime = created_event.get('datetime', '')
                    if event_datetime:
                        try:
                            event_time = datetime.fromisoformat(event_datetime.replace('Z', '+00:00'))
                            formatted_time = event_time.strftime('%d.%m.%Y %H:%M')
                        except:
                            formatted_time = event_datetime
                    else:
                        formatted_time = "Belirtilmemiş"
                    
                    return f"📅 Etkinliğiniz başarıyla oluşturuldu!\n🎯 Başlık: {created_event.get('title', 'Başlıksız')}\n⏰ Tarih/Saat: {formatted_time}\n🆔 Etkinlik ID: {created_event.get('id', 'Bilinmiyor')}"
                
                # Not kaydetme kontrolü
                if "note_saved" in context:
                    saved_note = context["note_saved"]
                    return f"✅ Notunuz başarıyla kaydedildi!\n📝 Başlık: {saved_note.get('title', 'Başlıksız')}\n🆔 Not ID: {saved_note.get('id', 'Bilinmiyor')}"
                
                # Takvim sorguları (etkinlik oluşturma değil, mevcut etkinlikleri sorgulama)
                if "calendar" in context and ("toplantı var mı" in user_message.lower() or "etkinlik var mı" in user_message.lower() or ("yarın" in user_message.lower() and "var mı" in user_message.lower())):
                    calendar_data = context["calendar"]
                    events = calendar_data.get("events", [])
                    
                    if "yarın" in user_message.lower():
                        tomorrow_events = context.get("tomorrow_events", [])
                        if tomorrow_events:
                            event_list = []
                            for event in tomorrow_events:
                                event_time = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                                event_list.append(f"• {event['title']} - {event_time.strftime('%H:%M')}")
                            return f"Yarın şu etkinlikleriniz var:\n" + "\n".join(event_list)
                        else:
                            return "Yarın herhangi bir etkinliğiniz bulunmuyor."
                    
                    elif events:
                        event_list = []
                        for event in events[:5]:  # İlk 5 etkinliği göster
                            event_time = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                            event_list.append(f"• {event['title']} - {event_time.strftime('%d.%m.%Y %H:%M')}")
                        return f"Yaklaşan etkinlikleriniz:\n" + "\n".join(event_list)
                    else:
                        return "Şu anda herhangi bir etkinliğiniz bulunmuyor."
                
                # Hava durumu sorguları
                if "weather" in context and "hava" in user_message.lower():
                    weather_data = context["weather"]
                    city = weather_data.get("city", "")
                    temp = weather_data.get("temperature", "")
                    condition = weather_data.get("condition", "")
                    humidity = weather_data.get("humidity", "")
                    
                    return f"{city} için güncel hava durumu:\n🌡️ Sıcaklık: {temp}°C\n☁️ Durum: {condition}\n💧 Nem: {humidity}%"
            
            # Intent'e göre varsayılan yanıtlar
            if intent == "note":
                return "Not almak istediğinizi anlıyorum. Not başlığını ve içeriğini belirtir misiniz?"
            elif intent == "reminder":
                return "Hatırlatıcı kurmak istiyorsunuz. Hangi tarih ve saatte size hatırlatmamı istiyorsunuz?"
            elif intent == "calendar":
                return "Takvim etkinliği oluşturmak istiyorsunuz. Etkinlik başlığını, tarihini ve saatini belirtir misiniz? Örnek: 'Yarın saat 14:00'da toplantı kur'"
            elif intent == "weather":
                location = entities.get("location", "")
                if location:
                    return f"{location} için hava durumu bilgisini getiriyorum..."
                else:
                    return "Hangi şehir için hava durumu bilgisi istiyorsunuz?"
            else:
                # Genel chat yanıtı
                return await self.generate_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Smart response error: {str(e)}")
            return await self.generate_response(user_message, context)

# Global servis instance (lazy loading)
gemini_service = None

def get_gemini_service():
    global gemini_service
    if gemini_service is None:
        gemini_service = GeminiService()
    return gemini_service 
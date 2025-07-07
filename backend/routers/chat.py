from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from models.schemas import ChatRequest, ChatResponse
from services.gemini_service import get_gemini_service
from services.firebase_service import firebase_service
from services.audio_service import AudioService
import uuid
from datetime import datetime, timedelta
import logging
import requests
import tempfile
import os
import re

logger = logging.getLogger(__name__)

router = APIRouter()
audio_service = AudioService()

async def get_calendar_data():
    """Takvim verilerini al - Firebase'den direkt"""
    try:
        # Firebase'den direkt al
        events = firebase_service.get_events() if firebase_service.is_available() else []
        logger.info(f"Firebase returned {len(events)} calendar events")
        
        # Eğer events dict listesi değilse düzelt
        if events and isinstance(events, list):
            # Firebase format'ını düzelt
            formatted_events = []
            for event in events:
                if isinstance(event, dict):
                    formatted_events.append({
                        "id": event.get("id", ""),
                        "title": event.get("title", ""),
                        "datetime": event.get("datetime", ""),
                        "description": event.get("description", "")
                    })
            
            return {"events": formatted_events, "count": len(formatted_events)}
        
        return {"events": [], "count": 0}
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return {"events": [], "count": 0}

def extract_city_from_message(message: str) -> str:
    """Mesajdan şehir ismini çıkar"""
    message_lower = message.lower()
    
    # Türkiye'deki büyük şehirler
    cities = {
        "istanbul": "Istanbul",
        "ankara": "Ankara", 
        "izmir": "Izmir",
        "bursa": "Bursa",
        "antalya": "Antalya",
        "adana": "Adana",
        "konya": "Konya",
        "gaziantep": "Gaziantep",
        "mersin": "Mersin",
        "diyarbakır": "Diyarbakir",
        "kayseri": "Kayseri",
        "eskişehir": "Eskisehir",
        "samsun": "Samsun",
        "denizli": "Denizli",
        "şanlıurfa": "Sanliurfa",
        "adapazarı": "Adapazari",
        "malatya": "Malatya",
        "kahramanmaraş": "Kahramanmaras",
        "erzurum": "Erzurum",
        "van": "Van",
        "batman": "Batman",
        "elazığ": "Elazig",
        "şırnak": "Sirnak",
        "siirt": "Siirt",
        "mardin": "Mardin",
        "manisa": "Manisa",
        "muğla": "Mugla",
        "balıkesir": "Balikesir",
        "tekirdağ": "Tekirdag",
        "aydın": "Aydin",
        "sakarya": "Sakarya",
        "ordu": "Ordu",
        "trabzon": "Trabzon",
        "hatay": "Hatay",
        "uşak": "Usak"
    }
    
    # Mesajda şehir ismi var mı kontrol et
    for city_key, city_name in cities.items():
        if city_key in message_lower:
            return city_name
    
    # Şehir bulunamazsa varsayılan olarak İstanbul
    return "Istanbul"

async def get_weather_data(city: str = "Istanbul"):
    """Hava durumu verilerini al - direkt weather router'ından"""
    try:
        # Weather router'ını direkt import et ve çağır
        from routers.weather import get_weather_by_city
        weather_data = await get_weather_by_city(city)
        return weather_data
    except Exception as e:
        logger.error(f"Weather data error: {e}")
        return None

async def save_note(title: str, content: str):
    """Not kaydet"""
    try:
        response = requests.post(
            "http://localhost:8000/api/notes/",
            params={"title": title, "content": content},
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

async def create_calendar_event(title: str, datetime_str: str, description: str = ""):
    """Takvim etkinliği oluştur"""
    try:
        response = requests.post(
            "http://localhost:8000/api/calendar/events",
            params={
                "title": title,
                "datetime_str": datetime_str,
                "description": description
            },
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Kullanıcı mesajını işle ve AI yanıtı döndür - akıllı parsing ile
    """
    try:
        # Gemini servisini al
        gemini_service = get_gemini_service()
        
        # Akıllı intent analizi
        intent_data = await gemini_service.analyze_intent(request.message)
        intent = intent_data.get("intent", "chat")
        entities = intent_data.get("entities", {})
        
        logger.info(f"Intent: {intent}, Entities: {entities}, Message: {request.message}")
        
        # Context başlat
        context = {}
        
        # Intent'e göre işlem yap
        if intent == "note":
            # Not kaydetme
            title = entities.get("title", "Yeni Not")
            content = entities.get("content", request.message)
            
            logger.info(f"Saving note - Title: {title}, Content: {content}")
            saved_note = await save_note(title, content)
            
            if saved_note:
                context["note_saved"] = saved_note
                logger.info(f"Note saved successfully: {saved_note}")
            else:
                logger.warning("Failed to save note")
        
        elif intent == "calendar":
            # Etkinlik oluşturma
            title = entities.get("title", "Yeni Etkinlik")
            datetime_str = entities.get("datetime", "")
            description = entities.get("description", f"Kullanıcı tarafından oluşturulan etkinlik: {request.message}")
            
            # Varsayılan tarih
            if not datetime_str:
                tomorrow = datetime.now() + timedelta(days=1)
                datetime_str = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
            
            logger.info(f"Creating event - Title: {title}, DateTime: {datetime_str}")
            created_event = await create_calendar_event(title, datetime_str, description)
            
            if created_event:
                context["event_created"] = created_event
                logger.info(f"Event created successfully: {created_event}")
            else:
                logger.warning("Failed to create event")
        
        elif intent == "weather":
            # Hava durumu - şehir ismini mesajdan çıkar
            city = extract_city_from_message(request.message)
            weather_data = await get_weather_data(city)
            if weather_data:
                context["weather"] = weather_data
        
        elif intent == "chat":
            # Takvim sorgularını kontrol et
            if any(keyword in request.message.lower() for keyword in ["toplantı", "etkinlik", "takvim", "yarın", "bugün"]):
                calendar_data = await get_calendar_data()
                logger.info(f"Calendar data retrieved: {calendar_data}")
                
                # Tarih-based filtering
                filtered_events = []
                if calendar_data and "events" in calendar_data:
                    message_lower = request.message.lower()
                    
                    # Türkçe ay isimleri için filtering
                    turkish_months = {
                        'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 
                        'mayıs': '05', 'haziran': '06', 'temmuz': '07', 'ağustos': '08',
                        'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'
                    }
                    
                    # "13 Temmuz" formatını kontrol et
                    for month_name, month_num in turkish_months.items():
                        if month_name in message_lower:
                            # Gün sayısını bul
                            import re
                            day_match = re.search(r'(\d{1,2})\s+' + month_name, message_lower)
                            if day_match:
                                day = day_match.group(1).zfill(2)
                                target_date = f"2025-{month_num}-{day}"
                                logger.info(f"Filtering events for date: {target_date}")
                                
                                # Bu tarihteki etkinlikleri filtrele
                                for event in calendar_data["events"]:
                                    event_date = event.get("datetime", "")
                                    logger.info(f"Checking event: {event.get('title')} on {event_date}")
                                    if event_date.startswith(target_date):
                                        filtered_events.append(event)
                                        logger.info(f"Event matched: {event.get('title')}")
                                
                                logger.info(f"Found {len(filtered_events)} events for {target_date}")
                                break
                    
                    # Bugün/yarın kontrolü
                    today = datetime.now().date()
                    if "bugün" in message_lower:
                        target_date = today.strftime("%Y-%m-%d")
                        for event in calendar_data["events"]:
                            event_date = event.get("datetime", "")
                            if event_date.startswith(target_date):
                                filtered_events.append(event)
                    elif "yarın" in message_lower:
                        tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
                        for event in calendar_data["events"]:
                            event_date = event.get("datetime", "")
                            if event_date.startswith(tomorrow):
                                filtered_events.append(event)
                
                # Filtrelenmiş etkinlikleri context'e ekle
                context["calendar"] = {
                    "events": filtered_events,
                    "count": len(filtered_events),
                    "query_date": request.message
                }
            
            # Hava durumu sorgularını kontrol et
            if "hava" in request.message.lower():
                city = extract_city_from_message(request.message)
                weather_data = await get_weather_data(city)
                if weather_data:
                    context["weather"] = weather_data
        
        # Akıllı yanıt üret
        ai_response = await gemini_service.generate_smart_response(
            request.message, 
            intent_data,
            context
        )
        
        # Chat mesajını Firebase'e kaydet
        user_id = request.user_id or "default"
        if firebase_service.is_available():
            try:
                firebase_service.save_chat_message(
                    message=request.message,
                    response=ai_response,
                    user_id=user_id,
                    intent=intent
                )
                logger.info(f"Chat message saved to Firebase for user: {user_id}")
            except Exception as e:
                logger.warning(f"Failed to save chat message to Firebase: {e}")
        
        # Yanıt oluştur
        response = ChatResponse(
            response=ai_response,
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now()
        )
        
        logger.info(f"Chat response generated for user: {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Mesaj işlenirken hata oluştu"
        )

@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """
    Kullanıcının chat geçmişini getir
    """
    try:
        if firebase_service.is_available():
            chat_history = firebase_service.get_chat_history(user_id=user_id, limit=limit)
            return {
                "user_id": user_id,
                "count": len(chat_history),
                "messages": chat_history
            }
        else:
            return {
                "user_id": user_id,
                "count": 0,
                "messages": [],
                "note": "Firebase kullanılamıyor, chat geçmişi kaydedilmiyor"
            }
        
    except Exception as e:
        logger.error(f"Chat history error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Chat geçmişi getirilirken hata oluştu"
        )

@router.delete("/history/{user_id}")
async def delete_chat_history(user_id: str):
    """
    Kullanıcının chat geçmişini sil
    """
    try:
        if firebase_service.is_available():
            success = firebase_service.delete_chat_history(user_id=user_id)
            if success:
                return {"message": "Chat geçmişi başarıyla silindi"}
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Chat geçmişi silinemedi"
                )
        else:
            return {"message": "Firebase kullanılamıyor, chat geçmişi zaten yok"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat history deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Chat geçmişi silinirken hata oluştu"
        )

@router.post("/analyze-intent")
async def analyze_message_intent(request: ChatRequest):
    """
    Mesajın intent'ini analiz et (debug amaçlı)
    """
    try:
        gemini_service = get_gemini_service()
        intent_data = await gemini_service.analyze_intent(request.message)
        
        return {
            "message": request.message,
            "intent_data": intent_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Intent analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Intent analizi yapılırken hata oluştu"
        )

@router.get("/health")
async def chat_health():
    """
    Chat servisinin sağlık durumunu kontrol et
    """
    try:
        # Gemini servisini test et
        gemini_service = get_gemini_service()
        
        # Firebase durumunu kontrol et
        firebase_available = firebase_service.is_available()
        
        return {
            "status": "healthy",
            "gemini_service": "available",
            "firebase_service": "available" if firebase_available else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/audio-message", response_model=ChatResponse)
async def send_audio_message(file: UploadFile = File(...), user_id: str = "default"):
    """
    Sesli mesajı işle ve AI yanıtı döndür
    """
    try:
        # Sesli mesajı text'e çevir
        text_message = await audio_service.transcribe_audio(file)
        
        if not text_message:
            raise HTTPException(
                status_code=400,
                detail="Ses dosyası işlenemedi"
            )
        
        # Text mesajını normal mesaj gibi işle
        request = ChatRequest(message=text_message, user_id=user_id)
        return await send_message(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio message error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Sesli mesaj işlenirken hata oluştu"
        ) 
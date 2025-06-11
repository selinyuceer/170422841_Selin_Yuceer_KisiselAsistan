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

logger = logging.getLogger(__name__)

router = APIRouter()
audio_service = AudioService()

async def get_calendar_data():
    """Takvim verilerini al"""
    try:
        response = requests.get("http://localhost:8000/api/calendar/events", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"events": [], "count": 0}
    except:
        return {"events": [], "count": 0}

async def get_weather_data():
    """Hava durumu verilerini al"""
    try:
        response = requests.get("http://localhost:8000/api/weather/?city=Istanbul", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

async def save_note(title: str, content: str):
    """Not kaydet"""
    try:
        response = requests.post(
            "http://localhost:8000/api/notes/",
            params={"title": title, "content": content},
            timeout=5
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
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Kullanıcı mesajını işle ve AI yanıtı döndür
    """
    try:
        # Gemini servisini al
        gemini_service = get_gemini_service()
        
        # Intent analizi yap
        intent_data = await gemini_service.analyze_intent(request.message)
        intent = intent_data.get("intent", "chat")
        
        # Bağlam verilerini topla
        context = {}
        
        # Takvim sorguları için takvim verilerini al
        if intent == "calendar" or "toplantı" in request.message.lower() or "etkinlik" in request.message.lower() or "takvim" in request.message.lower():
            calendar_data = await get_calendar_data()
            context["calendar"] = calendar_data
            
            # Yarın sorgusu için özel kontrol
            if "yarın" in request.message.lower():
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow_events = []
                for event in calendar_data.get("events", []):
                    event_date = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                    if event_date.date() == tomorrow.date():
                        tomorrow_events.append(event)
                context["tomorrow_events"] = tomorrow_events
        
        # Hava durumu sorguları için hava durumu verilerini al
        if intent == "weather" or "hava" in request.message.lower():
            weather_data = await get_weather_data()
            if weather_data:
                context["weather"] = weather_data
        
        # Not kaydetme işlemi - Daha güçlü kontrol
        note_keywords = ["not al", "kaydet", "not et", "not olarak", "not ekle", "not olarak ekle", "not kaydet", "not oluştur", "not yaz", "not tut", "bunu not", "notu kaydet"]
        is_note_request = intent == "note" or any(keyword in request.message.lower() for keyword in note_keywords)
        
        logger.info(f"Note check - Intent: {intent}, Message: {request.message.lower()}, Is note request: {is_note_request}")
        
        if is_note_request:
            entities = intent_data.get("entities", {})
            title = entities.get("title", "")
            
            # Mesajdan başlık ve içerik çıkarma
            message_lower = request.message.lower()
            content = request.message
            
            # Başlık çıkarma mantığı
            if not title:
                if ":" in request.message:
                    # "Not al: başlık" formatı
                    parts = request.message.split(":", 1)
                    if len(parts) == 2:
                        title = parts[1].strip()
                        content = parts[1].strip()
                elif "not al" in message_lower:
                    # "not al" ifadesinden sonrasını başlık yap
                    idx = message_lower.find("not al")
                    if idx != -1:
                        title = request.message[idx + 6:].strip()
                        content = title
                elif "kaydet" in message_lower:
                    # "kaydet" ifadesinden sonrasını başlık yap
                    idx = message_lower.find("kaydet")
                    if idx != -1:
                        remaining = request.message[idx + 6:].strip()
                        if remaining.startswith(":"):
                            remaining = remaining[1:].strip()
                        title = remaining if remaining else "Yeni Not"
                        content = remaining if remaining else request.message
                elif "not olarak" in message_lower or "not ekle" in message_lower:
                    # "not olarak ekle" veya "not ekle" durumu
                    # Mesajın kendisini not olarak kaydet
                    if "not olarak ekle" in message_lower:
                        # "not olarak ekle" ifadesini temizle
                        clean_content = request.message.replace("not olarak ekle", "").strip()
                        if clean_content:
                            title = clean_content[:30] + "..." if len(clean_content) > 30 else clean_content
                            content = clean_content
                        else:
                            title = "Yeni Not"
                            content = "Boş not"
                    else:
                        # "not ekle" durumu
                        clean_content = request.message.replace("not ekle", "").strip()
                        if clean_content:
                            title = clean_content[:30] + "..." if len(clean_content) > 30 else clean_content
                            content = clean_content
                        else:
                            title = "Yeni Not"
                            content = request.message
                else:
                    # Varsayılan başlık
                    words = request.message.split()
                    if len(words) > 3:
                        title = " ".join(words[:4])  # İlk 4 kelimeyi başlık yap
                    else:
                        title = request.message[:20] + "..." if len(request.message) > 20 else request.message
            
            # Başlık çok uzunsa kısalt
            if len(title) > 50:
                title = title[:47] + "..."
            
            # Notu kaydet
            saved_note = await save_note(title, content)
            if saved_note:
                context["note_saved"] = saved_note
        
        # Etkinlik oluşturma işlemi
        calendar_keywords = ["etkinlik", "toplantı", "randevu", "takvim", "etkinlik oluştur", "toplantı kur"]
        is_calendar_request = intent == "calendar" or any(keyword in request.message.lower() for keyword in calendar_keywords)
        
        logger.info(f"Calendar check - Intent: {intent}, Message: {request.message.lower()}, Is calendar request: {is_calendar_request}")
        
        if is_calendar_request:
            entities = intent_data.get("entities", {})
            title = entities.get("title", "")
            datetime_str = entities.get("datetime", "")
            
            # Mesajdan başlık ve tarih çıkarma
            message_lower = request.message.lower()
            
            # Başlık çıkarma mantığı
            if not title:
                if ":" in request.message:
                    # "Etkinlik oluştur: başlık" formatı
                    parts = request.message.split(":", 1)
                    if len(parts) == 2:
                        title = parts[1].strip()
                elif any(word in message_lower for word in ["etkinlik", "toplantı", "randevu"]):
                    # Anahtar kelimeden sonrasını başlık yap
                    for keyword in ["etkinlik oluştur", "toplantı kur", "randevu al", "etkinlik", "toplantı", "randevu"]:
                        if keyword in message_lower:
                            idx = message_lower.find(keyword)
                            if idx != -1:
                                remaining = request.message[idx + len(keyword):].strip()
                                if remaining:
                                    # Tarih ifadelerini temizle
                                    import re
                                    # Tarih kalıplarını bul ve temizle
                                    date_patterns = [
                                        r'\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b',  # 12/06/2025
                                        r'\b\d{1,2}:\d{2}\b',  # 10:00
                                        r'\byarın\b', r'\bbugün\b', r'\bgelecek\s+\w+\b'
                                    ]
                                    clean_title = remaining
                                    for pattern in date_patterns:
                                        clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
                                    title = clean_title.strip()
                                    break
                
                if not title:
                    title = "Yeni Etkinlik"
            
            # Tarih çıkarma (basit)
            if not datetime_str:
                import re
                from datetime import datetime as dt, timedelta as td
                
                # Yarın kontrolü
                if "yarın" in message_lower:
                    tomorrow = dt.now() + td(days=1)
                    # Saat varsa çıkar
                    time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', request.message)
                    if time_match:
                        hour, minute = int(time_match.group(1)), int(time_match.group(2))
                        datetime_str = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                    else:
                        datetime_str = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
                
                # Bugün kontrolü
                elif "bugün" in message_lower:
                    today = dt.now()
                    time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', request.message)
                    if time_match:
                        hour, minute = int(time_match.group(1)), int(time_match.group(2))
                        datetime_str = today.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                    else:
                        datetime_str = today.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
                
                # Tarih formatı kontrolü (12/06/2025)
                else:
                    date_match = re.search(r'\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b', request.message)
                    if date_match:
                        day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                        if year < 100:
                            year += 2000
                        
                        time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', request.message)
                        if time_match:
                            hour, minute = int(time_match.group(1)), int(time_match.group(2))
                        else:
                            hour, minute = 10, 0
                        
                        try:
                            event_date = dt(year, month, day, hour, minute)
                            datetime_str = event_date.isoformat()
                        except:
                            pass
                
                # Varsayılan: yarın saat 10:00
                if not datetime_str:
                    tomorrow = dt.now() + td(days=1)
                    datetime_str = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
            
            # Açıklama oluştur
            description = f"Gemini AI tarafından oluşturulan etkinlik: {request.message}"
            
            # Etkinliği oluştur
            logger.info(f"Creating event - Title: {title}, DateTime: {datetime_str}, Description: {description}")
            created_event = await create_calendar_event(title, datetime_str, description)
            logger.info(f"Event creation result: {created_event}")
            if created_event:
                context["event_created"] = created_event
        
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
            if firebase_service.delete_chat_history(user_id=user_id):
                return {
                    "message": "Chat geçmişi başarıyla silindi",
                    "user_id": user_id
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Chat geçmişi silinirken hata oluştu"
                )
        else:
            return {
                "message": "Firebase kullanılamıyor, silinecek chat geçmişi yok",
                "user_id": user_id
            }
        
    except Exception as e:
        logger.error(f"Chat history deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Chat geçmişi silinirken hata oluştu"
        )

@router.post("/analyze-intent")
async def analyze_message_intent(request: ChatRequest):
    """
    Mesaj amacını analiz et (debug için)
    """
    try:
        gemini_service = get_gemini_service()
        intent_data = await gemini_service.analyze_intent(request.message)
        return {
            "message": request.message,
            "intent_analysis": intent_data,
            "timestamp": datetime.now()
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
    Chat servisinin sağlık durumu
    """
    try:
        # Basit bir test mesajı gönder
        gemini_service = get_gemini_service()
        test_response = await gemini_service.generate_response("Merhaba")
        
        return {
            "status": "healthy",
            "gemini_service": "active",
            "firebase_service": "active" if firebase_service.is_available() else "inactive",
            "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/audio-message", response_model=ChatResponse)
async def send_audio_message(file: UploadFile = File(...), user_id: str = "default"):
    """
    Sesli mesajı işle ve AI yanıtı döndür
    """
    temp_file_path = None
    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file_path = temp_file.name
            # Ses dosyasını geçici dosyaya yaz
            file_content = await file.read()
            temp_file.write(file_content)
        
        logger.info(f"Audio file saved to: {temp_file_path}")
        
        # Ses dosyasını metne dönüştür
        text = audio_service.speech_to_text(temp_file_path)
        logger.info(f"Speech to text result: {text}")
        
        # Eğer ses tanıma başarısızsa hata mesajı döndür
        if not text or text.startswith("Ses"):
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                response=text or "Ses dosyası işlenemedi. Lütfen tekrar deneyin.",
                timestamp=datetime.now().isoformat()
            )
        
        # Metni normal mesaj olarak işle
        chat_request = ChatRequest(message=text, user_id=user_id)
        response = await send_message(chat_request)
        
        # Yanıta orijinal ses metnini ekle
        response.original_audio_text = text
        
        return response
        
    except Exception as e:
        logger.error(f"Sesli mesaj işlenirken hata oluştu: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sesli mesaj işlenirken hata oluştu: {str(e)}"
        )
    finally:
        # Geçici dosyayı temizle
        if temp_file_path:
            audio_service.cleanup_temp_file(temp_file_path) 
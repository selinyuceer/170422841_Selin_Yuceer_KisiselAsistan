from fastapi import APIRouter, HTTPException
from models.schemas import CalendarEventRequest, CalendarEventResponse
from services.firebase_service import firebase_service
from typing import List
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Geçici in-memory storage (Firebase kullanılamadığında fallback)
events_storage = {}

@router.get("/events")
async def get_all_events():
    """
    Tüm takvim etkinliklerini listele
    """
    try:
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            firebase_events = firebase_service.get_events()
            return {
                "events": firebase_events,
                "count": len(firebase_events)
            }
        
        # Firebase kullanılamazsa in-memory storage'dan al
        all_events = [
            {
                "id": event["id"],
                "title": event["title"],
                "description": event["description"],
                "datetime": event["start_time"].isoformat(),
                "created_at": event["created_at"].isoformat()
            }
            for event in events_storage.values()
        ]
        
        # Başlangıç zamanına göre sırala
        all_events.sort(key=lambda x: x["datetime"])
        
        return {
            "events": all_events,
            "count": len(all_events)
        }
        
    except Exception as e:
        logger.error(f"Events listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Etkinlikler listelenirken hata oluştu"
        )

@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event_simple(title: str, datetime_str: str, description: str = "", user_id: str = "default"):
    """
    Basit takvim etkinliği oluştur
    """
    try:
        # Firebase kullanılabilirse Firebase'e kaydet
        if firebase_service.is_available():
            event_id = firebase_service.create_event(title, datetime_str, description, user_id)
            if event_id:
                logger.info(f"Calendar event created in Firebase: {event_id}")
                # Firebase'den kaydedilen etkinliği döndür
                try:
                    event_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                except:
                    event_datetime = datetime.now() + timedelta(hours=1)
                
                return CalendarEventResponse(
                    id=event_id,
                    title=title,
                    description=description,
                    start_time=event_datetime,
                    end_time=event_datetime + timedelta(hours=1),
                    user_id=user_id,
                    created_at=datetime.now()
                )
        
        # Firebase kullanılamazsa in-memory storage'a kaydet
        event_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Datetime string'ini parse et
        try:
            event_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            event_datetime = datetime.now() + timedelta(hours=1)
        
        event = {
            "id": event_id,
            "title": title,
            "description": description,
            "start_time": event_datetime,
            "end_time": event_datetime + timedelta(hours=1),
            "user_id": user_id,
            "created_at": now
        }
        
        events_storage[event_id] = event
        
        logger.info(f"Calendar event created in memory: {event_id}")
        return CalendarEventResponse(**event)
        
    except Exception as e:
        logger.error(f"Calendar event creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Takvim etkinliği oluşturulurken hata oluştu"
        )

@router.post("/create-event", response_model=CalendarEventResponse)
async def create_calendar_event(request: CalendarEventRequest):
    """
    Yeni takvim etkinliği oluştur
    """
    try:
        # Başlangıç zamanı bitiş zamanından sonra olamaz
        if request.start_time >= request.end_time:
            raise HTTPException(
                status_code=400,
                detail="Başlangıç zamanı bitiş zamanından önce olmalıdır"
            )
        
        # Firebase kullanılabilirse Firebase'e kaydet
        if firebase_service.is_available():
            event_id = firebase_service.create_event(
                title=request.title,
                datetime_str=request.start_time.isoformat(),
                description=request.description,
                user_id=request.user_id
            )
            if event_id:
                logger.info(f"Calendar event created in Firebase: {event_id}")
                return CalendarEventResponse(
                    id=event_id,
                    title=request.title,
                    description=request.description,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    user_id=request.user_id,
                    created_at=datetime.now()
                )
        
        # Firebase kullanılamazsa in-memory storage'a kaydet
        event_id = str(uuid.uuid4())
        now = datetime.now()
        
        event = {
            "id": event_id,
            "title": request.title,
            "description": request.description,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "user_id": request.user_id,
            "created_at": now
        }
        
        events_storage[event_id] = event
        
        logger.info(f"Calendar event created in memory: {event_id} for user: {request.user_id}")
        return CalendarEventResponse(**event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calendar event creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Takvim etkinliği oluşturulurken hata oluştu"
        )

@router.get("/events/{user_id}", response_model=List[CalendarEventResponse])
async def get_user_events(user_id: str, start_date: str = None, end_date: str = None):
    """
    Kullanıcının takvim etkinliklerini listele
    """
    try:
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            firebase_events = firebase_service.get_events(user_id=user_id)
            user_events = []
            
            for event in firebase_events:
                try:
                    # Firebase'den gelen datetime string'ini parse et
                    event_datetime = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                    user_events.append(CalendarEventResponse(
                        id=event["id"],
                        title=event["title"],
                        description=event.get("description", ""),
                        start_time=event_datetime,
                        end_time=event_datetime + timedelta(hours=1),  # Varsayılan 1 saat
                        user_id=event.get("user_id", user_id),
                        created_at=datetime.fromisoformat(event["created_at"]) if event.get("created_at") else datetime.now()
                    ))
                except Exception as parse_error:
                    logger.warning(f"Error parsing event {event.get('id', 'unknown')}: {parse_error}")
                    continue
        else:
            # In-memory storage'dan al
            user_events = [
                CalendarEventResponse(**event) 
                for event in events_storage.values() 
                if event["user_id"] == user_id
            ]
        
        # Tarih filtresi uygula
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                user_events = [e for e in user_events if e.start_time >= start_dt]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Geçersiz başlangıç tarihi formatı (YYYY-MM-DD kullanın)"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                user_events = [e for e in user_events if e.end_time <= end_dt]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Geçersiz bitiş tarihi formatı (YYYY-MM-DD kullanın)"
                )
        
        # Başlangıç zamanına göre sırala
        user_events.sort(key=lambda x: x.start_time)
        
        return user_events
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Events listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Etkinlikler listelenirken hata oluştu"
        )

@router.get("/events/today/{user_id}")
async def get_today_events(user_id: str):
    """
    Bugünkü etkinlikleri getir
    """
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            firebase_events = firebase_service.get_events(user_id=user_id)
            today_events = []
            
            for event in firebase_events:
                try:
                    event_datetime = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                    if today_start <= event_datetime <= today_end:
                        today_events.append(CalendarEventResponse(
                            id=event["id"],
                            title=event["title"],
                            description=event.get("description", ""),
                            start_time=event_datetime,
                            end_time=event_datetime + timedelta(hours=1),
                            user_id=event.get("user_id", user_id),
                            created_at=datetime.fromisoformat(event["created_at"]) if event.get("created_at") else datetime.now()
                        ))
                except Exception as parse_error:
                    logger.warning(f"Error parsing today event {event.get('id', 'unknown')}: {parse_error}")
                    continue
        else:
            # In-memory storage'dan al
            today_events = [
                CalendarEventResponse(**event)
                for event in events_storage.values()
                if (event["user_id"] == user_id and 
                    today_start <= event["start_time"] <= today_end)
            ]
        
        # Başlangıç zamanına göre sırala
        today_events.sort(key=lambda x: x.start_time)
        
        return {
            "date": today.isoformat(),
            "count": len(today_events),
            "events": today_events
        }
        
    except Exception as e:
        logger.error(f"Today events error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Bugünkü etkinlikler getirilirken hata oluştu"
        )

@router.get("/events/upcoming/{user_id}")
async def get_upcoming_events(user_id: str, days: int = 7):
    """
    Yaklaşan etkinlikleri getir (varsayılan 7 gün)
    """
    try:
        now = datetime.now()
        future_limit = now + timedelta(days=days)
        
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            firebase_events = firebase_service.get_events(user_id=user_id)
            upcoming_events = []
            
            for event in firebase_events:
                try:
                    event_datetime = datetime.fromisoformat(event["datetime"].replace('Z', '+00:00'))
                    if now <= event_datetime <= future_limit:
                        upcoming_events.append(CalendarEventResponse(
                            id=event["id"],
                            title=event["title"],
                            description=event.get("description", ""),
                            start_time=event_datetime,
                            end_time=event_datetime + timedelta(hours=1),
                            user_id=event.get("user_id", user_id),
                            created_at=datetime.fromisoformat(event["created_at"]) if event.get("created_at") else datetime.now()
                        ))
                except Exception as parse_error:
                    logger.warning(f"Error parsing upcoming event {event.get('id', 'unknown')}: {parse_error}")
                    continue
        else:
            # In-memory storage'dan al
            upcoming_events = [
                CalendarEventResponse(**event)
                for event in events_storage.values()
                if (event["user_id"] == user_id and 
                    now <= event["start_time"] <= future_limit)
            ]
        
        # Başlangıç zamanına göre sırala
        upcoming_events.sort(key=lambda x: x.start_time)
        
        return {
            "period_days": days,
            "count": len(upcoming_events),
            "events": upcoming_events
        }
        
    except Exception as e:
        logger.error(f"Upcoming events error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Yaklaşan etkinlikler getirilirken hata oluştu"
        )

@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """
    Etkinliği sil
    """
    try:
        # Firebase kullanılabilirse Firebase'den sil
        if firebase_service.is_available():
            if firebase_service.delete_event(event_id):
                logger.info(f"Calendar event deleted from Firebase: {event_id}")
                return {
                    "message": "Etkinlik başarıyla silindi",
                    "deleted_event_id": event_id
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Etkinlik bulunamadı"
                )
        
        # In-memory storage'dan sil
        if event_id not in events_storage:
            raise HTTPException(
                status_code=404,
                detail="Etkinlik bulunamadı"
            )
        
        deleted_event = events_storage.pop(event_id)
        
        logger.info(f"Calendar event deleted from memory: {event_id}")
        return {
            "message": "Etkinlik başarıyla silindi",
            "deleted_event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Etkinlik silinirken hata oluştu"
        )

@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(event_id: str, request: CalendarEventRequest):
    """
    Etkinliği güncelle
    """
    try:
        # Başlangıç zamanı bitiş zamanından sonra olamaz
        if request.start_time >= request.end_time:
            raise HTTPException(
                status_code=400,
                detail="Başlangıç zamanı bitiş zamanından önce olmalıdır"
            )
        
        # Firebase kullanılabilirse Firebase'de güncelle
        if firebase_service.is_available():
            if firebase_service.update_event(
                event_id=event_id,
                title=request.title,
                datetime_str=request.start_time.isoformat(),
                description=request.description
            ):
                logger.info(f"Calendar event updated in Firebase: {event_id}")
                return CalendarEventResponse(
                    id=event_id,
                    title=request.title,
                    description=request.description,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    user_id=request.user_id,
                    created_at=datetime.now()  # Firebase'den gerçek created_at alınabilir
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Etkinlik bulunamadı"
                )
        
        # In-memory storage'da güncelle
        if event_id not in events_storage:
            raise HTTPException(
                status_code=404,
                detail="Etkinlik bulunamadı"
            )
        
        # Mevcut etkinliği güncelle
        existing_event = events_storage[event_id]
        existing_event.update({
            "title": request.title,
            "description": request.description,
            "start_time": request.start_time,
            "end_time": request.end_time,
        })
        
        logger.info(f"Calendar event updated in memory: {event_id}")
        return CalendarEventResponse(**existing_event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Etkinlik güncellenirken hata oluştu"
        ) 
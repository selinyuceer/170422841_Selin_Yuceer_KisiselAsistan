from fastapi import APIRouter, HTTPException
from models.schemas import ReminderRequest, ReminderResponse
from services.firebase_service import firebase_service
from typing import List
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Geçici in-memory storage (Firebase kullanılamadığında fallback)
reminders_storage = {}

@router.post("/create", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    """
    Yeni hatırlatıcı oluştur
    """
    try:
        # Firebase kullanılabilirse Firebase'e kaydet
        if firebase_service.is_available():
            reminder_id = firebase_service.create_reminder(
                title=request.title,
                description=request.description,
                reminder_time=request.reminder_time.isoformat(),
                user_id=request.user_id
            )
            if reminder_id:
                logger.info(f"Reminder created in Firebase: {reminder_id}")
                return ReminderResponse(
                    id=reminder_id,
                    title=request.title,
                    description=request.description,
                    reminder_time=request.reminder_time,
                    user_id=request.user_id,
                    is_completed=False,
                    created_at=datetime.now()
                )
        
        # Firebase kullanılamazsa in-memory storage'a kaydet
        reminder_id = str(uuid.uuid4())
        now = datetime.now()
        
        reminder = {
            "id": reminder_id,
            "title": request.title,
            "description": request.description,
            "reminder_time": request.reminder_time,
            "user_id": request.user_id,
            "is_completed": False,
            "created_at": now
        }
        
        reminders_storage[reminder_id] = reminder
        
        logger.info(f"Reminder created in memory: {reminder_id} for user: {request.user_id}")
        return ReminderResponse(**reminder)
        
    except Exception as e:
        logger.error(f"Reminder creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı oluşturulurken hata oluştu"
        )

@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(user_id: str = None, include_completed: bool = False):
    """
    Hatırlatıcıları listele
    """
    try:
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            firebase_reminders = firebase_service.get_reminders(user_id=user_id, include_completed=include_completed)
            reminders = []
            
            for reminder in firebase_reminders:
                try:
                    # Firebase'den gelen reminder_time string'ini parse et
                    reminder_time = datetime.fromisoformat(reminder["reminder_time"].replace('Z', '+00:00'))
                    reminders.append(ReminderResponse(
                        id=reminder["id"],
                        title=reminder["title"],
                        description=reminder.get("description", ""),
                        reminder_time=reminder_time,
                        user_id=reminder.get("user_id", "default"),
                        is_completed=reminder.get("is_completed", False),
                        created_at=datetime.fromisoformat(reminder["created_at"]) if reminder.get("created_at") else datetime.now()
                    ))
                except Exception as parse_error:
                    logger.warning(f"Error parsing reminder {reminder.get('id', 'unknown')}: {parse_error}")
                    continue
            
            return reminders
        
        # In-memory storage'dan al
        user_reminders = []
        for reminder in reminders_storage.values():
            if user_id and reminder["user_id"] != user_id:
                continue
            if not include_completed and reminder.get("is_completed", False):
                continue
            user_reminders.append(ReminderResponse(**reminder))
        
        # Hatırlatma zamanına göre sırala
        user_reminders.sort(key=lambda x: x.reminder_time)
        
        return user_reminders
        
    except Exception as e:
        logger.error(f"Reminders listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcılar listelenirken hata oluştu"
        )

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(reminder_id: str):
    """
    Belirli bir hatırlatıcıyı getir
    """
    try:
        # Firebase kullanılabilirse Firebase'den al
        if firebase_service.is_available():
            # Firebase'de tek reminder getirme fonksiyonu yok, tüm reminders'ı alıp filtrele
            firebase_reminders = firebase_service.get_reminders(include_completed=True)
            for reminder in firebase_reminders:
                if reminder["id"] == reminder_id:
                    reminder_time = datetime.fromisoformat(reminder["reminder_time"].replace('Z', '+00:00'))
                    return ReminderResponse(
                        id=reminder["id"],
                        title=reminder["title"],
                        description=reminder.get("description", ""),
                        reminder_time=reminder_time,
                        user_id=reminder.get("user_id", "default"),
                        is_completed=reminder.get("is_completed", False),
                        created_at=datetime.fromisoformat(reminder["created_at"]) if reminder.get("created_at") else datetime.now()
                    )
            
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        # In-memory storage'dan al
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        return ReminderResponse(**reminders_storage[reminder_id])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reminder get error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı getirilirken hata oluştu"
        )

@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(reminder_id: str, request: ReminderRequest):
    """
    Hatırlatıcıyı güncelle
    """
    try:
        # Firebase kullanılabilirse Firebase'de güncelle
        if firebase_service.is_available():
            if firebase_service.update_reminder(
                reminder_id=reminder_id,
                title=request.title,
                description=request.description,
                reminder_time=request.reminder_time.isoformat()
            ):
                logger.info(f"Reminder updated in Firebase: {reminder_id}")
                return ReminderResponse(
                    id=reminder_id,
                    title=request.title,
                    description=request.description,
                    reminder_time=request.reminder_time,
                    user_id=request.user_id,
                    is_completed=False,  # Güncelleme sırasında completed durumu korunabilir
                    created_at=datetime.now()  # Firebase'den gerçek created_at alınabilir
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Hatırlatıcı bulunamadı"
                )
        
        # In-memory storage'da güncelle
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        # Mevcut hatırlatıcıyı güncelle
        existing_reminder = reminders_storage[reminder_id]
        existing_reminder.update({
            "title": request.title,
            "description": request.description,
            "reminder_time": request.reminder_time,
        })
        
        logger.info(f"Reminder updated in memory: {reminder_id}")
        return ReminderResponse(**existing_reminder)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reminder update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı güncellenirken hata oluştu"
        )

@router.patch("/{reminder_id}/complete")
async def complete_reminder(reminder_id: str):
    """
    Hatırlatıcıyı tamamlandı olarak işaretle
    """
    try:
        # Firebase kullanılabilirse Firebase'de güncelle
        if firebase_service.is_available():
            if firebase_service.update_reminder(reminder_id=reminder_id, is_completed=True):
                logger.info(f"Reminder completed in Firebase: {reminder_id}")
                return {
                    "message": "Hatırlatıcı tamamlandı olarak işaretlendi",
                    "reminder_id": reminder_id
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Hatırlatıcı bulunamadı"
                )
        
        # In-memory storage'da güncelle
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        reminders_storage[reminder_id]["is_completed"] = True
        
        logger.info(f"Reminder completed in memory: {reminder_id}")
        return {
            "message": "Hatırlatıcı tamamlandı olarak işaretlendi",
            "reminder_id": reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reminder completion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı tamamlanırken hata oluştu"
        )

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """
    Hatırlatıcıyı sil
    """
    try:
        # Firebase kullanılabilirse Firebase'den sil
        if firebase_service.is_available():
            if firebase_service.delete_reminder(reminder_id):
                logger.info(f"Reminder deleted from Firebase: {reminder_id}")
                return {
                    "message": "Hatırlatıcı başarıyla silindi",
                    "deleted_reminder_id": reminder_id
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Hatırlatıcı bulunamadı"
                )
        
        # In-memory storage'dan sil
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        deleted_reminder = reminders_storage.pop(reminder_id)
        
        logger.info(f"Reminder deleted from memory: {reminder_id}")
        return {
            "message": "Hatırlatıcı başarıyla silindi",
            "deleted_reminder_id": reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reminder deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı silinirken hata oluştu"
        )

@router.get("/user/{user_id}/active", response_model=List[ReminderResponse])
async def get_active_reminders(user_id: str):
    """
    Kullanıcının aktif (tamamlanmamış) hatırlatıcılarını getir
    """
    try:
        return await get_reminders(user_id=user_id, include_completed=False)
        
    except Exception as e:
        logger.error(f"Active reminders error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Aktif hatırlatıcılar getirilirken hata oluştu"
        )

@router.get("/user/{user_id}/upcoming")
async def get_upcoming_reminders(user_id: str, hours: int = 24):
    """
    Yaklaşan hatırlatıcıları getir (varsayılan 24 saat)
    """
    try:
        from datetime import timedelta
        
        now = datetime.now()
        future_limit = now + timedelta(hours=hours)
        
        # Tüm aktif hatırlatıcıları al
        all_reminders = await get_reminders(user_id=user_id, include_completed=False)
        
        # Yaklaşan olanları filtrele
        upcoming_reminders = [
            reminder for reminder in all_reminders
            if now <= reminder.reminder_time <= future_limit
        ]
        
        # Hatırlatma zamanına göre sırala
        upcoming_reminders.sort(key=lambda x: x.reminder_time)
        
        return {
            "period_hours": hours,
            "count": len(upcoming_reminders),
            "reminders": upcoming_reminders
        }
        
    except Exception as e:
        logger.error(f"Upcoming reminders error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Yaklaşan hatırlatıcılar getirilirken hata oluştu"
        ) 
from fastapi import APIRouter, HTTPException
from models.schemas import ReminderRequest, ReminderResponse
from typing import List
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Geçici in-memory storage (sonra Firebase ile değiştirilecek)
reminders_storage = {}

@router.post("/create", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    """
    Yeni hatırlatıcı oluştur
    """
    try:
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
        
        logger.info(f"Reminder created: {reminder_id} for user: {request.user_id}")
        return ReminderResponse(**reminder)
        
    except Exception as e:
        logger.error(f"Reminder creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcı oluşturulurken hata oluştu"
        )

@router.get("/list/{user_id}", response_model=List[ReminderResponse])
async def get_user_reminders(user_id: str, include_completed: bool = False):
    """
    Kullanıcının hatırlatıcılarını listele
    """
    try:
        user_reminders = [
            ReminderResponse(**reminder) 
            for reminder in reminders_storage.values() 
            if reminder["user_id"] == user_id and (include_completed or not reminder["is_completed"])
        ]
        
        # Hatırlatma zamanına göre sırala
        user_reminders.sort(key=lambda x: x.reminder_time)
        
        return user_reminders
        
    except Exception as e:
        logger.error(f"Reminders listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hatırlatıcılar listelenirken hata oluştu"
        )

@router.put("/{reminder_id}/complete")
async def complete_reminder(reminder_id: str):
    """
    Hatırlatıcıyı tamamlandı olarak işaretle
    """
    try:
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        reminders_storage[reminder_id]["is_completed"] = True
        
        logger.info(f"Reminder completed: {reminder_id}")
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
            detail="Hatırlatıcı güncellenirken hata oluştu"
        )

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """
    Hatırlatıcıyı sil
    """
    try:
        if reminder_id not in reminders_storage:
            raise HTTPException(
                status_code=404,
                detail="Hatırlatıcı bulunamadı"
            )
        
        deleted_reminder = reminders_storage.pop(reminder_id)
        
        logger.info(f"Reminder deleted: {reminder_id}")
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

@router.get("/upcoming/{user_id}")
async def get_upcoming_reminders(user_id: str):
    """
    Yaklaşan hatırlatıcıları getir (24 saat içinde)
    """
    try:
        now = datetime.now()
        upcoming_limit = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        upcoming_reminders = [
            ReminderResponse(**reminder)
            for reminder in reminders_storage.values()
            if (reminder["user_id"] == user_id and 
                not reminder["is_completed"] and
                now <= reminder["reminder_time"] <= upcoming_limit)
        ]
        
        # Hatırlatma zamanına göre sırala
        upcoming_reminders.sort(key=lambda x: x.reminder_time)
        
        return {
            "count": len(upcoming_reminders),
            "reminders": upcoming_reminders
        }
        
    except Exception as e:
        logger.error(f"Upcoming reminders error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Yaklaşan hatırlatıcılar getirilirken hata oluştu"
        ) 
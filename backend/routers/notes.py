from fastapi import APIRouter, HTTPException
from models.schemas import NoteRequest, NoteResponse
from typing import List
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Geçici in-memory storage (sonra Firebase ile değiştirilecek)
notes_storage = {}

@router.get("/")
async def get_all_notes():
    """
    Tüm notları listele (demo için)
    """
    try:
        all_notes = [
            {
                "id": note["id"],
                "title": note["title"],
                "content": note["content"],
                "created_at": note["created_at"].isoformat(),
                "updated_at": note["updated_at"].isoformat()
            }
            for note in notes_storage.values()
        ]
        
        # Tarihe göre sırala (en yeni önce)
        all_notes.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "notes": all_notes,
            "count": len(all_notes)
        }
        
    except Exception as e:
        logger.error(f"Notes listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Notlar listelenirken hata oluştu"
        )

@router.post("/")
async def create_note_simple(title: str, content: str):
    """
    Basit not oluştur
    """
    try:
        note_id = str(uuid.uuid4())
        now = datetime.now()
        
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "user_id": "default",
            "is_voice_note": False,
            "created_at": now,
            "updated_at": now
        }
        
        notes_storage[note_id] = note
        
        logger.info(f"Note created: {note_id}")
        return {
            "id": note_id,
            "title": title,
            "content": content,
            "created_at": now.isoformat(),
            "message": "Not başarıyla oluşturuldu"
        }
        
    except Exception as e:
        logger.error(f"Note creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Not oluşturulurken hata oluştu"
        )

@router.post("/create", response_model=NoteResponse)
async def create_note(request: NoteRequest):
    """
    Yeni not oluştur
    """
    try:
        note_id = str(uuid.uuid4())
        now = datetime.now()
        
        note = {
            "id": note_id,
            "title": request.title,
            "content": request.content,
            "user_id": request.user_id,
            "is_voice_note": request.is_voice_note,
            "created_at": now,
            "updated_at": now
        }
        
        notes_storage[note_id] = note
        
        logger.info(f"Note created: {note_id} for user: {request.user_id}")
        return NoteResponse(**note)
        
    except Exception as e:
        logger.error(f"Note creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Not oluşturulurken hata oluştu"
        )

@router.get("/list/{user_id}", response_model=List[NoteResponse])
async def get_user_notes(user_id: str):
    """
    Kullanıcının notlarını listele
    """
    try:
        user_notes = [
            NoteResponse(**note) 
            for note in notes_storage.values() 
            if note["user_id"] == user_id
        ]
        
        # Tarihe göre sırala (en yeni önce)
        user_notes.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_notes
        
    except Exception as e:
        logger.error(f"Notes listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Notlar listelenirken hata oluştu"
        )

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """
    Belirli bir notu getir
    """
    try:
        if note_id not in notes_storage:
            raise HTTPException(
                status_code=404,
                detail="Not bulunamadı"
            )
        
        return NoteResponse(**notes_storage[note_id])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note retrieval error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Not getirilirken hata oluştu"
        )

@router.delete("/{note_id}")
async def delete_note(note_id: str):
    """
    Notu sil
    """
    try:
        if note_id not in notes_storage:
            raise HTTPException(
                status_code=404,
                detail="Not bulunamadı"
            )
        
        deleted_note = notes_storage.pop(note_id)
        
        logger.info(f"Note deleted: {note_id}")
        return {
            "message": "Not başarıyla silindi",
            "deleted_note_id": note_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Not silinirken hata oluştu"
        ) 
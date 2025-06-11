from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

class ChatRequest(BaseModel):
    message: str = Field(..., description="Kullanıcı mesajı")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Mesaj tipi")
    user_id: Optional[str] = Field(None, description="Kullanıcı ID")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI yanıtı")
    message_id: str = Field(..., description="Mesaj ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    original_audio_text: Optional[str] = Field(None, description="Orijinal ses metni")

class NoteRequest(BaseModel):
    title: str = Field(..., description="Not başlığı")
    content: str = Field(..., description="Not içeriği")
    user_id: str = Field(..., description="Kullanıcı ID")
    is_voice_note: bool = Field(default=False, description="Sesli not mu?")

class NoteResponse(BaseModel):
    id: str = Field(..., description="Not ID")
    title: str
    content: str
    user_id: str
    is_voice_note: bool
    created_at: datetime
    updated_at: datetime

class ReminderRequest(BaseModel):
    title: str = Field(..., description="Hatırlatıcı başlığı")
    description: Optional[str] = Field(None, description="Hatırlatıcı açıklaması")
    reminder_time: datetime = Field(..., description="Hatırlatma zamanı")
    user_id: str = Field(..., description="Kullanıcı ID")

class ReminderResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    reminder_time: datetime
    user_id: str
    is_completed: bool
    created_at: datetime

class CalendarEventRequest(BaseModel):
    title: str = Field(..., description="Etkinlik başlığı")
    description: Optional[str] = Field(None, description="Etkinlik açıklaması")
    start_time: datetime = Field(..., description="Başlangıç zamanı")
    end_time: datetime = Field(..., description="Bitiş zamanı")
    user_id: str = Field(..., description="Kullanıcı ID")

class CalendarEventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    user_id: str
    created_at: datetime

class WeatherRequest(BaseModel):
    city: str = Field(..., description="Şehir adı")
    country_code: Optional[str] = Field(None, description="Ülke kodu (TR, US, vb.)")

class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    pressure: int
    timestamp: datetime = Field(default_factory=datetime.now) 
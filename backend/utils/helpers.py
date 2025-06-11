from datetime import datetime, timezone
from typing import Optional, Dict, Any
import re
import uuid

def generate_unique_id() -> str:
    """Benzersiz ID üret"""
    return str(uuid.uuid4())

def get_current_timestamp() -> datetime:
    """Şu anki zaman damgasını getir"""
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Datetime'ı string'e çevir"""
    return dt.strftime(format_str)

def parse_datetime(date_str: str) -> Optional[datetime]:
    """String'i datetime'a çevir"""
    try:
        # ISO format dene
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Standart format dene
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

def clean_text(text: str) -> str:
    """Metni temizle"""
    if not text:
        return ""
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Özel karakterleri temizle (isteğe bağlı)
    # text = re.sub(r'[^\w\s\-.,!?]', '', text)
    
    return text

def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """Metinden varlıkları çıkar (basit regex tabanlı)"""
    entities = {}
    
    # Tarih kalıpları (Türkçe)
    date_patterns = [
        r'(\d{1,2})\s*(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)',
        r'(\d{1,2})[./](\d{1,2})[./](\d{2,4})',
        r'(bugün|yarın|pazartesi|salı|çarşamba|perşembe|cuma|cumartesi|pazar)'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            entities['dates'] = matches
            break
    
    # Saat kalıpları
    time_patterns = [
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})\s*(sabah|öğle|akşam|gece)'
    ]
    
    for pattern in time_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            entities['times'] = matches
            break
    
    # Şehir isimleri (basit liste)
    cities = ['istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 'konya', 'gaziantep']
    for city in cities:
        if city in text.lower():
            entities['city'] = city.title()
            break
    
    return entities

def validate_email(email: str) -> bool:
    """Email formatını doğrula"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Metni belirli uzunlukta kes"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Dictionary'den güvenli şekilde değer al"""
    return dictionary.get(key, default)

def is_valid_uuid(uuid_string: str) -> bool:
    """UUID formatını doğrula"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def format_response(success: bool, message: str, data: Any = None) -> Dict[str, Any]:
    """Standart API yanıt formatı"""
    response = {
        "success": success,
        "message": message,
        "timestamp": get_current_timestamp().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response 
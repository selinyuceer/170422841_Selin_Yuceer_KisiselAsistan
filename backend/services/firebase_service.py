import os
import logging
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        self.db = None
        self.is_initialized = False
        self._initialize()
    
    def _initialize(self):
        """Firebase'i başlat"""
        try:
            # Service account key dosyasının yolunu al
            key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
            
            if key_path and os.path.exists(key_path):
                # Service account key ile başlat
                credentials = service_account.Credentials.from_service_account_file(key_path)
                self.db = firestore.Client(credentials=credentials)
                self.is_initialized = True
                logger.info("Firebase initialized with service account key")
            else:
                logger.warning("Firebase credentials not found. Using default credentials.")
                try:
                    # Varsayılan credentials ile dene
                    self.db = firestore.Client()
                    self.is_initialized = True
                    logger.info("Firebase initialized with default credentials")
                except Exception as e:
                    logger.error(f"Firebase initialization failed: {e}")
                    self.is_initialized = False
                    
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            self.is_initialized = False
    
    def is_available(self) -> bool:
        """Firebase kullanılabilir mi?"""
        return self.is_initialized and self.db is not None
    
    # NOTES OPERATIONS
    def create_note(self, title: str, content: str, user_id: str = "default") -> Optional[str]:
        """Not oluştur"""
        if not self.is_available():
            return None
            
        try:
            doc_ref = self.db.collection('notes').document()
            doc_ref.set({
                'title': title,
                'content': content,
                'user_id': user_id,
                'is_voice_note': False,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Note created with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return None
    
    def get_notes(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Notları getir"""
        if not self.is_available():
            return []
            
        try:
            notes_ref = self.db.collection('notes')
            if user_id:
                notes_ref = notes_ref.where('user_id', '==', user_id)
            notes_ref = notes_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            docs = notes_ref.stream()
            
            notes = []
            for doc in docs:
                note_data = doc.to_dict()
                note_data['id'] = doc.id
                # Timestamp'i string'e çevir
                if 'created_at' in note_data and note_data['created_at']:
                    note_data['created_at'] = note_data['created_at'].isoformat()
                if 'updated_at' in note_data and note_data['updated_at']:
                    note_data['updated_at'] = note_data['updated_at'].isoformat()
                notes.append(note_data)
            
            return notes
        except Exception as e:
            logger.error(f"Error getting notes: {e}")
            return []
    
    def update_note(self, note_id: str, title: str = None, content: str = None) -> bool:
        """Not güncelle"""
        if not self.is_available():
            return False
            
        try:
            update_data = {'updated_at': firestore.SERVER_TIMESTAMP}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content
                
            self.db.collection('notes').document(note_id).update(update_data)
            logger.info(f"Note updated: {note_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            return False
    
    def delete_note(self, note_id: str) -> bool:
        """Not sil"""
        if not self.is_available():
            return False
            
        try:
            self.db.collection('notes').document(note_id).delete()
            logger.info(f"Note deleted: {note_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return False
    
    # CALENDAR EVENTS OPERATIONS
    def create_event(self, title: str, datetime_str: str, description: str = "", user_id: str = "default") -> Optional[str]:
        """Etkinlik oluştur"""
        if not self.is_available():
            return None
            
        try:
            doc_ref = self.db.collection('events').document()
            doc_ref.set({
                'title': title,
                'datetime': datetime_str,
                'description': description,
                'user_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Event created with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    def get_events(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Tüm etkinlikleri getir"""
        if not self.is_available():
            return []
            
        try:
            events_ref = self.db.collection('events')
            if user_id:
                events_ref = events_ref.where('user_id', '==', user_id)
            events_ref = events_ref.order_by('datetime')
            
            docs = events_ref.stream()
            
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                # Timestamp'i string'e çevir
                if 'created_at' in event_data and event_data['created_at']:
                    event_data['created_at'] = event_data['created_at'].isoformat()
                events.append(event_data)
            
            return events
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def update_event(self, event_id: str, title: str = None, datetime_str: str = None, description: str = None) -> bool:
        """Etkinlik güncelle"""
        if not self.is_available():
            return False
            
        try:
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if datetime_str is not None:
                update_data['datetime'] = datetime_str
            if description is not None:
                update_data['description'] = description
                
            if update_data:
                self.db.collection('events').document(event_id).update(update_data)
                logger.info(f"Event updated: {event_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """Etkinlik sil"""
        if not self.is_available():
            return False
            
        try:
            self.db.collection('events').document(event_id).delete()
            logger.info(f"Event deleted: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    # CHAT MESSAGES OPERATIONS
    def save_chat_message(self, message: str, response: str, user_id: str = "default", intent: str = "chat") -> Optional[str]:
        """Chat mesajını kaydet"""
        if not self.is_available():
            return None
            
        try:
            doc_ref = self.db.collection('chat_messages').document()
            doc_ref.set({
                'user_message': message,
                'ai_response': response,
                'user_id': user_id,
                'intent': intent,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Chat message saved with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return None
    
    def get_chat_history(self, user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """Chat geçmişini getir"""
        if not self.is_available():
            return []
            
        try:
            messages_ref = self.db.collection('chat_messages')
            if user_id:
                messages_ref = messages_ref.where('user_id', '==', user_id)
            messages_ref = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = messages_ref.stream()
            
            messages = []
            for doc in docs:
                message_data = doc.to_dict()
                message_data['id'] = doc.id
                # Timestamp'i string'e çevir
                if 'timestamp' in message_data and message_data['timestamp']:
                    message_data['timestamp'] = message_data['timestamp'].isoformat()
                messages.append(message_data)
            
            # Eski mesajları önce göstermek için ters çevir
            return list(reversed(messages))
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def delete_chat_history(self, user_id: str = "default") -> bool:
        """Chat geçmişini sil"""
        if not self.is_available():
            return False
            
        try:
            messages_ref = self.db.collection('chat_messages')
            if user_id:
                messages_ref = messages_ref.where('user_id', '==', user_id)
            
            docs = messages_ref.stream()
            for doc in docs:
                doc.reference.delete()
            
            logger.info(f"Chat history deleted for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat history: {e}")
            return False
    
    # REMINDERS OPERATIONS
    def create_reminder(self, title: str, description: str, reminder_time: str, user_id: str = "default") -> Optional[str]:
        """Hatırlatıcı oluştur"""
        if not self.is_available():
            return None
            
        try:
            doc_ref = self.db.collection('reminders').document()
            doc_ref.set({
                'title': title,
                'description': description,
                'reminder_time': reminder_time,
                'user_id': user_id,
                'is_completed': False,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Reminder created with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return None
    
    def get_reminders(self, user_id: str = None, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Hatırlatıcıları getir"""
        if not self.is_available():
            return []
            
        try:
            reminders_ref = self.db.collection('reminders')
            if user_id:
                reminders_ref = reminders_ref.where('user_id', '==', user_id)
            if not include_completed:
                reminders_ref = reminders_ref.where('is_completed', '==', False)
            reminders_ref = reminders_ref.order_by('reminder_time')
            
            docs = reminders_ref.stream()
            
            reminders = []
            for doc in docs:
                reminder_data = doc.to_dict()
                reminder_data['id'] = doc.id
                # Timestamp'i string'e çevir
                if 'created_at' in reminder_data and reminder_data['created_at']:
                    reminder_data['created_at'] = reminder_data['created_at'].isoformat()
                reminders.append(reminder_data)
            
            return reminders
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    def update_reminder(self, reminder_id: str, title: str = None, description: str = None, 
                       reminder_time: str = None, is_completed: bool = None) -> bool:
        """Hatırlatıcı güncelle"""
        if not self.is_available():
            return False
            
        try:
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if description is not None:
                update_data['description'] = description
            if reminder_time is not None:
                update_data['reminder_time'] = reminder_time
            if is_completed is not None:
                update_data['is_completed'] = is_completed
                
            if update_data:
                self.db.collection('reminders').document(reminder_id).update(update_data)
                logger.info(f"Reminder updated: {reminder_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Hatırlatıcı sil"""
        if not self.is_available():
            return False
            
        try:
            self.db.collection('reminders').document(reminder_id).delete()
            logger.info(f"Reminder deleted: {reminder_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False
    
    # WEATHER CACHE OPERATIONS (Opsiyonel)
    def cache_weather_data(self, city: str, weather_data: Dict[str, Any], ttl_minutes: int = 30) -> bool:
        """Hava durumu verilerini önbelleğe al"""
        if not self.is_available():
            return False
            
        try:
            from datetime import timedelta
            expire_time = datetime.now() + timedelta(minutes=ttl_minutes)
            
            doc_ref = self.db.collection('weather_cache').document(city.lower())
            doc_ref.set({
                'city': city,
                'data': weather_data,
                'cached_at': firestore.SERVER_TIMESTAMP,
                'expires_at': expire_time
            })
            logger.info(f"Weather data cached for city: {city}")
            return True
        except Exception as e:
            logger.error(f"Error caching weather data: {e}")
            return False
    
    def get_cached_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Önbelleğe alınmış hava durumu verilerini getir"""
        if not self.is_available():
            return None
            
        try:
            doc_ref = self.db.collection('weather_cache').document(city.lower())
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                expire_time = data.get('expires_at')
                
                # Önbellek süresi dolmuş mu kontrol et
                if expire_time and datetime.now() < expire_time:
                    return data.get('data')
                else:
                    # Süresi dolmuş önbelleği sil
                    doc_ref.delete()
                    logger.info(f"Expired weather cache deleted for city: {city}")
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached weather data: {e}")
            return None

# Global Firebase service instance
firebase_service = FirebaseService() 
import axios from 'axios';

// API Base URL - Geliştirme ortamı için
const API_BASE_URL = 'http://192.168.87.159:8000';

// Axios instance oluştur
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 saniye timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// API servisleri
export const apiService = {
  // Health check
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('Sunucu bağlantısı kurulamadı');
    }
  },

  // Chat API
  async sendMessage(message) {
    try {
      console.log('Sending message:', message);
      console.log('API URL:', `${API_BASE_URL}/api/chat/message`);
      
      // Chat için özel timeout (45 saniye)
      const response = await apiClient.post('/api/chat/message', {
        message: message,
      }, {
        timeout: 45000
      });
      
      console.log('Response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('İstek zaman aşımına uğradı. Lütfen tekrar deneyin.');
      }
      
      throw new Error('Mesaj gönderilemedi');
    }
  },

  // Audio Message API
  async sendAudioMessage(audioUri, userId = 'default') {
    try {
      console.log('Sending audio message:', audioUri);
      console.log('API URL:', `${API_BASE_URL}/api/chat/audio-message`);
      
      // FormData oluştur
      const formData = new FormData();
      formData.append('file', {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'audio_message.m4a',
      });
      formData.append('user_id', userId);
      
      // Ses mesajı için özel timeout (60 saniye)
      const response = await axios.post(`${API_BASE_URL}/api/chat/audio-message`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000
      });
      
      console.log('Audio response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('Audio API Error:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Ses mesajı zaman aşımına uğradı. Lütfen tekrar deneyin.');
      }
      
      throw new Error('Sesli mesaj gönderilemedi');
    }
  },

  // Chat History API
  async getChatHistory(userId = 'default', limit = 50) {
    try {
      const response = await apiClient.get(`/api/chat/history/${userId}`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw new Error('Chat geçmişi alınamadı');
    }
  },

  async deleteChatHistory(userId = 'default') {
    try {
      const response = await apiClient.delete(`/api/chat/history/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error('Chat geçmişi silinemedi');
    }
  },

  // Notes API
  async getNotes() {
    try {
      const response = await apiClient.get('/api/notes/');
      return response.data;
    } catch (error) {
      throw new Error('Notlar alınamadı');
    }
  },

  async createNote(title, content) {
    try {
      const response = await apiClient.post('/api/notes/', null, {
        params: {
          title: title,
          content: content,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Not oluşturulamadı');
    }
  },

  async deleteNote(noteId) {
    try {
      const response = await apiClient.delete(`/api/notes/${noteId}`);
      return response.data;
    } catch (error) {
      throw new Error('Not silinemedi');
    }
  },

  async updateNote(noteId, title, content) {
    try {
      const response = await apiClient.put(`/api/notes/${noteId}`, {
        title: title,
        content: content,
      });
      return response.data;
    } catch (error) {
      throw new Error('Not güncellenemedi');
    }
  },

  // Takvim API
  async getCalendarEvents() {
    try {
      const response = await apiClient.get('/api/calendar/events');
      return response.data;
    } catch (error) {
      throw new Error('Takvim etkinlikleri alınamadı');
    }
  },

  async createCalendarEvent(title, datetime, description = '') {
    try {
      const response = await apiClient.post('/api/calendar/events', {
        title: title,
        datetime: datetime,
        description: description,
      });
      return response.data;
    } catch (error) {
      throw new Error('Takvim etkinliği oluşturulamadı');
    }
  },

  async deleteCalendarEvent(eventId) {
    try {
      const response = await apiClient.delete(`/api/calendar/events/${eventId}`);
      return response.data;
    } catch (error) {
      throw new Error('Takvim etkinliği silinemedi');
    }
  },

  async getUserEvents(userId, startDate = null, endDate = null) {
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await apiClient.get(`/api/calendar/events/${userId}`, { params });
      return response.data;
    } catch (error) {
      throw new Error('Kullanıcı etkinlikleri alınamadı');
    }
  },

  async getTodayEvents(userId) {
    try {
      const response = await apiClient.get(`/api/calendar/events/today/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error('Bugünkü etkinlikler alınamadı');
    }
  },

  async getUpcomingEvents(userId, days = 7) {
    try {
      const response = await apiClient.get(`/api/calendar/events/upcoming/${userId}`, {
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw new Error('Yaklaşan etkinlikler alınamadı');
    }
  },

  // Reminders API
  async getReminders(userId = 'default', includeCompleted = false) {
    try {
      const response = await apiClient.get('/api/reminders/', {
        params: {
          user_id: userId,
          include_completed: includeCompleted
        }
      });
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcılar alınamadı');
    }
  },

  async createReminder(title, description, reminderTime, userId = 'default') {
    try {
      const response = await apiClient.post('/api/reminders/create', {
        title: title,
        description: description,
        reminder_time: reminderTime,
        user_id: userId
      });
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı oluşturulamadı');
    }
  },

  async getReminder(reminderId) {
    try {
      const response = await apiClient.get(`/api/reminders/${reminderId}`);
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı alınamadı');
    }
  },

  async updateReminder(reminderId, title, description, reminderTime, userId = 'default') {
    try {
      const response = await apiClient.put(`/api/reminders/${reminderId}`, {
        title: title,
        description: description,
        reminder_time: reminderTime,
        user_id: userId
      });
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı güncellenemedi');
    }
  },

  async completeReminder(reminderId) {
    try {
      const response = await apiClient.patch(`/api/reminders/${reminderId}/complete`);
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı tamamlanamadı');
    }
  },

  async deleteReminder(reminderId) {
    try {
      const response = await apiClient.delete(`/api/reminders/${reminderId}`);
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı silinemedi');
    }
  },

  async getActiveReminders(userId = 'default') {
    try {
      const response = await apiClient.get(`/api/reminders/user/${userId}/active`);
      return response.data;
    } catch (error) {
      throw new Error('Aktif hatırlatıcılar alınamadı');
    }
  },

  async getUpcomingReminders(userId = 'default', hours = 24) {
    try {
      const response = await apiClient.get(`/api/reminders/user/${userId}/upcoming`, {
        params: { hours }
      });
      return response.data;
    } catch (error) {
      throw new Error('Yaklaşan hatırlatıcılar alınamadı');
    }
  },

  // Weather API
  async getWeather(city = 'Istanbul') {
    try {
      const response = await apiClient.get('/api/weather/', {
        params: { city }
      });
      return response.data;
    } catch (error) {
      throw new Error('Hava durumu alınamadı');
    }
  }
};

export default apiService; 
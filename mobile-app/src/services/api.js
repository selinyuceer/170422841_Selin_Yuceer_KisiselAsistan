import axios from 'axios';

// Backend API base URL - telefon için IP adresi kullan
const API_BASE_URL = 'http://192.168.1.102:8000';

// API client oluştur
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 saniye timeout (Gemini API için)
  headers: {
    'Content-Type': 'application/json',
  },
});

// API servis fonksiyonları
export const apiService = {
  // Sağlık kontrolü
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('Backend bağlantısı kurulamadı');
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

  // Intent analizi
  async analyzeIntent(message) {
    try {
      const response = await apiClient.post('/api/chat/analyze-intent', {
        message: message,
      });
      return response.data;
    } catch (error) {
      throw new Error('Intent analizi yapılamadı');
    }
  },

  // Notlar API
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
      const response = await apiClient.post(`/api/notes/?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`);
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

  // Hatırlatıcılar API
  async getReminders() {
    try {
      const response = await apiClient.get('/api/reminders');
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcılar alınamadı');
    }
  },

  async createReminder(title, datetime, description = '') {
    try {
      const response = await apiClient.post('/api/reminders', {
        title: title,
        datetime: datetime,
        description: description,
      });
      return response.data;
    } catch (error) {
      throw new Error('Hatırlatıcı oluşturulamadı');
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

  // Hava durumu API
  async getWeather(city = 'Istanbul') {
    try {
      const response = await apiClient.get(`/api/weather/?city=${city}`);
      return response.data;
    } catch (error) {
      throw new Error('Hava durumu bilgisi alınamadı');
    }
  },
};

export default apiService; 
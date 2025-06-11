# Kişisel Asistan Backend API

Bu proje, Gemini AI tabanlı kişisel asistan uygulamasının backend API'sidir.

## 🚀 Özellikler

- **Gemini AI Entegrasyonu**: Google Gemini Pro modeli ile doğal dil işleme
- **Sesli Komut Desteği**: Kullanıcı mesajlarının intent analizi
- **Not Yönetimi**: Sesli ve yazılı not alma, listeleme, silme
- **Hatırlatıcı Sistemi**: Zamanlı hatırlatıcılar oluşturma ve yönetme
- **Takvim Entegrasyonu**: Etkinlik oluşturma ve yönetme
- **Hava Durumu**: OpenWeatherMap API ile güncel hava durumu
- **RESTful API**: FastAPI ile modern API yapısı

## 📋 Gereksinimler

- Python 3.9+
- Google Gemini API anahtarı
- OpenWeatherMap API anahtarı (isteğe bağlı)

## 🛠️ Kurulum

### 1. Bağımlılıkları Yükleyin

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables Ayarlayın

`.env` dosyası oluşturun:

```env
# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# OpenWeatherMap (isteğe bağlı)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. API Anahtarlarını Alın

#### Gemini API Anahtarı (Zorunlu)
1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine gidin
2. Yeni API anahtarı oluşturun
3. Anahtarı `.env` dosyasına ekleyin

#### OpenWeatherMap API Anahtarı (İsteğe Bağlı)
1. [OpenWeatherMap](https://openweathermap.org/api) adresine gidin
2. Ücretsiz hesap oluşturun
3. API anahtarını alın ve `.env` dosyasına ekleyin

## 🏃‍♂️ Çalıştırma

### Geliştirme Modu

```bash
# Yöntem 1: Start scripti ile
python start.py

# Yöntem 2: Doğrudan uvicorn ile
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Yöntem 3: Python modülü olarak
python -m uvicorn main:app --reload
```

### Prodüksiyon Modu

```bash
# DEBUG=False olarak ayarlayın
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 API Dokümantasyonu

Sunucu çalıştıktan sonra:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Test Etme

### Otomatik Test

```bash
python test_api.py
```

### Manuel Test

```bash
# Sağlık kontrolü
curl http://localhost:8000/health

# Chat testi
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Merhaba", "user_id": "test_user"}'
```

## 📁 Proje Yapısı

```
backend/
├── main.py                 # Ana FastAPI uygulaması
├── start.py               # Başlatma scripti
├── test_api.py           # Test scripti
├── requirements.txt      # Python bağımlılıkları
├── .env                  # Environment variables (oluşturulacak)
├── routers/              # API endpoint'leri
│   ├── __init__.py
│   ├── chat.py          # Chat API
│   ├── notes.py         # Notlar API
│   ├── reminders.py     # Hatırlatıcılar API
│   ├── calendar.py      # Takvim API
│   └── weather.py       # Hava durumu API
├── services/            # İş mantığı servisleri
│   ├── __init__.py
│   └── gemini_service.py # Gemini AI servisi
├── models/              # Veri modelleri
│   ├── __init__.py
│   └── schemas.py       # Pydantic şemaları
└── utils/               # Yardımcı fonksiyonlar
    ├── __init__.py
    └── helpers.py       # Genel yardımcılar
```

## 🔌 API Endpoint'leri

### Chat API
- `POST /api/chat/message` - Mesaj gönder
- `POST /api/chat/analyze-intent` - Intent analizi
- `GET /api/chat/health` - Chat servisi durumu

### Notes API
- `POST /api/notes/create` - Not oluştur
- `GET /api/notes/list/{user_id}` - Notları listele
- `GET /api/notes/{note_id}` - Not detayı
- `DELETE /api/notes/{note_id}` - Not sil

### Reminders API
- `POST /api/reminders/create` - Hatırlatıcı oluştur
- `GET /api/reminders/list/{user_id}` - Hatırlatıcıları listele
- `PUT /api/reminders/{reminder_id}/complete` - Hatırlatıcıyı tamamla
- `DELETE /api/reminders/{reminder_id}` - Hatırlatıcı sil
- `GET /api/reminders/upcoming/{user_id}` - Yaklaşan hatırlatıcılar

### Calendar API
- `POST /api/calendar/create-event` - Etkinlik oluştur
- `GET /api/calendar/events/{user_id}` - Etkinlikleri listele
- `GET /api/calendar/events/today/{user_id}` - Bugünkü etkinlikler
- `GET /api/calendar/events/upcoming/{user_id}` - Yaklaşan etkinlikler
- `PUT /api/calendar/events/{event_id}` - Etkinlik güncelle
- `DELETE /api/calendar/events/{event_id}` - Etkinlik sil

### Weather API
- `POST /api/weather/current` - Güncel hava durumu
- `GET /api/weather/cities/{city_name}` - Şehir arama

## 🔧 Yapılandırma

### Environment Variables

| Değişken | Açıklama | Zorunlu | Varsayılan |
|----------|----------|---------|------------|
| `GEMINI_API_KEY` | Google Gemini API anahtarı | Evet | - |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API anahtarı | Hayır | - |
| `HOST` | Sunucu adresi | Hayır | `0.0.0.0` |
| `PORT` | Sunucu portu | Hayır | `8000` |
| `DEBUG` | Debug modu | Hayır | `True` |

### Gemini AI Ayarları

`services/gemini_service.py` dosyasında:

```python
generation_config = {
    "temperature": 0.7,      # Yaratıcılık seviyesi (0.0-1.0)
    "top_p": 0.8,           # Nucleus sampling
    "top_k": 40,            # Top-k sampling
    "max_output_tokens": 1024, # Maksimum çıktı uzunluğu
}
```

## 🚨 Hata Ayıklama

### Yaygın Hatalar

1. **Gemini API Hatası**
   ```
   ValueError: GEMINI_API_KEY environment variable is required
   ```
   **Çözüm**: `.env` dosyasında `GEMINI_API_KEY` değerini ayarlayın.

2. **Port Kullanımda**
   ```
   OSError: [Errno 48] Address already in use
   ```
   **Çözüm**: Farklı port kullanın veya çalışan servisi durdurun.

3. **Modül Bulunamadı**
   ```
   ModuleNotFoundError: No module named 'fastapi'
   ```
   **Çözüm**: `pip install -r requirements.txt` komutunu çalıştırın.

### Log Seviyeleri

- **DEBUG**: Detaylı debug bilgileri
- **INFO**: Genel bilgi mesajları
- **WARNING**: Uyarı mesajları
- **ERROR**: Hata mesajları

## 🔒 Güvenlik

- API anahtarlarını asla kod içinde saklamayın
- Production'da `DEBUG=False` ayarlayın
- CORS ayarlarını production için kısıtlayın
- Rate limiting ekleyin (gelecek sürümlerde)

## 📈 Performans

- Gemini API çağrıları cache'lenebilir
- Database connection pooling kullanın
- Async/await pattern'i kullanılıyor
- Request/response logging mevcut

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👥 İletişim

- **Geliştirici**: Selin Yüceer
- **Danışman**: Dr. Öğr. Üyesi Ali Sarıkaş
- **Üniversite**: Marmara Üniversitesi Teknoloji Fakültesi 
# Sesli Komut ve Doğal Dil İşleme Tabanlı Mobil Kişisel Asistan

Bu proje, Marmara Üniversitesi Teknoloji Fakültesi Bilgisayar Mühendisliği Bölümü bitirme projesi kapsamında geliştirilmektedir.

## Proje Yapısı

```
├── backend/          # Python FastAPI Backend
├── mobile/           # React Native Mobil Uygulama
├── docs/            # Dokümantasyon
└── README.md
```

## Teknolojiler

### Backend
- Python 3.9+
- FastAPI
- Google Gemini AI
- Firebase Firestore
- OpenWeatherMap API
- Google Calendar API

### Mobil Uygulama
- React Native
- react-native-voice
- react-native-tts

## Kurulum

### Backend Kurulumu
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Mobil Uygulama Kurulumu
```bash
cd mobile
npm install
npx react-native run-android  # Android için
npx react-native run-ios      # iOS için
```

## Geliştirici
- **Öğrenci**: Selin Yüceer
- **Danışman**: Dr. Öğr. Üyesi Ali Sarıkaş
- **Üniversite**: Marmara Üniversitesi Teknoloji Fakültesi 
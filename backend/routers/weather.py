from fastapi import APIRouter, HTTPException
from models.schemas import WeatherRequest, WeatherResponse
import requests
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_weather_by_city(city: str = "Istanbul"):
    """
    Şehir adına göre hava durumu getir (GET endpoint)
    """
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenWeather API anahtarı yapılandırılmamış"
            )
        
        # OpenWeatherMap API URL'i
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # Parametreler
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",  # Celsius için
            "lang": "tr"  # Türkçe açıklamalar
        }
        
        # API çağrısı
        response = requests.get(base_url, params=params)
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Şehir bulunamadı"
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Hava durumu bilgisi alınamadı"
            )
        
        data = response.json()
        
        # Yanıt oluştur
        weather_data = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": round(data["main"]["temp"], 1),
            "condition": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data["wind"]["speed"], 1),
            "pressure": data["main"]["pressure"],
            "feels_like": round(data["main"]["feels_like"], 1),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Weather data retrieved for: {city}")
        return weather_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hava durumu bilgisi alınırken hata oluştu"
        )

@router.post("/current", response_model=WeatherResponse)
async def get_current_weather(request: WeatherRequest):
    """
    Güncel hava durumu bilgisi getir
    """
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenWeather API anahtarı yapılandırılmamış"
            )
        
        # OpenWeatherMap API URL'i
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # Parametreler
        params = {
            "q": f"{request.city},{request.country_code}" if request.country_code else request.city,
            "appid": api_key,
            "units": "metric",  # Celsius için
            "lang": "tr"  # Türkçe açıklamalar
        }
        
        # API çağrısı
        response = requests.get(base_url, params=params)
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Şehir bulunamadı"
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Hava durumu bilgisi alınamadı"
            )
        
        data = response.json()
        
        # Yanıt oluştur
        weather_response = WeatherResponse(
            city=data["name"],
            country=data["sys"]["country"],
            temperature=round(data["main"]["temp"], 1),
            description=data["weather"][0]["description"].title(),
            humidity=data["main"]["humidity"],
            wind_speed=round(data["wind"]["speed"], 1),
            pressure=data["main"]["pressure"],
            timestamp=datetime.now()
        )
        
        logger.info(f"Weather data retrieved for: {request.city}")
        return weather_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Hava durumu bilgisi alınırken hata oluştu"
        )

@router.get("/cities/{city_name}")
async def search_cities(city_name: str):
    """
    Şehir arama (otomatik tamamlama için)
    """
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenWeather API anahtarı yapılandırılmamış"
            )
        
        # Geocoding API ile şehir arama
        base_url = "http://api.openweathermap.org/geo/1.0/direct"
        
        params = {
            "q": city_name,
            "limit": 5,
            "appid": api_key
        }
        
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Şehir arama yapılamadı"
            )
        
        cities = response.json()
        
        # Sonuçları formatla
        formatted_cities = [
            {
                "name": city["name"],
                "country": city["country"],
                "state": city.get("state", ""),
                "lat": city["lat"],
                "lon": city["lon"]
            }
            for city in cities
        ]
        
        return {
            "query": city_name,
            "cities": formatted_cities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"City search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Şehir arama yapılırken hata oluştu"
        ) 
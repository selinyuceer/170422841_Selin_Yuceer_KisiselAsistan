from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging

# Routers
from routers import chat, notes, calendar, weather, reminders

# Services
from services.firebase_service import firebase_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kişisel Asistan API",
    description="Sesli komut ve doğal dil işleme tabanlı mobil kişisel asistan backend API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da specific origins kullanın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])

@app.get("/")
async def root():
    """Ana endpoint - API durumu"""
    return {
        "message": "Kişisel Asistan API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    return {
        "status": "healthy",
        "message": "API çalışıyor"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global hata yakalayıcı"""
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Sunucu hatası oluştu", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 
import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # FFmpeg path'ini kontrol et
        AudioSegment.converter = which("ffmpeg")
        AudioSegment.ffmpeg = which("ffmpeg")
        AudioSegment.ffprobe = which("ffprobe")
    
    async def transcribe_audio(self, file: UploadFile, language: str = "tr-TR") -> str:
        """
        UploadFile objesi ile ses dosyasını metne dönüştürür
        """
        temp_file_path = None
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1] if '.' in file.filename else 'wav'}") as temp_file:
                temp_file_path = temp_file.name
                # Ses dosyasını geçici dosyaya yaz
                file_content = await file.read()
                temp_file.write(file_content)
            
            logger.info(f"Audio file saved to: {temp_file_path}")
            
            # Ses dosyasını metne dönüştür
            text = self.speech_to_text(temp_file_path, language)
            return text
            
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {str(e)}")
            return None
        finally:
            # Geçici dosyayı temizle
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
        
    def convert_audio_to_wav(self, audio_file_path: str) -> str:
        """
        Ses dosyasını WAV formatına dönüştürür
        """
        try:
            # Ses dosyasını yükle
            audio = AudioSegment.from_file(audio_file_path)
            
            # WAV formatında geçici dosya oluştur
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                wav_path = temp_wav.name
                
            # WAV formatında kaydet
            audio.export(wav_path, format="wav")
            logger.info(f"Audio converted to WAV: {wav_path}")
            return wav_path
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            raise Exception(f"Ses dosyası dönüştürme hatası: {str(e)}")
    
    def speech_to_text(self, audio_file_path: str, language: str = "tr-TR") -> str:
        """
        Ses dosyasını metne dönüştürür
        """
        wav_path = None
        try:
            # Ses dosyasını WAV formatına dönüştür
            wav_path = self.convert_audio_to_wav(audio_file_path)
            
            # Ses dosyasını aç
            with sr.AudioFile(wav_path) as source:
                # Gürültüyü azalt
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Ses verisini oku
                audio_data = self.recognizer.record(source)
            
            # Google Speech Recognition kullanarak metne dönüştür
            try:
                text = self.recognizer.recognize_google(audio_data, language=language)
                logger.info(f"Speech to text successful: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Speech recognition could not understand audio")
                return "Ses anlaşılamadı. Lütfen daha net konuşun."
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {str(e)}")
                return "Ses tanıma servisi hatası. Lütfen tekrar deneyin."
                
        except Exception as e:
            logger.error(f"Error in speech to text: {str(e)}")
            raise Exception(f"Ses tanıma hatası: {str(e)}")
        finally:
            # Geçici WAV dosyasını sil
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except:
                    pass
    
    def cleanup_temp_file(self, file_path: str):
        """
        Geçici dosyayı temizler
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary file {file_path}: {str(e)}")

# Global audio service instance
audio_service = AudioService() 
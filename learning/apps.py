from django.apps import AppConfig
from decouple import config
import mongoengine 
import logging
from django.conf import settings
import os

# Set logging level for better visibility
logger = logging.getLogger(__name__)

def connect_mongoengine():
    """
    Hàm kết nối an toàn cho môi trường Gunicorn/forking và Local.
    """
    try:
        # Trong MongoEngine, connect() sẽ tự động ngắt kết nối cũ nếu cùng alias.
        # Tuy nhiên, để an toàn hơn, chúng ta gọi disconnect rõ ràng.
        try:
            mongoengine.disconnect(alias='default') 
            logger.info("Disconnected old MongoEngine connection (if it existed).")
        except Exception:
            # Bỏ qua nếu không thể disconnect (vì nó chưa connect)
            pass

        mongo_uri = settings.MONGO_URI
        
        # Thiết lập kết nối mới
        mongoengine.connect(
            host=mongo_uri, 
            alias='default', 
            maxPoolSize=50, 
            serverSelectionTimeoutMS=5000,
        )
        
        logger.info("MongoEngine connected successfully.")

    except Exception as e:
        # Nếu kết nối thất bại, log lỗi chi tiết
        logger.error(f"Failed to connect MongoEngine: {e}")
        # Reraise exception nếu không phải do Autoreloader để đảm bảo lỗi được thấy
        if 'You have not defined a default connection' in str(e):
             logger.error("HINT: MONGO_URI might be incorrect or missing.")

class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    
    def ready(self):
        """
        Thiết lập kết nối an toàn sau khi Django đã sẵn sàng.
        """
        # Kiểm tra nếu đây là process chính của Autoreloader
        is_reloader_process = os.environ.get('RUN_MAIN') == 'true'
        
        if settings.DEBUG:
            # Ở chế độ DEBUG, chỉ kết nối trong process chính (không phải reloader phụ)
            if is_reloader_process or not os.environ.get('RUN_MAIN'):
                connect_mongoengine()
        else:
            # Ở Production, kết nối ngay lập tức
            connect_mongoengine()
            
        # Import documents sau khi kết nối đã sẵn sàng
        try:
            from . import documents 
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")

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
    Hàm kết nối an toàn cho môi trường Local (runserver).
    """
    try:
        # Ngắt kết nối cũ nếu có
        try:
            mongoengine.disconnect(alias='default') 
            logger.info("Disconnected old MongoEngine connection (if it existed).")
        except Exception:
            pass

        mongo_uri = settings.MONGO_URI
        
        # Thiết lập kết nối mới
        mongoengine.connect(
            host=mongo_uri, 
            alias='default', 
            maxPoolSize=50, 
            serverSelectionTimeoutMS=5000,
            readPreference='secondaryPreferred' 
        )
        
        logger.info("MongoEngine connected successfully.")

    except Exception as e:
        logger.error(f"Failed to connect MongoEngine: {e}")
        # Không raise exception ở đây để Django Autoreloader có thể tiếp tục
        # Trong Production, lỗi này sẽ được xử lý bởi Gunicorn/post_fork.
        pass

class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    
    def ready(self):
        """
        Thiết lập kết nối. Chỉ kết nối trong runserver, không kết nối trong Gunicorn/Production.
        Gunicorn sẽ sử dụng hook `post_fork` để kết nối an toàn.
        """
        # Kiểm tra nếu chúng ta đang chạy trong môi trường Django Development Server (runserver)
        # Bằng cách kiểm tra sự tồn tại của biến môi trường do runserver tạo ra.
        is_running_main = os.environ.get('RUN_MAIN') or os.environ.get('WERKZEUG_RUN_MAIN')
        
        if settings.DEBUG and is_running_main:
            # Chỉ kết nối ở local development server (chỉ 1 lần trong master process của runserver)
            connect_mongoengine()
            
        # Import documents
        try:
            from . import documents 
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")

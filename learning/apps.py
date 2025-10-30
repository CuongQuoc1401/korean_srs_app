from django.apps import AppConfig
from decouple import config
import mongoengine
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def connect_mongoengine():
    """
    Hàm này được gọi bởi mỗi Gunicorn worker để thiết lập kết nối MongoEngine
    một cách an toàn trong môi trường đa luồng.
    """
    try:
        # Nếu đã có kết nối 'default' và nó đang mở, đóng nó.
        # Điều này là rất quan trọng trong môi trường Gunicorn/forking.
        if 'default' in mongoengine.connections._connections:
            try:
                mongoengine.disconnect(alias='default')
                logger.info("Disconnected old MongoEngine connection.")
            except Exception:
                # Bỏ qua lỗi nếu việc ngắt kết nối thất bại
                pass

        # Lấy MONGO_URI từ settings.py
        mongo_uri = settings.MONGO_URI
        
        # Thiết lập kết nối mới
        mongoengine.connect(
            host=mongo_uri, 
            alias='default', 
            # Đảm bảo kết nối được thiết lập ngay lập tức
            connect=True,
            # Tùy chọn để tối ưu hóa kết nối
            maxPoolSize=50, 
            serverSelectionTimeoutMS=5000,
        )
        
        logger.info("MongoEngine connected successfully to new process.")

    except Exception as e:
        logger.error(f"Failed to connect MongoEngine in worker process: {e}")

class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    
    def ready(self):
        """
        Đây là nơi an toàn nhất để thiết lập kết nối MongoEngine. 
        Nó đảm bảo kết nối được thiết lập sau khi Django đã sẵn sàng.
        """
        if not settings.DEBUG:
            # Trong Production (Render): Gọi kết nối an toàn cho mỗi process/worker
            connect_mongoengine()
        else:
            # Trong chế độ DEBUG (Local runserver): 
            # Dùng logic kiểm tra autoreload để tránh kết nối hai lần, 
            # dù việc này không bắt buộc nhưng giữ lại cho hiệu suất.
            import os
            is_master = os.environ.get('RUN_MAIN') or os.environ.get('DJANGO_SETTINGS_MODULE')
            if is_master:
                connect_mongoengine()

        # Import các models/documents sau khi kết nối đã sẵn sàng
        try:
            # Import documents để các models được register với MongoEngine
            from . import documents 
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")

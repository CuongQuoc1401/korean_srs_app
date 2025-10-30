from django.apps import AppConfig
from decouple import config
import mongoengine
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Đặt biến cờ (flag) để theo dõi trạng thái kết nối
_is_connected = False

def connect_mongoengine():
    global _is_connected
    # Chỉ kết nối nếu chưa được kết nối
    if not _is_connected:
        try:
            # Lấy MONGO_URI từ settings.py
            mongo_uri = settings.MONGO_URI
            
            # Kết nối an toàn (dùng alias 'default' đã định nghĩa trong settings)
            mongoengine.connect(host=mongo_uri, alias='default', connect=False)
            
            # Kiểm tra kết nối và thiết lập kết nối thực tế
            mongoengine.get_connection('default').connect()
            
            _is_connected = True
            logger.info("MongoEngine connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect MongoEngine: {e}")
            # Nếu kết nối thất bại, _is_connected vẫn là False

class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    
    def ready(self):
        """
        Đây là nơi an toàn nhất để thiết lập kết nối MongoEngine. 
        Nó đảm bảo kết nối được thiết lập sau khi Django đã sẵn sàng.
        """
        if not settings.DEBUG:
            # Trong Production, kết nối ngay lập tức
            connect_mongoengine()
        else:
            # Trong chế độ DEBUG, cần thận trọng hơn với Autoreloader
            import os
            # Django Autoreloader chạy `ready()` hai lần. Chỉ chạy kết nối ở lần thứ nhất.
            is_master = os.environ.get('RUN_MAIN') or os.environ.get('DJANGO_SETTINGS_MODULE')
            if is_master:
                connect_mongoengine()

        # Import các models/documents sau khi kết nối đã sẵn sàng
        try:
            from . import documents # Chỉ import sau khi MongoEngine sẵn sàng
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")

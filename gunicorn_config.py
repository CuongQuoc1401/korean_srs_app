# gunicorn_config.py - Cấu hình Gunicorn cho môi trường Production

import os
import sys
import django
import logging

# Thiết lập Django trước để có thể import settings và thư viện
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

logger = logging.getLogger(__name__)

# Cấu hình Gunicorn cơ bản
# Tăng số lượng worker để xử lý nhiều request đồng thời
workers = 4 
threads = 2
timeout = 30
# Bind tới port 10000 hoặc 8000 (tùy thuộc vào thiết lập của Render)
bind = '0.0.0.0:10000' 

# ====================================================================
# HOOK QUAN TRỌNG: KHẮC PHỤC LỖI "MongoClient opened before fork"
# ====================================================================
def post_fork(server, worker):
    """
    Hàm này được gọi ngay sau khi mỗi Worker Process được Gunicorn tạo ra (fork).
    Đây là NƠI DUY NHẤT AN TOÀN để tạo kết nối database, đảm bảo mỗi worker
    có một kết nối MongoEngine mới và hợp lệ, không bị hỏng do quá trình fork.
    """
    logger.info("Gunicorn Worker starting. Initializing MongoEngine connection...")
    
    # Imports phải được đặt ở đây để chắc chắn chúng chạy trong Worker Process
    from django.conf import settings
    import mongoengine

    try:
        # 1. Ngắt kết nối cũ nếu có (an toàn)
        try:
            mongoengine.disconnect(alias='default') 
        except Exception:
            pass

        mongo_uri = settings.MONGO_URI
        
        # 2. Kết nối lại MongoEngine trong Worker Process mới
        mongoengine.connect(
            host=mongo_uri, 
            alias='default', 
            maxPoolSize=50, 
            serverSelectionTimeoutMS=5000,
            readPreference='secondaryPreferred' # Tăng tính ổn định trong môi trường cloud
        )
        logger.info("MongoEngine connected successfully in worker process.")
        
    except Exception as e:
        # Nếu không thể kết nối DB, worker này phải dừng lại để tránh lỗi 500
        logger.critical(f"FATAL: Failed to connect MongoEngine in worker process: {e}")
        worker.exit()

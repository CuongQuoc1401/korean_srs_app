from pathlib import Path
import mongoengine
from datetime import timedelta
from decouple import config # (1) Import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# (2) Đọc SECRET_KEY từ biến môi trường (secret.env hoặc Render/Railway)
SECRET_KEY = config('SECRET_KEY') 

# SECURITY WARNING: don't run with debug turned on in production!
# (3) Đọc DEBUG từ biến môi trường, mặc định là False nếu không tìm thấy.
DEBUG = config('DEBUG', default=False, cast=bool) 

# (4) Cấu hình ALLOWED_HOSTS cho môi trường Production
if DEBUG:
    # Cho phép các host local khi ở chế độ phát triển
    ALLOWED_HOSTS = []
else:
    # Cho phép tất cả host (nên thay bằng tên miền cụ thể khi deploy)
    # Thêm '0.0.0.0' để đảm bảo Render nhận ra.
    ALLOWED_HOSTS = ['*', '0.0.0.0'] 


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'learning.apps.LearningConfig',
]

MIDDLEWARE = [
    # (A) THÊM WHITENOISE LÊN ĐẦU, NGAY SAU SecurityMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # BẮT BUỘC CHO ADMIN: Đưa Middleware mặc định trở lại
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    
    # !!! ĐẶT MIDDLEWARE TÙY CHỈNH SAU MIDDLEWARE MẶC ĐỊNH !!!
    # Middleware này sẽ chạy sau và GHI ĐÈ request.user bằng User Document MongoEngine
    'learning.middleware.CustomAuthMiddleware', 
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database (Vẫn giữ SQLite cho Django Sessions và Admin)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CẤU HÌNH MONGOENGINE
# (5) Đọc MONGO_URI từ biến môi trường
MONGO_URI = config('MONGO_URI')

# FIX LỖI: MongoClient opened before fork (Lỗi 500 khi sử dụng DB trong Production/Gunicorn)
# Loại bỏ khối try/except kết nối sớm. Thay thế bằng kết nối LAZY để Gunicorn 
# tạo worker trước khi mỗi worker tự thiết lập kết nối an toàn.
mongoengine.connect(
    host=MONGO_URI,
    alias="default",
    lazy=True # <--- THAY ĐỔI QUAN TRỌNG NHẤT CHO DEPLOYMENT
)

# Cấu hình User và Backend
MONGOENGINE_USER_DOCUMENT = 'learning.documents.User' 
AUTHENTICATION_BACKENDS = (
    'learning.auth_backend.CustomMongoEngineBackend', 
)

# Thêm path cho LOGIN
LOGIN_URL = '/login/' 
LOGIN_REDIRECT_URL = '/' # Tùy chọn, nếu bạn cần


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# (6) Cấu hình STATIC_ROOT cho Production
if not DEBUG:
    import os
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # (B) Cấu hình WhiteNoise để nén và cache tệp tĩnh (Tùy chọn nhưng nên có)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
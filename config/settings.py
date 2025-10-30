from pathlib import Path
from decouple import config 
from datetime import timedelta
# THIẾT YẾU: Cần import mongoengine để sử dụng MONGOENGINE_DATABASES
import mongoengine 

# --- CẤU HÌNH CƠ BẢN ---
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- KHU VỰC CẤU HÌNH BIẾN MÔI TRƯỜNG AN TOÀN ---

# SECURITY WARNING: don't run with debug turned on in production!
# Đọc DEBUG từ biến môi trường, mặc định là False nếu không tìm thấy.
DEBUG = config('DEBUG', default=False, cast=bool) 

if DEBUG:
    # Giá trị mặc định an toàn cho môi trường Local (DEBUG=True)
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-local-key-for-development-only') 
    # URI MongoDB Local mặc định (chỉ cho dev)
    MONGO_URI = config('MONGO_URI', default='mongodb://localhost:27017/korean_srs_local')
else:
    # Đọc SECRET_KEY và MONGO_URI từ biến môi trường Render
    SECRET_KEY = config('SECRET_KEY') 
    MONGO_URI = config('MONGO_URI')

# --- HẾT KHU VỰC CẤU HÌNH BIẾN MÔI TRƯỜNG AN TOÀN ---

# Cấu hình ALLOWED_HOSTS cho môi trường Production
if DEBUG:
    # Cho phép các host local khi ở chế độ phát triển
    ALLOWED_HOSTS = []
else:
    # Cho phép tất cả host khi deploy trên Render (nên thay bằng tên miền cụ thể khi có thể)
    ALLOWED_HOSTS = ['*', '0.0.0.0'] 


# Application definition

INSTALLED_APPS = [
    # Django Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # ĐÃ XÓA 'django_mongoengine' vì nó không tương thích với Django 4.2
    
    # Custom Apps
    'learning.apps.LearningConfig',
]

MIDDLEWARE = [
    # 1. Django Security
    'django.middleware.security.SecurityMiddleware',
    
    # 2. WhiteNoise (BẮT BUỘC cho việc phục vụ Static files trên Production)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    # 3. Django Standard Middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # 4. Django Auth (Cần thiết cho Admin Site)
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    
    # 5. Custom Auth Middleware (Để sử dụng User Document của MongoEngine)
    'learning.middleware.CustomAuthMiddleware', 
    
    # 6. Django Messages/Clickjacking
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

# CẤU HÌNH MONGOENGINE (Cách chính thức để MongoEngine tự kết nối)
# Việc này an toàn hơn so với việc gọi connect() trực tiếp.
MONGOENGINE_DATABASES = {
    'default': {
        'host': MONGO_URI,
    }
}

# THIẾT LẬP KẾT NỐI MONGOENGINE THỦ CÔNG
# ĐÃ XÓA mongoengine.connect() trực tiếp khỏi settings.py để tránh lỗi fork.
# Kết nối sẽ được gọi trong learning/apps.py
# mongoengine.connect(host=MONGO_URI) # <--- Đã bị loại bỏ

# Cấu hình User và Backend cho MongoEngine
MONGOENGINE_USER_DOCUMENT = 'learning.documents.User' 
AUTHENTICATION_BACKENDS = (
    'learning.auth_backend.CustomMongoEngineBackend', 
)

# Thêm path cho LOGIN
LOGIN_URL = '/login/' 
LOGIN_REDIRECT_URL = '/' 


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

# Cấu hình STATIC_ROOT cho Production
if not DEBUG:
    import os
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Cấu hình WhiteNoise để nén và cache tệp tĩnh (Tối ưu hóa Production)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
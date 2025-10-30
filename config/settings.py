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
# Đảm bảo ép kiểu sang bool để xử lý chuỗi 'False' hoặc 'True' từ ENV
DEBUG = config('DEBUG', default=False, cast=bool) 

if DEBUG:
    # Giá trị mặc định an toàn cho môi trường Local (DEBUG=True)
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-local-key-for-development-only') 
    # URI MongoDB Local mặc định (chỉ cho dev)
    MONGO_URI = config('MONGO_URI', default='mongodb://localhost:27017/korean_srs_local')
else:
    # Đọc SECRET_KEY và MONGO_URI từ biến môi trường Render
    # Trong môi trường Production, KHÔNG cung cấp giá trị default
    SECRET_KEY = config('SECRET_KEY') 
    MONGO_URI = config('MONGO_URI')

# --- HẾT KHU VỰC CẤU HÌNH BIẾN MÔI TRƯỜNG AN TOÀN ---

# Cấu hình ALLOWED_HOSTS cho môi trường Production
if DEBUG:
    # Cho phép các host local khi ở chế độ phát triển
    ALLOWED_HOSTS = []
else:
    # Cho phép tất cả host khi deploy trên Render (nên thay bằng tên miền cụ thể khi có thể)
    ALLOWED_HOSTS = ['*', '0.0.0.0', 'korean-srs-app.onrender.com'] 


# Application definition

INSTALLED_APPS = [
    # Django Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    # KHẮC PHỤC: PHẢI THÊM LẠI CONTENTTYPES VÌ ADMIN PHỤ THUỘC VÀO NÓ
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom Apps
    'learning.apps.LearningConfig',
]

# Thêm biến này để nói với Django không sử dụng Permission/ContentType trong Auth
# Dù không phải cách chính thức, đây là giải pháp phổ biến nhất khi dùng MongoEngine
DISABLE_AUTH_PERMISSIONS = True 


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
MONGOENGINE_DATABASES = {
    'default': {
        'host': MONGO_URI,
    }
}

# --- DEBUGGING: BẮT BUỘC THỰC HIỆN KẾT NỐI SỚM ĐỂ BẮT LỖI ---
# Dùng thư viện mongoengine trực tiếp để kết nối và kiểm tra URI.
if MONGO_URI:
    try:
        # Tên database thường là phần cuối cùng của chuỗi URI trước dấu '?'
        db_name = MONGO_URI.split('/')[-1].split('?')[0]
        # Sử dụng connect() để buộc kiểm tra kết nối ngay khi file settings được đọc
        mongoengine.connect(host=MONGO_URI, db=db_name)
        print(f"✅ Kết nối MongoDB thành công với DB: {db_name}")
    except Exception as e:
        # Nếu DEBUG=True, ta cho phép nó crash để thấy lỗi chi tiết
        if DEBUG:
            raise Exception(f"LỖI KHỞI TẠO MONGODB (LOCAL/DEV): {e}") 
        # Nếu DEBUG=False (Production), ta ghi log và không làm crash máy chủ ngay lập tức
        # nhưng lỗi này sẽ xuất hiện rõ ràng trong log Render.
        else:
            print(f"❌ LỖI KẾT NỐI MONGODB (RENDER/PROD): Vui lòng kiểm tra MONGO_URI và Network Access. Lỗi: {e}")
# -------------------------------------------------------------


# Cấu hình User và Backend cho MongoEngine
MONGOENGINE_USER_DOCUMENT = 'learning.documents.User' 
AUTHENTICATION_BACKENDS = (
    'learning.auth_backend.CustomMongoEngineBackend', 
    # KHẮC PHỤC: VÔ HIỆU HÓA MODEL BACKEND MẶC ĐỊNH
    # 'django.contrib.auth.backends.ModelBackend',
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

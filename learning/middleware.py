# File: learning/middleware.py (Đã sửa lỗi)

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from .auth_backend import CustomMongoEngineBackend
from .documents import User
from django.utils.functional import SimpleLazyObject

# Tạo một đối tượng User giả cho người dùng chưa đăng nhập
class AnonymousUserPlaceholder:
    id = None
    pk = None
    is_active = False
    is_staff = False
    is_superuser = False
    is_authenticated = False
    is_anonymous = True
    full_name = "Guest"
    email = ""

    def __bool__(self):
        return self.is_authenticated

    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False
        
def get_user_from_session(request):
    """
    Hàm tùy chỉnh để lấy User Document từ session an toàn.
    """
    if not hasattr(request, '_cached_user'):
        user_id = request.session.get(SESSION_KEY)
        
        if user_id is None:
            request._cached_user = AnonymousUserPlaceholder()
        else:
            backend = CustomMongoEngineBackend()
            user = backend.get_user(user_id)
            
            if user is None:
                request.session.flush()
                request._cached_user = AnonymousUserPlaceholder()
            else:
                request._cached_user = user
                
    return request._cached_user

class CustomAuthMiddleware(MiddlewareMixin):
    """
    Middleware thay thế request.user bằng User Document từ MongoEngine,
    sau khi AuthenticationMiddleware mặc định đã chạy.
    """
    def process_request(self, request):
        # Ghi đè request.user bằng đối tượng User Document (SimpleLazyObject)
        # Điều này loại bỏ đối tượng SimpleLazyObject bị lỗi do Middleware mặc định tạo ra
        request.user = SimpleLazyObject(lambda: get_user_from_session(request))
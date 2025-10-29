from .documents import User
from django.contrib.auth.backends import BaseBackend

class CustomMongoEngineBackend(BaseBackend):
    # Hàm xác thực (không đổi, vẫn hoạt động tốt)
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None

        if user.is_active and user.check_password(password):
            return user
        return None

    # Hàm bắt buộc: Lấy User object từ ID
    def get_user(self, user_id):
        try:
            # user_id là ID (pk) của user được lưu trong session (ObjectId string)
            return User.objects.get(pk=user_id) 
        except User.DoesNotExist:
            return None
            
    # --- PHẦN KHẮC PHỤC LỖI Attribute Error ---
    
    # 1. Thêm hàm get_user_model: Bắt buộc cho Django Auth system
    def get_user_model(self):
        # Trả về User Document của bạn (từ MongoEngine)
        return User

    # 2. Thêm hàm get_user_id: Hàm này sẽ được Django gọi thay vì truy cập user._meta.pk
    def get_user_id(self, user):
        # Trả về ID dưới dạng string. 'id' là trường khóa chính mặc định của MongoEngine.
        return str(user.id) 
    
    # 3. (Tùy chọn) Thêm hàm get_user_details: Cần thiết để hỗ trợ đầy đủ
    def get_user_details(self, user):
        # Trả về dictionary chứa thông tin user cơ bản
        return {
            'username': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
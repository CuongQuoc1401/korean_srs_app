from django.contrib.auth.backends import BaseBackend
from .documents import User # Import model User của MongoEngine
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class CustomMongoEngineBackend(BaseBackend):
    """
    Custom Authentication Backend cho phép Django sử dụng MongoEngine User model
    được lưu trữ trong MongoDB.
    """

    def authenticate(self, request, username=None, password=None):
        """
        Xác thực người dùng bằng email (username) và mật khẩu.
        """
        if username is None or password is None:
            # Nếu username hoặc password bị thiếu, không thể xác thực
            return None

        try:
            # Tìm kiếm người dùng dựa trên email
            user = User.objects(email=username).first()
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn User từ MongoDB: {e}")
            return None

        if user:
            # Kiểm tra mật khẩu (hàm check_password đã được MongoEngine thêm vào User)
            if user.check_password(password) and user.is_active:
                logger.debug(f"Xác thực thành công cho user: {user.email}")
                return user
            else:
                logger.warning(f"Xác thực thất bại cho user: {user.email} (mật khẩu sai hoặc tài khoản không hoạt động)")
                return None
        
        logger.warning(f"Không tìm thấy User với email: {username}")
        return None

    def get_user(self, user_id):
        """
        Lấy đối tượng User (document) dựa trên user_id (được lưu trong session).
        user_id ở đây là ObjectId dạng chuỗi.
        """
        if not user_id:
            return None

        try:
            # Chuyển đổi user_id sang ObjectId trước khi truy vấn
            object_id = ObjectId(str(user_id))
        except Exception as e:
            logger.error(f"User ID {user_id} không phải là ObjectId hợp lệ: {e}")
            return None

        try:
            # Tìm kiếm người dùng theo ObjectId
            user = User.objects(id=object_id).first()
            return user
        except Exception as e:
            logger.error(f"Lỗi khi lấy User theo ID {user_id}: {e}")
            return None

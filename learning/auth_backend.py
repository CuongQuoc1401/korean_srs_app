from datetime import datetime
from .documents import User
from django.contrib.auth.backends import BaseBackend
# Thêm import ObjectId để bắt lỗi
from bson.errors import InvalidId 
# Thêm import mongoengine để bắt lỗi Connection/Query
import mongoengine 

class CustomMongoEngineBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 1. Tìm kiếm người dùng bằng email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Nếu người dùng không tồn tại, trả về None (Django xử lý)
            return None
        except mongoengine.errors.ConnectionError as e:
            # Lỗi kết nối DB
            print(f"LỖI KẾT NỐI MONGO DB TRONG AUTHENTICATE: {e}")
            raise
        except Exception as e:
            # Ghi nhật ký lỗi truy vấn DB tổng quát
            print(f"Lỗi truy vấn MongoDB trong authenticate: {e}")
            raise # Ném lại lỗi để hệ thống ghi nhận traceback

        if user.is_active and user.check_password(password):
            try:
                # 2. Cập nhật thời gian đăng nhập lần cuối
                user.last_login = datetime.now()
                user.save()
            except Exception as e:
                # Ghi nhật ký lỗi khi lưu user
                print(f"Lỗi khi lưu user sau đăng nhập: {e}")
                raise 
                
            return user
        return None

    def get_user(self, user_id):
        # user_id là ID (pk) của user được lưu trong session (ObjectId string)
        try:
            # BẮT BUỘC: Bắt lỗi InvalidId khi Django cố gắng ép kiểu ID
            return User.objects.with_id(user_id) 
        except InvalidId:
            # Lỗi thường xảy ra khi user_id không phải là ObjectId hợp lệ
            print(f"Lỗi ID không hợp lệ (InvalidId) cho user_id: {user_id}")
            return None
        except mongoengine.errors.ConnectionError as e:
            print(f"LỖI KẾT NỐI MONGO DB TRONG GET_USER: {e}")
            return None
        except Exception as e:
            # Lỗi khi tìm user từ session
            print(f"Lỗi truy vấn MongoDB trong get_user: {e}")
            return None
            
    def get_user_model(self):
        # Trả về User Document của bạn
        return User

    def get_user_id(self, user):
        # Trả về ID dưới dạng string.
        return str(user.id)

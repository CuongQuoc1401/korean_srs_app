# File: learning/auth_backend.py

import datetime
from .documents import User
from django.contrib.auth.backends import BaseBackend

class CustomMongoEngineBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None

        if user.is_active and user.check_password(password):
            # Cập nhật thời gian đăng nhập lần cuối
            user.last_login = datetime.now()
            user.save()
            return user
        return None

    def get_user(self, user_id):
        # user_id là ID (pk) của user được lưu trong session (ObjectId string)
        try:
            return User.objects.get(pk=user_id) 
        except User.DoesNotExist:
            return None
            
    def get_user_model(self):
        # Trả về User Document của bạn
        return User

    def get_user_id(self, user):
        # Trả về ID dưới dạng string.
        return str(user.id)
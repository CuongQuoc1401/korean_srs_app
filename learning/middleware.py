from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import SESSION_KEY
from learning.documents import User

class MongoUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_id = request.session.get(SESSION_KEY)
        if user_id:
            user = User.objects(id=user_id).first()
            request.user = user
        else:
            request.user = None

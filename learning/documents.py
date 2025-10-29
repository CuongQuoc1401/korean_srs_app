# File: learning/documents.py

from mongoengine import Document, fields, CASCADE 
from datetime import datetime, timedelta
# Import các hàm băm từ Django
from django.contrib.auth.hashers import make_password, check_password

# --- 1. User Document (Không Custom Manager) ---

# KẾ THỪA CHỈ TỪ DOCUMENT và TỰ ĐỊNH NGHĨA CÁC TRƯỜNG AUTH
class User(Document): 
    email = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=True)  # Lưu hash mật khẩu
    full_name = fields.StringField(max_length=100)
    
    # Các trường permissions cần thiết cho Django Auth
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)
    last_login = fields.DateTimeField(default=datetime.now) 
    
    created_at = fields.DateTimeField(default=datetime.now)

    # Cấu hình Django Auth (Vẫn cần để hệ thống Auth nhận diện trường)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    # KHÔNG CÓ objects = CustomUserManager()

    # Phương thức set_password/check_password thủ công
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # Các phương thức cần thiết của Django Auth/PermissionsMixin
    def get_username(self):
        return self.email
        
    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
        
    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser 
        
    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser 

    meta = {'collection': 'users'}


# --- 2. Vocabulary Document ---

class Vocabulary(Document):
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE) 
    korean_word = fields.StringField(required=True)
    hanja = fields.StringField()
    vietnamese_meaning = fields.StringField(required=True)
    example_sentence = fields.StringField()
    notes = fields.StringField()
    added_at = fields.DateTimeField(default=datetime.now)
    
    # Các trường Spaced Repetition
    level = fields.IntField(default=1) 
    next_review_date = fields.DateField(default=datetime.now().date()) 
    last_reviewed_at = fields.DateTimeField(default=datetime.now)
    current_interval_days = fields.IntField(default=1) 
    consecutive_correct_count = fields.IntField(default=0)
    
    meta = {
        'collection': 'vocabularies',
        'indexes': [
            'user', 
            'next_review_date', 
        ]
    }
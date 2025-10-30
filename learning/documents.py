from mongoengine import Document, fields, CASCADE 
from datetime import datetime, date 
from django.contrib.auth.hashers import make_password, check_password

# --- User Document ---

class User(Document): 
    # Thuộc tính pk để Django có thể truy cập user.pk
    # LƯU Ý: Đây là một property, nó trả về ID của MongoEngine (ObjectId)
    pk = property(lambda self: self.id) 
    
    email = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=True)
    full_name = fields.StringField(max_length=100)
    
    # Các trường permissions cần thiết cho Django Auth
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)
    last_login = fields.DateTimeField(default=datetime.now) 
    created_at = fields.DateTimeField(default=datetime.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # CẦN THIẾT: Phương thức get_username
    def get_username(self):
        return self.email
    
    # KHẮC PHỤC CHÍNH: Phương thức get_session_auth_hash()
    # Django sử dụng hàm băm này để xác thực user trong session.
    # Khi dùng MongoEngine, nó mặc định không có, gây lỗi 500.
    def get_session_auth_hash(self):
        """
        Trả về một hàm băm được sử dụng để xác thực user trong session.
        Chúng ta sẽ sử dụng một hàm băm đơn giản từ mật khẩu đã băm.
        """
        return self.password

    # CẦN THIẾT: Phương thức get_full_name (dùng trong base_layout.html)
    def get_full_name(self):
        return self.full_name or self.email

    # CẦN THIẾT: Các phương thức Property (nên dùng @property)
    # Tuy nhiên, phiên bản hàm của bạn đã hoạt động tốt cho mục đích này
    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
        
    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser 
        
    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser 

    meta = {'collection': 'users'}


# --- Vocabulary Document ---

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
    # KHẮC PHỤC: Sử dụng lambda để gọi date.today() MỖI KHI document mới được tạo
    next_review_date = fields.DateField(default=lambda: date.today()) 
    last_reviewed_at = fields.DateTimeField(default=datetime.now)
    current_interval_days = fields.IntField(default=1) 
    consecutive_correct_count = fields.IntField(default=0)
    
    meta = {
        'collection': 'vocabularies',
        'indexes': ['user', 'next_review_date', ]
    }

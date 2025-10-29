# File: learning/management/commands/create_mongo_superuser.py (Hoàn thiện & Thủ công)

from django.core.management.base import BaseCommand
from learning.documents import User 
from datetime import datetime
import getpass 
import pymongo.errors
from django.contrib.auth.hashers import make_password 

class Command(BaseCommand):
    help = 'Tạo Superuser cho MongoEngine (thay thế cho createsuperuser mặc định).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("--- Bắt đầu tạo Superuser cho MongoDB ---"))
        
        # 1. Nhập thông tin
        email = input("Email (dùng làm tên đăng nhập): ")
        full_name = input("Tên đầy đủ: ")
        
        # Nhập mật khẩu ẩn
        while True:
            password = getpass.getpass("Mật khẩu: ")
            password2 = getpass.getpass("Xác nhận mật khẩu: ")
            if password == password2:
                break
            self.stdout.write(self.style.ERROR("Mật khẩu không khớp. Vui lòng thử lại."))

        try:
            # 2. KIỂM TRA USER: Dùng .objects.filter() là cú pháp MongoEngine thuần túy
            if User.objects.filter(email=email).count() > 0: 
                self.stdout.write(self.style.WARNING(f"Superuser với email '{email}' đã tồn tại."))
                return

            # 3. TẠO USER THỦ CÔNG & LƯU
            admin_user = User(
                email=email,
                full_name=full_name,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                created_at=datetime.now()
            )
            
            # Sử dụng phương thức set_password đã định nghĩa trong documents.py để băm
            admin_user.set_password(password)
            
            admin_user.save() # Lưu vào MongoDB
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Superuser '{admin_user.email}' đã được tạo thành công."))
            self.stdout.write(self.style.NOTICE("Bạn có thể đăng nhập vào /admin ngay bây giờ."))

        except pymongo.errors.ConnectionFailure as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Lỗi kết nối MongoDB: Vui lòng kiểm tra MONGO_URI và kết nối mạng: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Lỗi không xác định khi tạo superuser: {e}"))
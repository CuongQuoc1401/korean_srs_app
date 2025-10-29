from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('register/success/', views.registration_success_view, name='registration_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core Application
    path('', views.home_view, name='home'), # Trang chủ/Dashboard
    path('add/', views.add_vocabulary, name='add_vocabulary'), # Thêm từ mới
    
    # Danh sách các từ cần ôn tập (Dashboard List)
    path('review/', views.review_session, name='review_session'), 
    
    # Trang chi tiết/Quiz cho một từ cụ thể
    # Dùng <str:word_id> vì ObjectId của MongoDB là chuỗi (24 ký tự hex)
    path('review/<str:word_id>/', views.word_detail_view, name='word_detail'), 
    
    # ĐƯỜNG DẪN MỚI: Trang chỉnh sửa từ vựng
    path('word/edit/<str:word_id>/', views.word_edit_view, name='word_edit'),
    
    # API để gửi kết quả kiểm tra
    # Chú ý: Đường dẫn này phải nằm SAU đường dẫn review/<str:word_id>/ 
    # nếu không Django sẽ hiểu 'check' là một word_id.
    # Tuy nhiên, cách an toàn hơn là đặt nó ở một prefix khác:
    path('api/check/<str:word_id>/<str:result>/', views.check_word_view, name='check_word'), 
]

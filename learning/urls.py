# File: learning/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core Application
    path('', views.home_view, name='home'), # Trang chủ/Dashboard
    path('add/', views.add_vocabulary, name='add_vocabulary'), # Thêm từ mới
    path('review/', views.review_session, name='review_session'), # Trang kiểm tra
    # API để gửi kết quả kiểm tra
    path('review/check/<str:word_id>/<str:result>/', views.check_word_view, name='check_word'), 
]
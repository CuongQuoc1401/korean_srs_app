# File: learning/forms.py

from django import forms
from .documents import User
from django.core.exceptions import ValidationError

# ========================
# AUTH FORMS
# ========================

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label='Email (Dùng làm Tên đăng nhập)',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(
        label='Tên đầy đủ',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    # THÊM TRƯỜNG XÁC NHẬN MẬT KHẨU
    password_confirm = forms.CharField(
        label='Xác nhận Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean_email(self):
        """Kiểm tra email đã tồn tại chưa."""
        email = self.cleaned_data.get('email')
        if User.objects(email=email).count() > 0:
            raise ValidationError("Email này đã được đăng ký. Vui lòng sử dụng email khác.")
        return email

    def clean(self):
        """Kiểm tra mật khẩu và xác nhận mật khẩu có trùng khớp không."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # Đảm bảo cả hai trường tồn tại trước khi so sánh
        if password and password_confirm:
            if password != password_confirm:
                # Thêm lỗi tổng quát cho trường password_confirm
                self.add_error('password_confirm', 'Mật khẩu xác nhận không khớp.')
                
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

# ========================
# VOCABULARY FORM
# ========================

class VocabularyForm(forms.Form):
    korean_word = forms.CharField(
        label='Từ tiếng Hàn', 
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    vietnamese_meaning = forms.CharField(
        label='Nghĩa tiếng Việt', 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    hanja = forms.CharField(
        label='Hán tự (Tùy chọn)', 
        required=False, 
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    example_sentence = forms.CharField(
        label='Câu ví dụ minh họa', 
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    notes = forms.CharField(
        label='Ghi chú cá nhân', 
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
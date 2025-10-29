# File: learning/forms.py

from django import forms
from .documents import User

# ========================
# AUTH FORMS
# ========================

class RegisterForm(forms.Form):
    email = forms.EmailField(label='Email (Dùng làm Tên đăng nhập)')
    password = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput)
    full_name = forms.CharField(label='Tên đầy đủ')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects(email=email).count() > 0:
            raise forms.ValidationError("Email này đã được đăng ký.")
        return email

class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput)

# ========================
# VOCABULARY FORM
# ========================

class VocabularyForm(forms.Form):
    korean_word = forms.CharField(label='Từ tiếng Hàn', max_length=100)
    vietnamese_meaning = forms.CharField(label='Nghĩa tiếng Việt', widget=forms.Textarea)
    hanja = forms.CharField(label='Hán tự (Tùy chọn)', required=False, max_length=50)
    example_sentence = forms.CharField(label='Câu ví dụ minh họa', required=False, widget=forms.Textarea)
    notes = forms.CharField(label='Ghi chú cá nhân', required=False, widget=forms.Textarea)
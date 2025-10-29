# File: learning/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import SESSION_KEY
from datetime import date
from .documents import User, Vocabulary
from .sr_logic import update_spaced_repetition
from .forms import RegisterForm, LoginForm, VocabularyForm
import json

# ========================
# A. SESSION LOGIN LOGIC
# ========================

def _manual_login(request, user):
    request.session.cycle_key()
    request.session[SESSION_KEY] = str(user.id)  # Lưu ObjectId dưới dạng chuỗi

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ========================
# B. AUTHENTICATION VIEWS
# ========================

def register_view(request):
    if request.session.get(SESSION_KEY):
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        full_name = form.cleaned_data['full_name']

        if User.objects(email=email).first():
            form.add_error('email', 'Email đã tồn tại.')
        else:
            user = User(email=email, full_name=full_name, is_active=True)
            user.set_password(password)
            user.save()
            _manual_login(request, user)
            return redirect('home')

    return render(request, 'learning/register.html', {'form': form})

def login_view(request):
    if request.session.get(SESSION_KEY):
        return redirect('home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects(email=email).first()

        if user and user.check_password(password):
            _manual_login(request, user)
            return redirect('home')
        else:
            form.add_error(None, 'Email hoặc mật khẩu không đúng.')

    return render(request, 'learning/login.html', {'form': form})

# ========================
# C. FUNCTIONAL VIEWS
# ========================

def home_view(request):
    if not request.user:
        return redirect('login')

    vocab = Vocabulary.objects(user=request.user)
    today = date.today()

    context = {
        'total_words': vocab.count(),
        'words_to_review_count': vocab(next_review_date__lte=today).count(),
        'user_name': request.user.full_name or request.user.email,
    }
    return render(request, 'learning/home.html', context)

def add_vocabulary(request):
    if not request.user:
        return redirect('login')

    form = VocabularyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        Vocabulary(
            user=request.user,
            korean_word=form.cleaned_data['korean_word'],
            vietnamese_meaning=form.cleaned_data['vietnamese_meaning'],
            hanja=form.cleaned_data['hanja'],
            example_sentence=form.cleaned_data['example_sentence'],
            notes=form.cleaned_data['notes'],
        ).save()
        return redirect('home')

    return render(request, 'learning/add_vocabulary.html', {'form': form})

def vocabulary_list(request):
    if not request.user:
        return redirect('login')

    words = Vocabulary.objects(user=request.user).order_by('-created_at')
    return render(request, 'learning/vocabulary_list.html', {'words': words})

def review_session(request):
    if not request.user:
        return redirect('login')

    today = date.today()
    words = Vocabulary.objects(user=request.user, next_review_date__lte=today).order_by('next_review_date')

    if not words:
        return render(request, 'learning/review_done.html')

    return render(request, 'learning/review_session.html', {
        'word': words.first(),
        'remaining_count': words.count() - 1,
    })

def check_word_view(request):
    if not request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')
        result = data.get('result')
        if not word_id or not result:
            raise ValueError("Missing fields")
        is_correct = result.lower() == 'correct'
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request data or format'}, status=400)

    word = Vocabulary.objects(user=request.user, id=word_id).first()
    if not word:
        return JsonResponse({'error': 'Word not found or unauthorized'}, status=404)

    update_spaced_repetition(word, is_correct)

    return JsonResponse({
        'success': True,
        'new_level': word.level,
        'next_review_date': word.next_review_date.isoformat(),
        'message': f'Cấp độ mới: {word.level}. Ôn tập lại vào ngày: {word.next_review_date.isoformat()}'
    })

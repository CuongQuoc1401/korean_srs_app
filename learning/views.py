from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from datetime import date, datetime
from .documents import User, Vocabulary # Đảm bảo import Model MongoEngine
from .sr_logic import update_spaced_repetition
from .forms import RegisterForm, LoginForm, VocabularyForm
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# ĐẢM BẢO CÓ BSON.ObjectId CHO MONGODB
from bson import ObjectId 


# ========================
# 1. REUSABLE UTILITY FUNCTION
# ========================

def _paginate_queryset(request, queryset, per_page=20):
    """
    Hàm tiện ích giúp phân trang cho QuerySet (sử dụng được cho MongoEngine)
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj, paginator


# ========================
# A. SESSION LOGIN LOGIC
# ========================
def _manual_login(request, user):
    """Thay thế django.contrib.auth.login() an toàn."""
    request.session.cycle_key()
    request.session[SESSION_KEY] = str(user.id)
    request.session[BACKEND_SESSION_KEY] = 'learning.auth_backend.CustomMongoEngineBackend'
    
    # Cập nhật last_login khi đăng nhập
    user.last_login = datetime.now()
    user.save()

def logout_view(request):
    request.session.flush()
    return redirect('login')


# ========================
# B. AUTHENTICATION VIEWS
# ========================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        full_name = form.cleaned_data['full_name']

        user = User(email=email, full_name=full_name, is_active=True)
        user.set_password(password)
        user.save()
            
        return redirect('registration_success')

    return render(request, 'learning/register.html', {'form': form})

def registration_success_view(request):
    return render(request, 'learning/registration_success.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        user = User.objects(email=email).first()

        if user and user.check_password(password) and user.is_active:
            _manual_login(request, user)
            return redirect('home')
        else:
            form.add_error(None, 'Email hoặc mật khẩu không đúng hoặc tài khoản chưa kích hoạt.')

    return render(request, 'learning/login.html', {'form': form})

# ========================
# C. FUNCTIONAL VIEWS
# ========================

def home_view(request):
    if not request.user.is_authenticated: 
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
    if not request.user.is_authenticated: return redirect('login')

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
    if not request.user.is_authenticated: return redirect('login')

    words = Vocabulary.objects(user=request.user).order_by('-created_at')
    # Nếu bạn muốn phân trang danh sách từ vựng chung, bạn cũng có thể dùng hàm này tại đây
    # page_obj, paginator = _paginate_queryset(request, words, per_page=20)

    return render(request, 'learning/vocabulary_list.html', {'words': words})

def review_session(request):
    if not request.user.is_authenticated: return redirect('login')

    today = date.today()
    # Lấy TẤT CẢ các từ cần ôn tập hôm nay
    words_to_review = Vocabulary.objects(user=request.user, next_review_date__lte=today).order_by('next_review_date')

    if not words_to_review:
        return render(request, 'learning/review_done.html')

    # Áp dụng phân trang 20 từ/trang
    page_obj, paginator = _paginate_queryset(request, words_to_review, per_page=20)

    return render(request, 'learning/review_list_dashboard.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_words': words_to_review.count(),
    })

def word_detail_view(request, word_id):
    if not request.user.is_authenticated: 
        return redirect('login')

    # Chú ý: Vì đang dùng MongoEngine, chúng ta phải chuyển đổi ID sang ObjectId
    try:
        object_id = ObjectId(word_id)
    except Exception:
        raise Http404("Word ID không hợp lệ.")
        
    # SỬA LỖI: Dùng MongoEngine lookup thay vì get_object_or_404
    word = Vocabulary.objects(id=object_id, user=request.user).first()
    if not word:
        raise Http404("Word not found or unauthorized.")

    # Trả về template chi tiết
    return render(request, 'learning/word_detail.html', {'word': word})


def word_edit_view(request, word_id):
    """
    Xử lý việc chỉnh sửa chi tiết một từ vựng cụ thể.
    """
    if not request.user.is_authenticated: 
        return redirect('login')
    
    # Chú ý: Vì đang dùng MongoEngine, chúng ta phải chuyển đổi ID sang ObjectId
    try:
        object_id = ObjectId(word_id)
    except Exception:
        raise Http404("Word ID không hợp lệ.")
        
    # SỬA LỖI: Dùng MongoEngine lookup thay vì get_object_or_404
    word = Vocabulary.objects(id=object_id, user=request.user).first()
    if not word:
        raise Http404("Word not found or unauthorized.")
    
    # --- LOGIC XỬ LÝ POST REQUEST ---
    if request.method == 'POST':
        # Sử dụng VocabularyForm để validate và cập nhật dữ liệu
        form = VocabularyForm(request.POST) 
        
        if form.is_valid():
            # Cập nhật các trường thủ công từ cleaned_data
            word.korean_word = form.cleaned_data['korean_word']
            word.vietnamese_meaning = form.cleaned_data['vietnamese_meaning']
            word.hanja = form.cleaned_data['hanja']
            word.example_sentence = form.cleaned_data['example_sentence']
            word.notes = form.cleaned_data['notes']
            
            # Lưu thay đổi vào MongoDB
            word.save()
            
            # Chuyển hướng người dùng về trang danh sách ôn tập hoặc trang chi tiết vừa sửa
            return redirect('review_session') 
        
    # --- LOGIC XỬ LÝ GET REQUEST ---
    # Khi là GET request, chúng ta tạo form với dữ liệu hiện tại của word để điền vào template
    
    # Tạo form để điền dữ liệu mặc định vào template
    initial_data = word.to_mongo().to_dict()
    form = VocabularyForm(initial=initial_data)

    # Render template chỉnh sửa, truyền đối tượng word và form vào
    return render(request, 'learning/word_edit.html', {'word': word, 'form': form})


def check_word_view(request):
    # API này cần được cập nhật nếu bạn muốn chuyển từ Quiz sang List
    # Hiện tại, nó vẫn giữ nguyên logic xử lý một từ (POST request)
    if not request.user.is_authenticated: return JsonResponse({'error': 'Unauthorized'}, status=401)

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

    # Chuyển đổi ID sang ObjectId
    try:
        object_id = ObjectId(word_id)
    except Exception:
        return JsonResponse({'error': 'Invalid Word ID format'}, status=400)

    word = Vocabulary.objects(user=request.user, id=object_id).first()
    if not word:
        return JsonResponse({'error': 'Word not found or unauthorized'}, status=404)

    update_spaced_repetition(word, is_correct)

    return JsonResponse({
        'success': True,
        'new_level': word.level,
        'next_review_date': word.next_review_date.isoformat(),
        'message': f'Cấp độ mới: {word.level}. Ôn tập lại vào ngày: {word.next_review_date.isoformat()}'
    })

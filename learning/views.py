from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
# SỬ DỤNG HÀM CHUẨN ĐỂ ĐẢM BẢO TÍNH TƯƠNG THÍCH VỚI HỆ THỐNG AUTHENTICATION CỦA DJANGO
from django.contrib.auth import authenticate, login, logout 
from datetime import date, datetime
# Đảm bảo import Model MongoEngine, giả định các models này nằm trong .documents
from .documents import User, Vocabulary 
# Import logic SR
from .sr_logic import update_spaced_repetition
# Import Forms
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

def logout_view(request):
    """Sử dụng hàm logout chuẩn của Django để kết thúc phiên."""
    logout(request)
    # Chuyển hướng về trang login sau khi đăng xuất
    return redirect('login')


# ========================
# B. AUTHENTICATION VIEWS
# ========================

def register_view(request):
    """Xử lý đăng ký tài khoản mới."""
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        full_name = form.cleaned_data['full_name']

        # Tạo và lưu User mới vào MongoDB (MongoEngine document)
        user = User(email=email, full_name=full_name, is_active=True)
        user.set_password(password) # Lưu mật khẩu đã hash
        user.save()
            
        return redirect('registration_success')

    return render(request, 'learning/register.html', {'form': form})

def registration_success_view(request):
    """Trang thông báo đăng ký thành công."""
    return render(request, 'learning/registration_success.html')

def login_view(request):
    """Xử lý đăng nhập tài khoản."""
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        # 1. SỬ DỤNG HÀM AUTHENTICATE CHUẨN CỦA DJANGO
        # Backend (CustomMongoEngineBackend) sẽ kiểm tra email và mật khẩu
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # 2. SỬ DỤNG HÀM LOGIN CHUẨN CỦA DJANGO
            # Thiết lập session cho người dùng đã xác thực
            login(request, user)
            return redirect('home')
        else:
            form.add_error(None, 'Email hoặc mật khẩu không đúng hoặc tài khoản chưa kích hoạt.')

    return render(request, 'learning/login.html', {'form': form})

# ========================
# C. FUNCTIONAL VIEWS
# ========================

def home_view(request):
    """Trang chủ, hiển thị tổng quan và số từ cần ôn tập."""
    if not request.user.is_authenticated: 
        return redirect('login')

    # Query tất cả từ vựng của người dùng hiện tại
    vocab = Vocabulary.objects(user=request.user)
    today = date.today()

    context = {
        'total_words': vocab.count(),
        # Đếm số từ có ngày ôn tập <= hôm nay
        'words_to_review_count': vocab(next_review_date__lte=today).count(),
        # Lấy tên hoặc email của người dùng
        'user_name': request.user.full_name or request.user.email,
    }
    return render(request, 'learning/home.html', context)

def add_vocabulary(request):
    """Thêm một từ vựng mới vào bộ sưu tập."""
    if not request.user.is_authenticated: return redirect('login')

    form = VocabularyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Tạo và lưu document Vocabulary mới
        Vocabulary(
            user=request.user,
            korean_word=form.cleaned_data['korean_word'],
            vietnamese_meaning=form.cleaned_data['vietnamese_meaning'],
            hanja=form.cleaned_data['hanja'],
            example_sentence=form.cleaned_data['example_sentence'],
            notes=form.cleaned_data['notes'],
        ).save()
        # Có thể redirect về trang chi tiết của từ vừa thêm hoặc danh sách
        return redirect('vocabulary_list') 

    return render(request, 'learning/add_vocabulary.html', {'form': form})

def vocabulary_list(request):
    """Hiển thị toàn bộ danh sách từ vựng đã thêm (không phân trang trong ví dụ này)."""
    if not request.user.is_authenticated: return redirect('login')

    # Lấy tất cả từ vựng của người dùng, sắp xếp theo thời gian tạo mới nhất
    words = Vocabulary.objects(user=request.user).order_by('-created_at')
    
    # Bạn có thể phân trang danh sách từ vựng chung ở đây nếu cần
    page_obj, paginator = _paginate_queryset(request, words, per_page=20)


    return render(request, 'learning/vocabulary_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'words': words # Giữ nguyên biến words nếu bạn không dùng page_obj trong template
    })

def review_session(request):
    """Dashboard hiển thị danh sách từ cần ôn tập hôm nay, có phân trang."""
    if not request.user.is_authenticated: return redirect('login')

    today = date.today()
    # Lấy TẤT CẢ các từ cần ôn tập hôm nay, sắp xếp theo ngày ôn tập gần nhất
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
    """Xem chi tiết một từ vựng."""
    if not request.user.is_authenticated: 
        return redirect('login')

    try:
        # Chuyển đổi ID từ URL sang ObjectId của MongoDB
        object_id = ObjectId(word_id)
    except Exception:
        raise Http404("Word ID không hợp lệ.")
        
    # Tìm từ vựng theo ID và đảm bảo nó thuộc về người dùng hiện tại
    word = Vocabulary.objects(id=object_id, user=request.user).first()
    if not word:
        raise Http404("Word not found or unauthorized.")

    return render(request, 'learning/word_detail.html', {'word': word})


def word_edit_view(request, word_id):
    """Xử lý việc chỉnh sửa chi tiết một từ vựng cụ thể."""
    if not request.user.is_authenticated: 
        return redirect('login')
    
    try:
        object_id = ObjectId(word_id)
    except Exception:
        raise Http404("Word ID không hợp lệ.")
        
    word = Vocabulary.objects(id=object_id, user=request.user).first()
    if not word:
        raise Http404("Word not found or unauthorized.")
    
    # --- LOGIC XỬ LÝ POST REQUEST (Cập nhật) ---
    if request.method == 'POST':
        # Sử dụng VocabularyForm để validate dữ liệu từ người dùng
        form = VocabularyForm(request.POST) 
        
        if form.is_valid():
            # Cập nhật các trường dữ liệu
            word.korean_word = form.cleaned_data['korean_word']
            word.vietnamese_meaning = form.cleaned_data['vietnamese_meaning']
            word.hanja = form.cleaned_data['hanja']
            word.example_sentence = form.cleaned_data['example_sentence']
            word.notes = form.cleaned_data['notes']
            
            # Lưu thay đổi vào MongoDB
            word.save()
            
            # Chuyển hướng người dùng về trang danh sách ôn tập
            return redirect('review_session') 
        
    # --- LOGIC XỬ LÝ GET REQUEST (Hiển thị form) ---
    # Khi là GET request, tạo form với dữ liệu hiện tại của word để điền vào template
    
    # Chuyển đổi MongoEngine Document sang Dict để truyền vào initial của Form
    initial_data = word.to_mongo().to_dict()
    form = VocabularyForm(initial=initial_data)

    return render(request, 'learning/word_edit.html', {'word': word, 'form': form})


def check_word_view(request, word_id, result):
    """API Endpoint để cập nhật cấp độ SR (Spaced Repetition) của một từ vựng."""
    if not request.user.is_authenticated: return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        # API này chỉ chấp nhận POST request
        return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        # Lấy kết quả từ URL (correct/incorrect)
        is_correct = result.lower() == 'correct'
        # Chuyển đổi ID từ URL sang ObjectId
        object_id = ObjectId(word_id) 
    except Exception:
        return JsonResponse({'error': 'Invalid Word ID format'}, status=400)


    # Tìm từ vựng và đảm bảo nó thuộc về người dùng
    word = Vocabulary.objects(user=request.user, id=object_id).first()
    if not word:
        return JsonResponse({'error': 'Word not found or unauthorized'}, status=404)

    # Cập nhật logic lặp lại ngắt quãng
    update_spaced_repetition(word, is_correct)
    
    # Trả về kết quả cho frontend (thường là qua AJAX)
    return JsonResponse({
        'success': True,
        'new_level': word.level,
        'next_review_date': word.next_review_date.isoformat(),
        'message': f'Cấp độ mới: {word.level}. Ôn tập lại vào ngày: {word.next_review_date.strftime("%Y-%m-%d")}'
    })

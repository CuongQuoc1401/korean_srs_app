# File: learning/sr_logic.py (Tạo file mới để tách logic)

from datetime import date, timedelta
import datetime
from .documents import Vocabulary

# Khoảng thời gian lặp lại ngắt quãng theo cấp độ (ngày)
# Cấp độ (Int): Khoảng thời gian ôn tập (Int)
SR_INTERVALS = {
    1: 1,  # Mới
    2: 3,  # Đang học
    3: 7,  # Tốt
    4: 14, # Thành thạo
}

def update_spaced_repetition(vocabulary_doc: Vocabulary, is_correct: bool):
    """
    Cập nhật các trường SR của từ vựng dựa trên kết quả kiểm tra.
    """
    
    # 1. Xử lý khi trả lời ĐÚNG
    if is_correct:
        # Tăng số lần trả lời đúng liên tiếp
        vocabulary_doc.consecutive_correct_count += 1
        
        # Nếu chưa đạt cấp 4, tăng cấp độ
        if vocabulary_doc.level < 4:
            vocabulary_doc.level += 1
            
        # Lấy khoảng thời gian ôn tập mới dựa trên cấp độ mới
        interval = SR_INTERVALS.get(vocabulary_doc.level, SR_INTERVALS[4]) # Mặc định là 14 ngày nếu cấp độ > 4
        
        vocabulary_doc.current_interval_days = interval
        
    # 2. Xử lý khi trả lời SAI
    else:
        # Quay về Cấp 1
        vocabulary_doc.level = 1
        vocabulary_doc.consecutive_correct_count = 0
        
        # Khoảng thời gian sẽ là 1 ngày
        interval = SR_INTERVALS[1] 
        vocabulary_doc.current_interval_days = interval

    # 3. Cập nhật ngày ôn tập tiếp theo
    vocabulary_doc.next_review_date = date.today() + timedelta(days=vocabulary_doc.current_interval_days)
    vocabulary_doc.last_reviewed_at = datetime.now()
    
    # Lưu lại vào MongoDB
    vocabulary_doc.save()

# --- Ví dụ về hàm kiểm tra (sẽ được gọi trong views.py) ---
# def check_word_view(request, word_id, answer_result):
#     # 1. Lấy từ vựng
#     try:
#         word = Vocabulary.objects.get(id=word_id, user=request.user)
#     except Vocabulary.DoesNotExist:
#         return JsonResponse({'error': 'Word not found'}, status=404)
#
#     # 2. Cập nhật logic SR
#     update_spaced_repetition(word, is_correct=(answer_result == 'correct'))
#
#     # 3. Trả về kết quả
#     return JsonResponse({'message': 'Review successfully recorded', 'next_review': word.next_review_date})
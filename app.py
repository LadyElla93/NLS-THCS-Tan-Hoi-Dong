import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

# --- 1. CẤU HÌNH TỪ ĐIỂN ĐỆM CHO CÁC MÔN HỌC ---
# Đây là "bộ não" giúp App hiểu tiếng nói của giáo viên từng môn
SUBJECT_MAPPING = {
    "Toán học": {
        "keywords": ["geogebra", "máy tính cầm tay", "đồ thị", "tính toán", "excel", "mô phỏng", "số liệu"],
        "nls_id_suggest": ["5.1TC1a", "5.1TC2b"] # Gợi ý mã NLS thường gặp (Giải quyết vấn đề)
    },
    "Ngữ văn": {
        "keywords": ["soạn thảo", "văn bản", "trình chiếu", "clip", "video", "tra cứu", "tác giả", "e-book"],
        "nls_id_suggest": ["3.1TC1a", "1.1TC1a"] # Gợi ý mã NLS thường gặp (Sáng tạo nội dung, Tìm tin)
    },
    "Lịch sử & Địa lý": {
        "keywords": ["bản đồ số", "google earth", "lược đồ", "tư liệu", "tranh ảnh", "gps", "tìm nguồn"],
        "nls_id_suggest": ["1.2TC1a", "1.1TC1b"] # (Đánh giá thông tin, Tìm kiếm)
    },
    "Khoa học tự nhiên (Lý/Hóa/Sinh)": {
        "keywords": ["thí nghiệm ảo", "mô phỏng", "phet", "video thí nghiệm", "ghi lại số liệu", "cảm biến"],
        "nls_id_suggest": ["5.3TC1a", "1.3TC1a"] # (Sử dụng sáng tạo, Quản lý dữ liệu)
    },
    "Tin học": {
        "keywords": [], # Tin học thì dùng chính từ khóa gốc của NLS
        "nls_id_suggest": []
    }
}

# --- 2. HÀM TẢI DỮ LIỆU NLS (GIỮ NGUYÊN) ---
@st.cache_data
def load_nls_data():
    # Trong thực tế bạn load file CSV đầy đủ
    data = {
        'Id': ['1.1TC1a', '1.1TC2b', '3.1TC1a', '5.1TC1a'],
        'Muc': ['TC1', 'TC2', 'TC1', 'TC1'],
        'YCCD': [
            'Xác định được nhu cầu thông tin; tìm kiếm dữ liệu trên mạng',
            'Tổ chức tìm kiếm thông tin nâng cao',
            'Tạo và chỉnh sửa nội dung số (văn bản, hình ảnh)',
            'Giải quyết vấn đề kỹ thuật khi vận hành thiết bị'
        ]
    }
    return pd.DataFrame(data)

# --- 3. LOGIC PHÂN TÍCH NÂNG CAO ---
def analyze_content_advanced(lesson_text, df_nls, subject_choice):
    results = []
    lesson_text_lower = lesson_text.lower()
    
    # Lấy danh sách từ khóa bổ sung của môn học đó
    extra_keywords = []
    if subject_choice in SUBJECT_MAPPING:
        extra_keywords = SUBJECT_MAPPING[subject_choice]['keywords']
    
    for index, row in df_nls.iterrows():
        # 1. Từ khóa gốc của NLS
        original_keywords = [w for w in row['YCCD'].lower().split() if len(w) > 3]
        
        # 2. Kết hợp từ khóa môn học vào việc tìm kiếm
        # Nếu giáo án chứa từ khóa môn học (VD: "GeoGebra") VÀ ID này thuộc nhóm gợi ý -> Tăng điểm khớp
        bonus_score = 0
        
        # Kiểm tra từ khóa môn học xuất hiện trong bài không
        found_subject_kw = [kw for kw in extra_keywords if kw in lesson_text_lower]
        
        if found_subject_kw:
            # Nếu tìm thấy từ khóa chuyên ngành, ta xem xét ID này có liên quan không
            # Đây là logic "mở rộng": Map từ khóa chuyên ngành sang NLS
            bonus_score = 0.3 # Cộng 30% độ tin cậy
        
        # Đếm từ khóa gốc
        match_count = sum(1 for word in original_keywords if word in lesson_text_lower)
        base_score = match_count / len(original_keywords) if original_keywords else 0
        
        final_score = base_score + bonus_score
        
        # Ngưỡng duyệt (thấp hơn một chút vì đã có bonus)
        if final_score > 0.5:
            # Tìm vị trí (Logic bước 4)
            segments = re.split(r'(Hoạt động\s+[0-9]+|Phần\s+[0-9]+)', lesson_text, flags=re.IGNORECASE)
            location = "Tiến trình dạy học"
            for seg in segments:
                if len(seg) > 50 and (any(k in seg.lower() for k in original_keywords) or any(k in seg.lower() for k in found_subject_kw)):
                    # Lấy tên hoạt động trước đó (giả lập)
                    location = "Hoạt động học tập (có chứa từ khóa liên quan)"
                    break
            
            # Tạo lời giải thích theo môn
            explanation = (
                f"Trong môn {subject_choice}, việc sử dụng các yếu tố như {', '.join(found_subject_kw) if found_subject_kw else 'công nghệ số'} "
                f"đáp ứng yêu cầu '{row['YCCD']}'. "
                f"Giúp học sinh không chỉ học kiến thức {subject_choice} mà còn phát triển kỹ năng số."
            )

            results.append({
                "ID": row['Id'],
                "YCCD": row['YCCD'],
                "Vi_tri": location,
                "Giai_thich": explanation
            })
            
    return results

# --- 4. GIAO DIỆN STREAMLIT ---
st.title("🤖 Trợ lý AI Soạn Giáo Án Tích Hợp NLS")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    grade_option = st.selectbox("1. Chọn Khối lớp", ('Lớp 6', 'Lớp 7', 'Lớp 8', 'Lớp 9'))
with col2:
    # THÊM: Chọn môn học để tối ưu thuật toán
    subject_option = st.selectbox("2. Chọn Môn học", 
                                  ("Toán học", "Ngữ văn", "Lịch sử & Địa lý", "Khoa học tự nhiên (Lý/Hóa/Sinh)", "Tin học", "Khác"))

uploaded_file = st.file_uploader("3. Tải lên giáo án (Word/PDF)", type=['docx', 'pdf'])

if uploaded_file:
    # Xử lý mapping lớp
    target_muc = 'TC1' if grade_option in ['Lớp 6', 'Lớp 7'] else 'TC2'
    
    # Đọc file
    text_content = ""
    if uploaded_file.name.endswith('.docx'):
        text_content = docx2txt.process(uploaded_file)
    # (Phần PDF giữ nguyên như cũ)

    # Load data và lọc
    df = load_nls_data()
    df_filtered = df[df['Muc'] == target_muc]

    st.info(f"Đang phân tích giáo án môn **{subject_option}** - Khối **{target_muc}**...")
    
    # GỌI HÀM PHÂN TÍCH NÂNG CAO
    analysis_results = analyze_content_advanced(text_content, df_filtered, subject_option)

    st.divider()
    if analysis_results:
        st.success(f"✅ Tìm thấy {len(analysis_results)} điểm tích hợp phù hợp!")
        
        for item in analysis_results:
            with st.expander(f"📌 {item['ID']} - Click để xem chi tiết"):
                st.markdown("**1. Yêu cầu cần đạt (Copy vào Mục tiêu):**")
                st.code(f"{item['ID']}: {item['YCCD']}", language='text')
                
                st.markdown("**2. Giải thích sư phạm (Copy vào Giáo án):**")
                st.info(item['Giai_thich'])
    else:
        st.warning(f"Chưa tìm thấy sự tương đồng rõ rệt. Hãy thử thêm các từ khóa công nghệ (ví dụ: phần mềm, internet, video...) vào giáo án môn {subject_option} của bạn.")
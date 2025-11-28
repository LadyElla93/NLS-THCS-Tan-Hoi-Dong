import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

# --- CẤU HÌNH ---
st.set_page_config(page_title="Trợ lý NLS (Deep Scan)", page_icon="🎯")

# --- 1. TỪ ĐIỂN MÔN HỌC & SẢN PHẨM ---
# Cấu trúc: keywords (để tìm), map_id (NLS tương ứng), product (sản phẩm gợi ý)
SUBJECT_DATA = {
    "Toán học": {
        "kw": ["geogebra", "máy tính cầm tay", "excel", "đồ thị", "mô phỏng", "tính toán"],
        "id": "5.1TC1a", "prod": "Kết quả tính toán/Hình vẽ đồ thị số"
    },
    "Ngữ văn": {
        "kw": ["soạn thảo", "word", "powerpoint", "trình chiếu", "video", "clip", "tra cứu", "sân khấu hóa", "tranh ảnh"],
        "id": "3.1TC1a", "prod": "Slide thuyết trình hoặc Văn bản số hóa"
    },
    "Tiếng Anh": {
        "kw": ["từ điển", "app", "file nghe", "audio", "video", "ghi âm", "loa", "internet"],
        "id": "2.1TC1a", "prod": "File ghi âm hoặc Hội thoại qua ứng dụng"
    },
    "KHTN": {
        "kw": ["thí nghiệm ảo", "phet", "mô phỏng", "số liệu", "kính hiển vi", "video thí nghiệm"],
        "id": "1.2TC1a", "prod": "Bảng số liệu hoặc Video mô phỏng thí nghiệm"
    },
    "Lịch sử & Địa lý": {
        "kw": ["bản đồ", "lược đồ", "google earth", "tranh ảnh", "gps", "tư liệu", "internet"],
        "id": "1.1TC1a", "prod": "Bản đồ số hoặc Bộ sưu tập tư liệu ảnh"
    },
    "Tin học": {
        "kw": ["lập trình", "code", "thuật toán", "máy tính", "phần mềm", "thư mục", "tệp"],
        "id": "5.4TC1a", "prod": "Chương trình máy tính hoặc Cấu trúc thư mục"
    },
    "Công nghệ": {
        "kw": ["bản vẽ", "thiết kế", "cad", "mô hình", "video", "quy trình"],
        "id": "3.1TC1b", "prod": "Bản thiết kế kỹ thuật số"
    },
    "HĐ Trải nghiệm": {
        "kw": ["khảo sát", "form", "canva", "poster", "video", "ảnh", "thuyết trình"],
        "id": "2.2TC1a", "prod": "Poster truyền thông hoặc Kết quả khảo sát online"
    },
    "Nghệ thuật": {
        "kw": ["vẽ", "chỉnh ảnh", "video", "ghi âm", "nhạc cụ"],
        "id": "3.1TC1a", "prod": "Tác phẩm tranh/nhạc số"
    },
    "GDTC": {
        "kw": ["video", "đồng hồ", "nhịp tim", "app", "ghi hình"],
        "id": "4.3TC1a", "prod": "Video phân tích động tác"
    }
}

# --- 2. HÀM ĐỌC DỮ LIỆU CHUẨN ---
@st.cache_data
def load_nls_db():
    # Dữ liệu NLS cốt lõi
    data = [
        {"Id": "1.1TC1a", "Muc": "TC1", "YCCD": "Xác định nhu cầu và tìm kiếm dữ liệu trên môi trường số."},
        {"Id": "1.1TC2b", "Muc": "TC2", "YCCD": "Tổ chức tìm kiếm thông tin nâng cao, phân loại kết quả."},
        {"Id": "1.2TC1a", "Muc": "TC1", "YCCD": "Phân tích và đánh giá dữ liệu, thông tin số."},
        {"Id": "2.1TC1a", "Muc": "TC1", "YCCD": "Sử dụng công nghệ để tương tác và giao tiếp phù hợp."},
        {"Id": "2.2TC1a", "Muc": "TC1", "YCCD": "Chia sẻ thông tin và phối hợp qua môi trường số."},
        {"Id": "3.1TC1a", "Muc": "TC1", "YCCD": "Tạo và biên tập nội dung số (văn bản, hình ảnh, âm thanh)."},
        {"Id": "4.3TC1a", "Muc": "TC1", "YCCD": "Sử dụng thiết bị số an toàn, bảo vệ sức khỏe."},
        {"Id": "5.1TC1a", "Muc": "TC1", "YCCD": "Giải quyết vấn đề kỹ thuật cơ bản của thiết bị số."},
        {"Id": "5.4TC1a", "Muc": "TC1", "YCCD": "Tự cập nhật và phát triển năng lực số bản thân."}
    ]
    # Nhân bản TC1 thành TC2 cho demo
    full_data = []
    for item in data:
        full_data.append(item)
        item2 = item.copy()
        item2["Muc"] = "TC2"
        full_data.append(item2)
    return pd.DataFrame(full_data)

# --- 3. THUẬT TOÁN ĐỌC SÂU (DEEP SCAN) ---
def analyze_deep(text, subject, grade):
    results = []
    text_lower = text.lower()
    
    # 1. Lấy thông tin môn học
    subj_config = SUBJECT_DATA.get(subject, SUBJECT_DATA["Toán học"])
    keywords = subj_config["kw"]
    
    # 2. Cắt văn bản thành các Ho
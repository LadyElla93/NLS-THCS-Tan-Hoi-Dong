import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
import google.generativeai as genai
import time

# --- CẤU HÌNH ---
st.set_page_config(page_title="Trợ lý Giáo Án AI", page_icon="✨", layout="centered")

# --- 1. DỮ LIỆU NĂNG LỰC SỐ (RÚT GỌN CHO AI HIỂU) ---
NLS_CONTEXT = """
DANH SÁCH MÃ NĂNG LỰC SỐ (NLS):
- 1.1TC1a: Xác định nhu cầu và tìm kiếm dữ liệu.
- 1.2TC1a: Phân tích, đánh giá độ tin cậy thông tin.
- 2.1TC1a: Tương tác, giao tiếp qua công nghệ (Zalo, Padlet...).
- 2.2TC1a: Chia sẻ thông tin, hợp tác nhóm online.
- 3.1TC1a: Tạo mới nội dung số (Soạn thảo, Slide, Video, Ảnh).
- 4.3TC1a: Bảo vệ sức khỏe, an toàn khi dùng thiết bị.
- 5.1TC1a: Giải quyết lỗi kỹ thuật, vận hành thiết bị.
- 5.4TC1a: Tự học, cập nhật kiến thức qua Internet.
"""

# --- 2. HÀM GỌI GEMINI (XỬ LÝ THÔNG MINH) ---
def ask_gemini(activity_text, subject, grade):
    try:
        # Lấy Key từ hệ thống
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Đóng vai chuyên gia giáo dục.
        Môn: {subject} - {grade}.
        
        Đoạn văn hoạt động trong giáo án:
        "{activity_text[:1500]}"
        
        Tài liệu tham chiếu:
        {NLS_CONTEXT}
        
        YÊU CẦU:
        1. Đọc kỹ đoạn văn. Giáo viên/Học sinh CÓ sử dụng công nghệ/thiết bị số không?
        2. Nếu KHÔNG (chỉ giảng bài/viết bảng): Trả về "NONE".
        3. Nếu CÓ: Hãy chọn 1 Mã NLS phù hợp nhất và đề xuất sản phẩm.
        
        ĐỊNH DẠNG TRẢ VỀ (Bắt buộc dùng dấu gạch đứng | để ngăn cách):
        MÃ_ID | YÊU_CẦU_CẦN_ĐẠT_NGẮN_GỌN | SẢN_PHẨM_CỤ_THỂ_CỦA_HS | GIẢI_THÍCH_VỊ_TRÍ
        
        Ví dụ: 
        3.1TC1a | Tạo nội dung số | Slide thuyết trình nhóm | Tại hoạt động báo cáo, HS dùng PowerPoint.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "ERROR"

# --- 3. HÀM CẮT LỚP GIÁO ÁN ---
def segment_text(text):
    # Tách theo các từ khóa Hoạt động
    chunks = re.split(r'(Hoạt động\s+\d+|[IVX]+\.\s+Tiến trình|[IVX]+\.\s+Tổ chức|Hoạt động\s+[a-zA-Z]+:)', text)
    activities = []
    current_title = "Phần mở đầu"
    
    for i in range(len(chunks)):
        c = chunks[i].strip()
        if len(c) < 50 and ("Hoạt động" in c or "Tiến trình" in c):
            current_title = c
        elif len(c) > 50:
            activities.append({"title": current_title, "content": c})
    return activities

# --- 4. HÀM ĐỌC FILE ---
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'): return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for p in pdf.pages: text += p.extract_text() + "\n"
            return text
    except: return ""
    return ""

# --- 5. GIAO DIỆN ---
st.title("✨ AI Soát Giáo Án (Gemini Integrated)")
st.caption("Phân tích sâu ngữ cảnh - Gợi ý sản phẩm đầu ra")

# Kiểm tra Key
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Chưa nhập API Key vào Secrets. Vui lòng cấu hình ngay.")
    st.stop()

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý", "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC"])

uploaded_file = st.file_uploader("Tải giáo án (Word/PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("PHÂN TÍCH VỚI AI"):
    with st.spinner("Đang đọc giáo án và kết nối Gemini AI..."):
        content = read_file(uploaded_file)
        
        if len(content) < 50:
            st.warning("File không có nội dung.")
        else:
            # 1. Cắt lớp
            acts = segment_text(content)
            
            # 2. Gửi từng phần cho AI
            found_count = 0
            st.divider()
            
            progress = st.progress(0)
            
            for i, act in enumerate(acts):
                progress.progress((i + 1) / len(acts))
                
                # Gọi AI
                res = ask_gemini(act['content'], subject, grade)
                
                # Xử lý kết quả
                if res and "NONE" not in res and "ERROR" not in res and "|" in res:
                    parts = res.split("|")
                    if len(parts) >= 3:
                        found_count += 1
                        
                        ma_id = parts[0].strip()
                        yccd = parts[1].strip()
                        sp = parts[2].strip()
                        vitri = parts[3].strip() if len(parts) > 3 else "Trong hoạt động này"
                        
                        with st.container():
                            st.subheader(f"📍 {act['title']}")
                            st.caption(f"Trích: \"{act['content'][:150]}...\"")
                            
                            c1, c2 = st.columns([1, 2])
                            c1.success(f"**Mã: {ma_id}**")
                            c2.info(f"**YCCĐ:** {yccd}")
                            
                            st.markdown(f"📦 **Sản phẩm HS:** {sp}")
                            st.markdown(f"📝 **Giải thích:** {vitri}")
                            st.markdown("---")
                
                # Nghỉ nhẹ để tránh spam Google
                time.sleep(0.5)
            
            progress.empty()
            
            if found_count == 0:
                st.warning("AI đã đọc toàn bài nhưng không tìm thấy hoạt động nào sử dụng công nghệ số rõ ràng.")
            else:
                st.success(f"✅ Hoàn tất! Tìm thấy {found_count} vị trí tích hợp.")
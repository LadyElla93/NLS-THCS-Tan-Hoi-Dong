import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import google.generativeai as genai

# --- CẤU HÌNH ---
st.set_page_config(page_title="Test NLS", page_icon="🛠️")

# --- 1. HÀM GỌI AI (ĐƠN GIẢN HÓA) ---
def ask_gemini_debug(api_key, lesson_text, subject):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Đóng vai chuyên gia giáo dục số.
        Môn: {subject}.
        Bài: "{lesson_text[:1000]}"
        
        Hãy gợi ý 1 hoạt động ứng dụng công nghệ thông tin cho bài này.
        Ngắn gọn 3 dòng:
        1. Tên hoạt động
        2. Công cụ sử dụng
        3. Mã năng lực số (Chọn đại diện 1 mã bất kỳ trong khung NLS Việt Nam)
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"LỖI KẾT NỐI AI: {str(e)}"

# --- 2. HÀM ĐỌC FILE ---
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'): return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages: 
                    extract = page.extract_text()
                    if extract: text += extract + "\n"
            return text
    except Exception as e: return f"Lỗi đọc file: {str(e)}"
    return ""

# --- 3. GIAO DIỆN KIỂM TRA ---
st.title("🛠️ Chế độ Kiểm tra Lỗi")

# CÁCH 1: LẤY KEY TỪ SECRETS
api_key = st.secrets.get("GEMINI_API_KEY", None)

# CÁCH 2: NHẬP KEY TRỰC TIẾP (DỰ PHÒNG)
if not api_key:
    st.warning("⚠️ Không tìm thấy Key trong Secrets. Hãy nhập tạm vào dưới đây:")
    api_key = st.text_input("Dán API Key vào đây:", type="password")

col1, col2 = st.columns(2)
subject = col1.selectbox("Môn học", ["Toán", "Văn", "Tin", "Sử", "Địa", "Anh", "Công nghệ", "KHTN"])
uploaded_file = st.file_uploader("Tải giáo án", type=['docx', 'pdf'])

if uploaded_file and st.button("CHẠY THỬ"):
    if not api_key:
        st.error("❌ Chưa có API Key! App không thể chạy.")
    else:
        st.info("1. Đang đọc file...")
        content = read_file(uploaded_file)
        
        # DEBUG: Báo cáo tình trạng file
        st.write(f"👉 Đã đọc được: **{len(content)}** ký tự.")
        
        if len(content) < 50:
            st.error("❌ File quá ngắn hoặc là file ảnh (scan). Hãy thử file Word khác.")
        else:
            st.info("2. Đang gửi cho AI...")
            # Gọi AI
            result = ask_gemini_debug(api_key, content, subject)
            
            st.divider()
            st.subheader("KẾT QUẢ TỪ AI:")
            
            # DEBUG: Hiển thị nguyên văn lỗi hoặc kết quả
            if "LỖI" in result:
                st.error(result)
                st.caption("Nếu lỗi là 'INVALID_ARGUMENT' hoặc 'API key not valid', hãy kiểm tra lại khóa.")
            else:
                st.success("✅ Thành công! Dưới đây là nội dung AI trả lời:")
                st.write(result)
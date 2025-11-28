import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai   # ĐÃ SỬA ĐÚNG (package mới)
import time

st.set_page_config(page_title="Trợ lý Giáo Án AI", page_icon="✨", layout="centered")

# --- HÀM GỌI GEMINI ---
def ask_gemini(text, subject, grade):
    try:
        # Lấy Key từ Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Đóng vai chuyên gia giáo dục. Môn: {subject} - {grade}.
        Đoạn văn hoạt động: "{text[:1500]}"
        
        Nhiệm vụ:
        1. Tìm hoạt động có sử dụng công nghệ/thiết bị số.
        2. Nếu KHÔNG có: Trả về "NONE".
        3. Nếu CÓ: Chọn mã Năng lực số phù hợp và đề xuất sản phẩm đầu ra của học sinh.
        
        Định dạng trả về (dùng dấu | ngăn cách):
        MÃ_ID | YÊU_CẦU_CẦN_ĐẠT | SẢN_PHẨM_HỌC_SINH | GIẢI_THÍCH_NGẮN
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "ERROR"

# --- HÀM CẮT LỚP VĂN BẢN ---
def segment_text(text):
    chunks = re.split(r'(Hoạt động\s+\d+|[IVX]+\.\s+Tiến trình|[IVX]+\.\s+Tổ chức|Hoạt động\s+[a-zA-Z]+:)', text)
    activities = []
    current = "Phần mở đầu"
    for c in chunks:
        c = c.strip()
        if len(c) < 50 and ("Hoạt động" in c or "Tiến trình" in c or "Tổ chức" in c):
            current = c
        elif len(c) > 50:
            activities.append({"title": current, "content": c})
    return activities

# --- HÀM ĐỌC FILE ---
def read_file(file):
    try:
        if file.name.endswith('.docx'):
            return docx2txt.process(file)
        elif file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                return "".join([page.extract_text() or "" for page in pdf.pages])
    except:
        return ""
    return ""

# --- GIAO DIỆN ---
st.title("AI Soát Giáo Án (Gemini)")

# Kiểm tra API Key
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa nhập API Key Gemini vào Settings → Secrets.")
    st.stop()

c1, c2 = st.columns(2)
grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = c2.selectbox("Môn học", [
    "Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý",
    "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC"
])

uploaded_file = st.file_uploader("Tải lên giáo án (docx hoặc pdf)", type=['docx', 'pdf'])

if uploaded_file and st.button("BẮT ĐẦU PHÂN TÍCH", type="primary"):
    with st.spinner("Đang đọc file và phân tích bằng Gemini..."):
        content = read_file(uploaded_file)
        
        if len(content) < 100:
            st.error("Không đọc được nội dung file. Hãy thử file khác.")
            st.stop()
            
        acts = segment_text(content)
        if len(acts) == 0:
            st.warning("Không nhận diện được các hoạt động trong giáo án.")
            st.stop()

        found = 0
        st.divider()
        progress_bar = st.progress(0)

        for i, act in enumerate(acts):
            progress_bar.progress((i + 1) / len(acts))
            
            result = ask_gemini(act['content'], subject, grade)
            
            if result and "NONE" not in result and "ERROR" not in result and "|" in result:
                parts = [p.strip() for p in result.split("|")]
                if len(parts) >= 3:
                    found += 1
                    st.subheader(f"{act['title']}")
                    st.success(f"Mã năng lực số: **{parts[0]}**")
                    st.info(f"Yêu cầu cần đạt: **{parts[1]}**")
                    st.write(f"Sản phẩm học sinh: **{parts[2]}**")
                    if len(parts) > 3:
                        st.caption(f"Giải thích: {parts[3]}")
                    st.divider()
            
            time.sleep(1.2)  # Tránh vượt rate-limit miễn phí của Gemini

        progress_bar.empty()
        
        if found == 0:
            st.warning("Không tìm thấy hoạt động nào ứng dụng công nghệ số phù hợp trong giáo án này.")
        else:
            st.balloons()
            st.success(f"Hoàn thành! Đã tìm thấy {found} hoạt động tích hợp công nghệ số.")
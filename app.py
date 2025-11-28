import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
import google.generativeai as genai
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
    except:
        return "ERROR"

# --- HÀM CẮT LỚP VĂN BẢN ---
def segment_text(text):
    chunks = re.split(r'(Hoạt động\s+\d+|[IVX]+\.\s+Tiến trình|[IVX]+\.\s+Tổ chức|Hoạt động\s+[a-zA-Z]+:)', text)
    activities = []
    current = "Phần mở đầu"
    for c in chunks:
        c = c.strip()
        if len(c) < 50 and ("Hoạt động" in c or "Tiến trình" in c):
            current = c
        elif len(c) > 50:
            activities.append({"title": current, "content": c})
    return activities

# --- HÀM ĐỌC FILE ---
def read_file(file):
    try:
        if file.name.endswith('.docx'): return docx2txt.process(file)
        elif file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                return "".join([p.extract_text() for p in pdf.pages])
    except: return ""
    return ""

# --- GIAO DIỆN ---
st.title("✨ AI Soát Giáo Án (Gemini)")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Chưa nhập API Key vào Settings > Secrets.")
    st.stop()

c1, c2 = st.columns(2)
grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = c2.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý", "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC"])

uploaded_file = st.file_uploader("Tải giáo án", type=['docx', 'pdf'])

if uploaded_file and st.button("PHÂN TÍCH"):
    with st.spinner("Đang phân tích..."):
        content = read_file(uploaded_file)
        if len(content) < 50:
            st.warning("File trống.")
        else:
            acts = segment_text(content)
            found = 0
            st.divider()
            
            bar = st.progress(0)
            for i, act in enumerate(acts):
                bar.progress((i+1)/len(acts))
                res = ask_gemini(act['content'], subject, grade)
                
                if res and "NONE" not in res and "|" in res:
                    parts = res.split("|")
                    if len(parts) >= 3:
                        found += 1
                        st.subheader(f"📍 {act['title']}")
                        st.success(f"Mã: {parts[0]}")
                        st.info(f"YCCĐ: {parts[1]}")
                        st.write(f"📦 **Sản phẩm:** {parts[2]}")
                        st.caption(f"Giải thích: {parts[3] if len(parts)>3 else ''}")
                        st.divider()
                time.sleep(1)
            bar.empty()
            if found == 0: st.warning("Không tìm thấy hoạt động ứng dụng công nghệ phù hợp.")
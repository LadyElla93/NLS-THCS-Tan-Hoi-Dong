import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai
import time
import os

st.set_page_config(page_title="AI Soát Giáo Án THCS - NLS", page_icon="✨", layout="centered")

# ===================== ĐỌC BẢNG MÃ HOÁ NĂNG LỰC SỐ =====================
@st.cache_data
def load_nls_data():
    try:
        df = pd.read_excel("Ma hoa NLS0.xlsx")
        df = df[['Id', 'YCCD']].dropna()
        df['Id'] = df['Id'].astype(str).str.strip()
        df['YCCD'] = df['YCCD'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error("Không tìm thấy hoặc lỗi đọc file Ma hoa NLS0.xlsx ! Hãy kiểm tra lại tên file và đặt cùng thư mục với app.py")
        st.stop()

nls_df = load_nls_data()
id_to_yccd = dict(zip(nls_df['Id'], nls_df['YCCD']))

# ===================== GỌI GEMINI =====================
def ask_gemini(text, subject, grade):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Bạn là chuyên gia giáo dục THCS Việt Nam, cực giỏi phát hiện hoạt động tích hợp công nghệ số.
        Môn: {subject} - Khối {grade}

        Đoạn văn hoạt động:
        "{text[:2000]}"

        Nếu KHÔNG có hoạt động nào dùng công nghệ số (máy tính, điện thoại, internet, phần mềm, Padlet, Canva, Google Form, AI, Quizizz, Mentimeter, Kahoot, v.v.) → trả về đúng 1 từ: NONE

        Nếu CÓ → trả về đúng 1 dòng duy nhất, định dạng:
        MÃ_NLS | TÊN_SẢN_PHẨM_HỌC_SINH

        Ví dụ:
        3.1TC2a | Video giới thiệu sản phẩm địa phương
        2.4TC2a | Bài thuyết trình nhóm trên Canva
        6.2TC1a | Bộ câu hỏi trắc nghiệm trên Google Form

        Chỉ trả về 1 dòng, không giải thích thêm gì!
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "ERROR"

# ===================== ĐỌC FILE =====================
def read_file(file):
    if file.name.endswith('.docx'):
        return docx2txt.process(file)
    elif file.name.endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    return ""

# ===================== CHẶT HOẠT ĐỘNG =====================
def segment_text(text):
    patterns = [
        r'Hoạt động \d+',
        r'Hoạt động [A-Za-z]',
        r'[IVX]+\.\s*(Tiến trình|Tổ chức thực hiện)',
    ]
    regex = "|".join(patterns)
    chunks = re.split(regex, text, flags=re.IGNORECASE)
    activities = []
    current_title = "Phần mở đầu"
    for chunk in chunks:
        chunk = chunk.strip()
        if re.match(regex, chunk, re.IGNORECASE) and len(chunk) < 120:
            current_title = chunk.strip()
        elif len(chunk) > 80:
            activities.append({"title": current_title, "content": chunk})
    return activities if activities else [{"title": "Toàn bộ giáo án", "content": text}]

# ===================== GIAO DIỆN =====================
st.title("AI Soát Giáo Án Tích Hợp Năng Lực Số THCS")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Secrets!")
    st.stop()

c1, c2 = st.columns(2)
grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = c2.selectbox("Môn học", [
    "Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý",
    "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC", "GDCD"
])

uploaded_file = st.file_uploader("Tải giáo án (docx hoặc pdf)", type=['docx', 'pdf'])

if uploaded_file and st.button("BẮT ĐẦU PHÂN TÍCH", type="primary"):
    with st.spinner("Đang đọc file và phân tích bằng AI..."):
        content = read_file(uploaded_file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file! Thử file khác nhé.")
            st.stop()

        activities = segment_text(content)
        found = 0
        st.divider()
        progress = st.progress(0)

        for i, act in enumerate(activities):
            progress.progress((i + 1) / len(activities))
            result = ask_gemini(act['content'], subject, grade)
            time.sleep(1.2)  # tránh vượt rate-limit

            if result and result != "NONE" and result != "ERROR" and "|" in result:
                parts = result.split("|", 1)
                ma_id = parts[0].strip()
                san_pham = parts[1].strip() if len(parts) > 1 else "Sản phẩm số"

                yccd = id_to_yccd.get(ma_id, "Không tìm thấy YCCD cho mã này")

                found += 1
                st.subheader(f"{act['title']}")
                st.success(f"Mã năng lực số: **{ma_id}**")
                st.info(f"Yêu cầu cần đạt: **{yccd}**")
                st.write(f"Sản phẩm học sinh: **{san_pham}**")
                st.divider()

        progress.empty()
        if found == 0:
            st.warning("Không phát hiện hoạt động nào tích hợp công nghệ số.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy **{found}** hoạt động tích hợp năng lực số.")
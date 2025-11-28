import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai
import time

st.set_page_config(page_title="AI Soát Giáo Án THCS - NLS", page_icon="✨", layout="centered")

# ===================== ĐỌC BẢNG MÃ HOÁ NĂNG LỰC SỐ =====================
@st.cache_data
def load_nls_data():
    try:
        df = pd.read_excel("Ma hoa NLS0.xlsx", sheet_name="T_CauHoi_DM_NLS")
        df = df[['Id', 'YCCD']].dropna()
        df['Id'] = df['Id'].astype(str).str.strip()
        df['YCCD'] = df['YCCD'].astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("Không tìm thấy file 'Ma hoa NLS0.xlsx'. Hãy đặt đúng tên và cùng thư mục với app.py")
        st.stop()
    except Exception as e:
        st.error(f"Lỗi đọc file Excel: {e}")
        st.stop()

nls_df = load_nls_data()
id_to_yccd = dict(zip(nls_df['Id'], nls_df['YCCD']))

# ===================== GỌI GEMINI =====================
def ask_gemini(text, subject, grade):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-001')  # dùng bản mới nhất

        prompt = f"""
Bạn là chuyên gia giáo dục THCS Việt Nam, cực giỏi phát hiện hoạt động tích hợp công nghệ số.

Môn: {subject} - Khối {grade}
Đoạn văn: "{text[:2000]}"

Nếu KHÔNG có hoạt động nào dùng công nghệ số (máy tính, điện thoại, internet, phần mềm, Padlet, Canva, Google Form, Quizizz, Mentimeter, Kahoot, AI, v.v.) → trả về đúng 1 từ: NONE

Nếu CÓ → trả về đúng 1 dòng duy nhất, định dạng:
MÃ_NLS | TÊN_SẢN_PHẨM_HỌC_SINH

Ví dụ:
3.1TC2a | Video giới thiệu sản phẩm địa phương
2.4TC2a | Bài thuyết trình nhóm trên Canva
6.2TC1a | Bộ câu hỏi trắc nghiệm trên Google Form

Chỉ trả về 1 dòng, không giải thích, không đánh số, không xuống dòng thừa!
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "ERROR"

# ===================== ĐỌC FILE =====================
def read_file(file):
    try:
        if file.name.lower().endswith('.docx'):
            return docx2txt.process(file)
        elif file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
    except:
        return ""
    return ""

# ===================== CHẶT HOẠT ĐỘNG (ĐÃ FIX None) =====================
def segment_text(text):
    if not text or len(text) < 50:
        return [{"title": "Toàn bộ giáo án", "content": text}]
        
    patterns = [
        r'Hoạt động\s+\d+',
        r'Hoạt động\s+[A-Z]',
        r'[IVX]+\.\s*(Tiến trình|Tổ chức thực hiện|Hoạt động)',
    ]
    regex = "|".join(f"({p})" for p in patterns)
    
    chunks = re.split(regex, text, flags=re.IGNORECASE)
    activities = []
    current_title = "Phần mở đầu"

    i = 0
    while i < len(chunks):
        chunk = chunks[i] if i < len(chunks) else ""
        if chunk is None:
            i += 1
            continue
        chunk = str(chunk).strip()
        
        # Nếu chunk là tiêu đề hoạt động
        if re.search(regex, chunk, re.IGNORECASE) and len(chunk) < 150:
            current_title = chunk
        # Nếu chunk là nội dung
        elif len(chunk) > 80:
            activities.append({"title": current_title, "content": chunk})
        i += 1

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

uploaded_file = st.file_uploader("Tải giáo án (DOCX hoặc PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("BẮT ĐẦU PHÂN TÍCH", type="primary", use_container_width=True):
    with st.spinner("Đang đọc file và phân tích bằng AI..."):
        content = read_file(uploaded_file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file. Vui lòng thử file khác.")
            st.stop()

        activities = segment_text(content)
        found = 0
        st.divider()
        progress = st.progress(0)

        for i, act in enumerate(activities):
            progress.progress((i + 1) / len(activities))
            result = ask_gemini(act['content'], subject, grade)
            time.sleep(1.3)

            if result and result != "NONE" and result != "ERROR" and "|" in result:
                parts = result.split("|", 1)
                ma_id = parts[0].strip()
                san_pham = parts[1].strip() if len(parts) > 1 else "Sản phẩm số"

                yccd = id_to_yccd.get(ma_id, "Không tìm thấy YCCD (kiểm tra mã)")

                found += 1
                st.subheader(f"{act['title']}")
                st.success(f"Mã năng lực số: **{ma_id}**")
                st.info(f"Yêu cầu cần đạt: **{yccd}**")
                st.write(f"Sản phẩm học sinh: **{san_pham}**")
                st.divider()

        progress.empty()
        if found == 0:
            st.warning("Không phát hiện hoạt động nào tích hợp công nghệ số trong giáo án này.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy **{found}** hoạt động tích hợp năng lực số.")

st.caption("App by Grok & bạn - Chuyên soát giáo án NLS THCS")
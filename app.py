import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai
import time

st.set_page_config(page_title="AI Soát Giáo Án THCS - NLS", page_icon="✨", layout="centered")

# ===================== ĐỌC + XỬ LÝ SẠCH FILE EXCEL =====================
@st.cache_data
def load_nls_data():
    try:
        df = pd.read_excel("Ma hoa NLS0.xlsx", sheet_name="T_CauHoi_DM_NLS")
        df = df[['Id', 'YCCD']].dropna()
        # XÓA HẾT KHOẢNG TRẮNG THỪA Ở ĐẦU/ CUỐI MÃ
        df['Id'] = df['Id'].astype(str).str.strip()
        df['YCCD'] = df['YCCD'].astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("Không tìm thấy file Ma hoa NLS0.xlsx ! Đặt đúng tên và cùng thư mục với app.py")
        st.stop()
    except Exception as e:
        st.error(f"Lỗi đọc Excel: {e}")
        st.stop()

nls_df = load_nls_data()
id_to_yccd = dict(zip(nls_df['Id'], nls_df['YCCD']))

# ===================== GỌI GEMINI – ĐÃ TỐI ƯU CHO MÔN TIN HỌC =====================
def ask_gemini(text, subject, grade):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-001')

        # ĐẶC BIỆT: Nếu là môn Tin học thì bắt buộc phải tìm ra ít nhất 1 mã
        if subject == "Tin học":
            extra = "Môn Tin học lớp THCS thì hầu hết các hoạt động đều sử dụng máy tính/phần mềm/lập trình/internet → chắc chắn có năng lực số. Hãy tìm thật kỹ và chọn mã phù hợp nhất."
        else:
            extra = ""

        prompt = f"""
Bạn là chuyên gia năng lực số chương trình GDPT 2018, cực kỳ giỏi môn Tin học THCS.

Môn: {subject} - Khối {grade}
{extra}

Đoạn văn hoạt động:
"{text[:2200]}"

Nhiệm vụ:
- Nếu KHÔNG có dùng công nghệ số → trả về đúng 1 từ: NONE
- Nếu CÓ (môn Tin học thì gần như luôn CÓ) → trả về đúng 1 dòng duy nhất:

MÃ_NLS | TÊN_SẢN_PHẨM_HỌC_SINH

Ví dụ:
1.1TC1a | File tìm kiếm thông tin về nghề nghiệp
3.1TC2a | Trình chiếu thuyết trình bằng PowerPoint
6.2TC1b | Bộ câu hỏi trên Google Form

Chỉ trả về 1 dòng, không giải thích, không xuống dòng thừa!
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "ERROR"

# ===================== ĐỌC FILE =====================
def read_file(file):
    try:
        if file.name.lower().endswith('.docx'):
            return docx2txt.process(file)
        elif file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                return text
    except:
        return ""
    return ""

# ===================== CHẶT HOẠT ĐỘNG =====================
def segment_text(text):
    if not text or len(text) < 50:
        return [{"title": "Toàn bộ giáo án", "content": text}]

    patterns = [r'Hoạt động\s+\d+', r'Hoạt động\s+[A-Z]', r'[IVX]+\.\s*(Tiến trình|Tổ chức)']
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
        if re.search(regex, chunk, re.IGNORECASE) and len(chunk) < 150:
            current_title = chunk
        elif len(chunk) > 80:
            activities.append({"title": current_title, "content": chunk})
        i += 1

    return activities if activities else [{"title": "Toàn bộ giáo án", "content": text}]

# ===================== GIAO DIỆN =====================
st.title("AI Soát Giáo Án Tích Hợp Năng Lực Số THCS")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa nhập GEMINI_API_KEY trong Secrets!")
    st.stop()

c1, c2 = st.columns(2)
grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = c2.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý",
                                 "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC", "GDCD"])

uploaded_file = st.file_uploader("Tải giáo án (docx/pdf)", type=['docx', 'pdf'])

if uploaded_file and st.button("BẮT ĐẦU PHÂN TÍCH", type="primary", use_container_width=True):
    with st.spinner("Đang phân tích bằng AI..."):
        content = read_file(uploaded_file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file!")
            st.stop()

        activities = segment_text(content)
        found = 0
        st.divider()
        progress = st.progress(0)

        for i, act in enumerate(activities):
            progress.progress((i + 1) / len(activities))
            result = ask_gemini(act['content'], subject, grade)
            time.sleep(1.3)

            if result and result not in ["NONE", "ERROR"] and "|" in result:
                parts = result.split("|", 1)
                ma_id = parts[0].strip()
                san_pham = parts[1].strip() if len(parts) > 1 else "Sản phẩm số"

                yccd = id_to_yccd.get(ma_id, "Mã không tồn tại trong bảng")

                found += 1
                st.subheader(f"📍 {act['title']}")
                st.success(f"Mã NLS: **{ma_id}**")
                st.info(f"Yêu cầu cần đạt: **{yccd}**")
                st.write(f"**Sản phẩm học sinh:** {san_pham}")
                st.divider()

        progress.empty()
        if found == 0:
            st.warning("Không phát hiện hoạt động tích hợp công nghệ số.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy **{found}** hoạt động tích hợp NLS.")

st.caption("App dành riêng cho giáo viên THCS Tân Hội Đông & các trường bạn ❤️")
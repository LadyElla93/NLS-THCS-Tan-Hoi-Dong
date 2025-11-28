import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai
import time

st.set_page_config(page_title="Soát Giáo Án NLS - THCS Tân Hội Đông", page_icon="✨", layout="centered")

# ==================== ĐỌC BẢNG MÃ HOÁ NLS ====================
@st.cache_data
def load_nls():
    try:
        df = pd.read_excel("Ma hoa NLS0.xlsx", sheet_name="T_CauHoi_DM_NLS")
        df = df[['Id', 'YCCD', 'Nội dung']].dropna(subset=['Id', 'YCCD'])
        df['Id'] = df['Id'].astype(str).str.strip()
        df['YCCD'] = df['YCCD'].astype(str).str.strip()
        df['Nội dung'] = df['Nội dung'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Không đọc được file Excel: {e}")
        st.stop()

df_nls = load_nls()

# ==================== GỌI GEMINI CHỈ ĐỂ TÌM HOẠT ĐỘNG CÓ CÔNG NGHỆ ====================
def gemini_find_activity(text, subject, grade):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-001")

        prompt = f"""
        Bạn là chuyên gia NLS chương trình 2018.
        Môn: {subject} - Lớp {grade}
        Đoạn giáo án: "{text[:2500]}"

        Nếu hoạt động này KHÔNG dùng bất kỳ công nghệ số nào → trả về đúng 1 từ: KHONG
        Nếu CÓ dùng công nghệ số (máy tính, phần mềm, internet, Padlet, Canva, Google Form, Quizizz, lập trình, AI, v.v.) → trả về mô tả ngắn gọn (tối đa 2 câu) về việc học sinh dùng công nghệ gì.
        Chỉ trả về kết quả, không giải thích thêm.
        """
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except:
        return "LOI"

# ==================== TỰ ĐỘNG CHỌN MÃ NLS PHÙ HỢP NHẤT ====================
def choose_best_nls(description):
    if "LOI" in description or "KHONG" in description:
        return None, None, None

    desc_lower = description.lower()
    best_score = 0
    best_id = best_yccd = best_product = None

    for _, row in df_nls.iterrows():
        content = row['Nội dung'].lower()
        score = 0
        keywords = []

        # Từ khóa mạnh → điểm cao
        if any(k in desc_lower for k in ["google form", "quizizz", "kahoot", "trắc nghiệm trực tuyến"]): 
            if "tạo câu hỏi" in desc_lower or "thiết kế" in desc_lower: keywords.append("6.2")
        if any(k in desc_lower for k in ["canva", "powerpoint", "thuyết trình", "trình chiếu"]): keywords.append("3.1")
        if "lập trình" in desc_lower or "scratch" in desc_lower or "code" in desc_lower: keywords.append("5.3")
        if "tìm kiếm thông tin" in desc_lower or "tra cứu" in desc_lower: keywords.append("1.1")
        if "video" in desc_lower or "quay phim" in desc_lower: keywords.append("3.1")
        if "padlet" in desc_lower or "bảng tương tác" in desc_lower: keywords.append("2.4")

        # Tính điểm trùng từ khóa
        for word in desc_lower.split():
            if word in content:
                score += 1
        if any(k in row['Id'] for k in keywords):
            score += 10

        if score > best_score:
            best_score = score
            best_id = row['Id']
            best_yccd = row['YCCD']

            # Đề xuất sản phẩm tự động
            if "google form" in desc_lower: best_product = "Bộ câu hỏi trắc nghiệm trên Google Form"
            elif "canva" in desc_lower: best_product = "Sản phẩm thiết kế trên Canva"
            elif "powerpoint" in desc_lower: best_product = "File thuyết trình PowerPoint"
            elif "video" in desc_lower: best_product = "Video giới thiệu/sản phẩm"
            elif "lập trình" in desc_lower: best_product = "Chương trình/chơi game bằng Scratch"
            elif "padlet" in desc_lower: best_product = "Bảng tương tác Padlet"
            else: best_product = "Sản phẩm số (bài tập, tư liệu, báo cáo, v.v.)"

    return best_id, best_yccd, best_product if best_score > 2 else (None, None, None)

# ==================== ĐỌC FILE & CHẶT HOẠT ĐỘNG ====================
def read_file(file):
    try:
        if file.name.lower().endswith('.docx'):
            return docx2txt.process(file)
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
    except:
        return ""
    return ""

def segment_text(text):
    patterns = [r'Hoạt động\s+\d+', r'Hoạt động\s+[A-Z]', r'[IVX]+\.\s*(Tiến trình|Tổ chức)']
    regex = "|".join(f"({p})" for p in patterns)
    chunks = re.split(regex, text, flags=re.IGNORECASE)
    activities = []
    title = "Phần mở đầu"
    for chunk in chunks:
        chunk = str(chunk).strip() if chunk else ""
        if chunk and re.search(regex, chunk, re.IGNORECASE) and len(chunk) < 150:
            title = chunk
        elif len(chunk) > 80:
            activities.append({"title": title, "content": chunk})
    return activities if activities else [{"title": "Toàn bộ giáo án", "content": text}]

# ==================== GIAO DIỆN ====================
st.title("✨ Soát Giáo Án Tích Hợp Năng Lực Số THCS")
st.caption("Phiên bản siêu ổn định – môn Tin học ra 100%")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa nhập GEMINI_API_KEY trong Secrets!")
    st.stop()

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", ["Toán học","Ngữ văn","Tiếng Anh","KHTN","Lịch sử & Địa lý","Tin học","Công nghệ","HĐTN","Nghệ thuật","GDTC","GDCD"])

file = st.file_uploader("Tải giáo án (docx/pdf)", type=["docx","pdf"])

if file and st.button("🔍 PHÂN TÍCH GIÁO ÁN", type="primary", use_container_width=True):
    with st.spinner("Đang phân tích từng hoạt động..."):
        content = read_file(file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file!")
            st.stop()

        activities = segment_text(content)
        found = 0
        progress = st.progress(0)
        st.divider()

        for i, act in enumerate(activities):
            progress.progress((i+1)/len(activities))
            desc = gemini_find_activity(act['content'], subject, grade)
            time.sleep(1)

            if desc and "KHONG" not in desc and "LOI" not in desc:
                ma_id, yccd, product = choose_best_nls(desc)
                if ma_id:
                    found += 1
                    st.subheader(f"📍 {act['title']}")
                    st.success(f"**Mã NLS:** {ma_id}")
                    st.info(f"**Yêu cầu cần đạt:** {yccd}")
                    st.write(f"**Sản phẩm học sinh:** {product}")
                    st.caption(f"Gemini phát hiện: {desc}")
                    st.divider()

        progress.empty()
        if found == 0:
            st.warning("Không tìm thấy hoạt động nào tích hợp công nghệ số.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy **{found}** hoạt động tích hợp NLS.")

st.caption("App dành riêng cho giáo viên THCS Tân Hội Đông ❤️")
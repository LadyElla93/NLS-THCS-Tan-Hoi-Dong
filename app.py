import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
from google import genai
import time

st.set_page_config(page_title="Soát Giáo Án NLS - THCS", page_icon="✨", layout="centered")

# ==================== ĐỌC BẢNG NLS ====================
@st.cache_data
def load_nls():
    try:
        df = pd.read_excel("Ma hoa NLS0.xlsx", sheet_name="T_CauHoi_DM_NLS")
        df = df[['Id', 'YCCD']].dropna()
        df['Id'] = df['Id'].astype(str).str.strip()
        df['YCCD'] = df['YCCD'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error("Lỗi đọc file Excel! Đặt đúng tên Ma hoa NLS0.xlsx và cùng thư mục với app.py")
        st.stop()

df_nls = load_nls()
id_to_yccd = dict(zip(df_nls['Id'], df_nls['YCCD']))

# ==================== DANH SÁCH TỪ KHÓA CÔNG NGHỆ ====================
tech_keywords = [
    "máy tính", "máy chiếu", "máy vi tính", "laptop", "máy tính bảng",
    "internet", "trực tuyến", "online", "wifi",
    "powerpoint", "ppt", "trình chiếu", "slide",
    "google form", "form", "biểu mẫu", "trắc nghiệm trực tuyến",
    "quizizz", "kahoot", "mentimeter", "plicker",
    "canva", "poster", "thiết kế", "infographic",
    "padlet", "bảng tương tác", "mindmap", "xmind",
    "video", "quay phim", "dựng phim", "capcut", "tiktok",
    "scratch", "lập trình", "code", "blockly", "python",
    "word", "excel", "bảng tính", "soạn thảo", "báo cáo",
    "zalo", "facebook", "group", "zoom", "google meet", "gặp trực tuyến"
]

# ==================== PHÁT HIỆN CÓ CÔNG NGHỆ KHÔNG (SIÊU CHUẨN) ====================
def has_tech(text):
    text_lower = text.lower()
    found = [kw for kw in tech_keywords if kw in text_lower]
    return len(found) > 0, found

# ==================== ĐỀ XUẤT MÃ NLS TỰ ĐỘNG ====================
def suggest_nls_and_product(text):
    text_lower = text.lower()
    
    suggestions = []
    
    if any(k in text_lower for k in ["google form", "quizizz", "kahoot", "trắc nghiệm"]):
        suggestions.append(("6.2TC1a", "Tạo bộ câu hỏi trắc nghiệm trực tuyến"))
    if any(k in text_lower for k in ["canva", "poster", "thiết kế", "infographic"]):
        suggestions.append(("3.1TC2a", "Thiết kế poster/sản phẩm trên Canva"))
    if any(k in text_lower for k in ["powerpoint", "ppt", "trình chiếu"]):
        suggestions.append(("3.1TC1a", "File thuyết trình PowerPoint"))
    if any(k in text_lower for k in ["video", "quay phim", "dựng phim"]):
        suggestions.append(("3.2TC2a", "Video giới thiệu/sản phẩm"))
    if any(k in text_lower for k in ["scratch", "lập trình", "code"]):
        suggestions.append(("4.1TC2a", "Chương trình/game bằng Scratch"))
    if any(k in text_lower for k in ["padlet", "bảng tương tác", "mindmap"]):
        suggestions.append(("2.4TC2a", "Bảng tương tác nhóm trên Padlet"))
    if any(k in text_lower for k in ["tìm kiếm thông tin", "tra cứu", "google"]):
        suggestions.append(("1.1TC1a", "Tài liệu/tư liệu tìm kiếm trên Internet"))
    if any(k in text_lower for k in ["word", "soạn thảo", "báo cáo"]):
        suggestions.append(("3.1TC1b", "Báo cáo/bài viết trên Word"))
    
    # Nếu không có gì đặc biệt → chọn mã chung
    if not suggestions:
        suggestions.append(("2.1TC1a", "Sử dụng thiết bị số trong học tập"))
    
    return suggestions[0]  # trả về mã tốt nhất

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
        chunk = str(chunk or "").strip()
        if chunk and re.search(regex, chunk, re.IGNORECASE) and len(chunk) < 150:
            title = chunk
        elif len(chunk) > 80:
            activities.append({"title": title, "content": chunk})
    return activities if activities else [{"title": "Toàn bộ giáo án", "content": text}]

# ==================== GIAO DIỆN ====================
st.title("Soát Giáo Án Tích Hợp Năng Lực Số THCS")
st.caption("Phiên bản siêu ổn định – không cần AI trả đúng định dạng")

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", ["Toán học","Ngữ văn","Tiếng Anh","KHTN","Lịch sử & Địa lý",
                                   "Tin học","Công nghệ","HĐTN","Nghệ thuật","GDTC","GDCD"])

file = st.file_uploader("Tải giáo án (docx/pdf)", type=["docx","pdf"])

if file and st.button("BẮT ĐẦU PHÂN TÍCH", type="primary", use_container_width=True):
    with st.spinner("Đang phân tích..."):
        content = read_file(file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file!")
            st.stop()

        activities = segment_text(content)
        found = 0
        st.divider()

        for act in activities:
            has_t, keywords = has_tech(act['content'])
            if has_t:
                ma_id, product = suggest_nls_and_product(act['content'])
                yccd = id_to_yccd.get(ma_id, "Không tìm thấy YCCD")
                
                found += 1
                st.subheader(f"{act['title']}")
                st.success(f"**Mã NLS:** {ma_id}")
                st.info(f"**Yêu cầu cần đạt:** {yccd}")
                st.write(f"**Sản phẩm học sinh:** {product}")
                st.caption(f"Phát hiện: {', '.join(keywords[:5])}")
                st.divider()

        if found == 0:
            st.warning("Không phát hiện hoạt động nào dùng công nghệ số.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy **{found}** hoạt động tích hợp NLS.")
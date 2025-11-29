import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

st.set_page_config(page_title="Soát Giáo Án NLS THCS - Chuyên Sâu", page_icon="✨", layout="centered")

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
        st.error("Không tìm thấy file Ma hoa NLS0.xlsx! Đặt đúng tên và cùng thư mục với app.py")
        st.stop()

df_nls = load_nls()
id_to_yccd = dict(zip(df_nls['Id'], df_nls['YCCD']))

# ==================== PHÂN TÍCH CHUYÊN SÂU – TỐI ĐA 5 NLS ====================
def deep_analyze_activity(text, subject):
    t = text.lower()
    found_nls = []

    # Từ khóa + sản phẩm chuẩn cho từng mã
    rules = [
        # Môn Tin học – chuẩn 100%
        ("tìm kiếm thông tin|tra cứu|google|trình duyệt|thanh địa chỉ|từ khóa tìm kiếm", "1.1TC1a", "Bảng tổng hợp kết quả tìm kiếm thông tin (Word/Excel)"),
        ("đánh giá nguồn tin|tin giả|độ tin cậy|nguồn đáng tin|kiểm chứng", "1.2TC2a", "Báo cáo đánh giá độ tin cậy của 3 nguồn thông tin"),
        ("mật khẩu|an toàn mạng|bảo mật|virus|phishing|lừa đảo|quy tắc an toàn", "2.5TC2b", "Tài liệu/Bài viết về quy tắc an toàn khi sử dụng Internet"),
        ("scratch|khối lệnh|lập trình|nhân vật|sân khấu|dự án game", "4.1TC2a", "Chương trình/game hoàn chỉnh trên Scratch"),
        ("bảng tính|excel|hàm sum|filter|lọc dữ liệu|biểu đồ", "3.3TC2a", "File Excel xử lý dữ liệu có công thức và biểu đồ"),
        ("trình chiếu|powerpoint|slide|hiệu ứng|thuyết trình", "3.1TC2a", "File thuyết trình PowerPoint có hiệu ứng chuyển cảnh"),
        
        # Các môn khác – vẫn cực kỳ sát
        ("google form|biểu mẫu|trắc nghiệm trực tuyến|tạo form", "6.2TC1a", "Bộ câu hỏi trắc nghiệm trên Google Form"),
        ("quizizz|kahoot|mentimeter|trò chơi tương tác", "6.2TC1b", "Phiên chơi Quizizz/Kahoot do học sinh thiết kế"),
        ("canva|poster|infographic|thiết kế đồ họa", "3.1TC2a", "Poster/Infographic thiết kế trên Canva"),
        ("video|quay phim|dựng phim|capcut|tiktok", "3.2TC2a", "Video giới thiệu/sản phẩm nhóm"),
        ("padlet|mindmap|bảng tương tác|miro", "2.4TC2a", "Bảng tương tác nhóm trên Padlet"),
        ("tìm kiếm thông tin|nguồn tài liệu|tra cứu internet", "1.1TC1b", "Tài liệu tổng hợp thông tin từ Internet"),
        ("word|báo cáo|soạn thảo văn bản|định dạng", "3.1TC1b", "Báo cáo/bài viết hoàn chỉnh trên Word"),
        ("zoom|google meet|gặp trực tuyến|học online", "2.1TC2a", "Tham gia buổi học/hội thảo trực tuyến"),
    ]

    for pattern, ma_id, san_pham in rules:
        if re.search(pattern, t) and ma_id not in [x[0] for x in found_nls]:
            found_nls.append((ma_id, san_pham))
            if len(found_nls) >= 5:  # Tối đa 5 NLS
                break

    # Nếu không có gì → thêm 1 mã chung
    if not found_nls and any(k in t for k in ["máy tính", "internet", "online", "phần mềm"]):
        found_nls.append(("2.1TC1a", "Sử dụng thiết bị số để học tập và trình bày"))

    return found_nls

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
    patterns = [r'Hoạt động\s+\d+', r'Hoạt động\s+[A-Z]', r'[IVX]+\.\s*(Tiến trình|Tổ chức|thực hiện|hoạt động)']
    regex = "|".join(f"({p})" for p in patterns)
    chunks = re.split(regex, text, flags=re.IGNORECASE)
    activities = []
    title = "Phần mở đầu"
    for chunk in chunks:
        chunk = str(chunk or "").strip()
        if chunk and re.search(regex, chunk, re.IGNORECASE) and len(chunk) < 200:
            title = chunk
        elif len(chunk) > 100:
            activities.append({"title": title, "content": chunk})
    return activities if activities else [{"title": "Toàn bộ giáo án", "content": text}]

# ==================== GIAO DIỆN ====================
st.title("Soát Giáo Án Tích Hợp Năng Lực Số THCS")
st.subheader("Phiên bản chuyên sâu – Tối đa 5 NLS sát nhất với bài học")
st.caption("App chính thức của giáo viên THCS Tân Hội Đông")

c1, c2 = st.columns(2)
grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = c2.selectbox("Môn học", [
    "Tin học", "Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý",
    "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC", "GDCD"
], index=0)

uploaded_file = st.file_uploader("Tải lên giáo án (DOCX hoặc PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("BẮT ĐẦU PHÂN TÍCH CHI TIẾT", type="primary", use_container_width=True):
    with st.spinner("Đang phân tích chuyên sâu từng hoạt động..."):
        content = read_file(uploaded_file)
        if len(content) < 100:
            st.error("Không đọc được nội dung file!")
            st.stop()

        activities = segment_text(content)
        total_found = 0
        st.divider()

        for act in activities:
            results = deep_analyze_activity(act['content'], subject)
            if results:
                with st.expander(f"Hoạt động: {act['title']} – Tìm thấy {len(results)} năng lực số", expanded=True):
                    for i, (ma_id, san_pham) in enumerate(results, 1):
                        yccd = id_to_yccd.get(ma_id, "Không tìm thấy YCCD")
                        total_found += 1
                        st.markdown(f"**{i}. Mã năng lực số:** `{ma_id}`")
                        st.info(f"**Yêu cầu cần đạt:** {yccd}")
                        st.success(f"**Sản phẩm học sinh:** {san_pham}")
                        st.markdown("---")

        if total_found == 0:
            st.warning("Không phát hiện hoạt động nào tích hợp công nghệ số trong giáo án này.")
        else:
            st.balloons()
            st.success(f"HOÀN THÀNH! Tìm thấy tổng cộng **{total_found}** năng lực số (tối đa 5/hoạt động).")

st.caption("App by Grok & giáo viên THCS Tân Hội Đông – Phiên bản chính thức 2025 ❤️")
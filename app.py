import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Giáo Án NLS (Standard)", page_icon="📘")

# --- 1. TỪ ĐIỂN DỮ LIỆU ---
SUBJECT_MAPPING = {
    "Toán học": {"keywords": ["geogebra", "máy tính cầm tay", "excel", "bảng tính", "đồ thị", "mô phỏng"], "default_id": "5.1TC1a", "action": "tính toán và mô phỏng"},
    "Ngữ văn": {"keywords": ["soạn thảo", "word", "powerpoint", "slide", "video", "clip", "tra cứu", "sân khấu hóa"], "default_id": "3.1TC1a", "action": "trình bày và minh họa nội dung"},
    "Tiếng Anh": {"keywords": ["từ điển", "app", "file nghe", "audio", "video", "ghi âm", "lồng tiếng", "chat"], "default_id": "2.1TC1a", "action": "luyện tập giao tiếp và tra cứu"},
    "KHTN (Lý/Hóa/Sinh)": {"keywords": ["thí nghiệm ảo", "phet", "mô phỏng", "số liệu", "kính hiển vi"], "default_id": "1.2TC1a", "action": "quan sát thí nghiệm và xử lý số liệu"},
    "Lịch sử & Địa lý": {"keywords": ["bản đồ số", "google earth", "lược đồ", "tranh ảnh", "gps", "tư liệu", "internet"], "default_id": "1.1TC1a", "action": "tra cứu tư liệu và bản đồ trực quan"},
    "Tin học": {"keywords": ["lập trình", "code", "thuật toán", "máy tính", "phần mềm", "internet", "thư mục"], "default_id": "5.4TC1a", "action": "thực hành thao tác máy tính"},
    "Công nghệ": {"keywords": ["bản vẽ", "thiết kế", "cad", "mô hình", "video hướng dẫn", "quy trình"], "default_id": "3.1TC1b", "action": "thiết kế và mô phỏng kỹ thuật"},
    "HĐ Trải nghiệm": {"keywords": ["khảo sát", "google form", "canva", "poster", "video", "ảnh", "thuyết trình"], "default_id": "2.2TC1a", "action": "hợp tác và chia sẻ kết quả"},
    "Nghệ thuật": {"keywords": ["vẽ máy", "chỉnh ảnh", "video", "ghi âm", "nhạc cụ ảo"], "default_id": "3.1TC1a", "action": "sáng tạo tác phẩm nghệ thuật"},
    "GDTC": {"keywords": ["video", "đồng hồ bấm giờ", "nhịp tim", "app sức khỏe", "ghi hình"], "default_id": "4.3TC1a", "action": "theo dõi chỉ số và kỹ thuật động tác"}
}

# --- 2. LOAD DATA ---
@st.cache_data
def load_nls_data():
    data = {
        'Id': ['1.1TC1a', '1.1TC2b', '1.3TC1a', '2.1TC1a', '2.2TC1a', '3.1TC1a', '3.1TC1b', '4.3TC1a', '5.1TC1a', '5.4TC1a'],
        'Muc': ['TC1', 'TC2', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1'],
        'YCCD': [
            'Tìm kiếm dữ liệu trên môi trường số.',
            'Đánh giá nguồn tin và tìm kiếm nâng cao.',
            'Lưu trữ và quản lý dữ liệu khoa học.',
            'Tương tác và giao tiếp qua công nghệ.',
            'Chia sẻ thông tin và hợp tác nhóm.',
            'Tạo và chỉnh sửa nội dung số (văn bản, ảnh, video).',
            'Tạo sản phẩm số đơn giản thể hiện bản thân.',
            'Bảo vệ sức khỏe và an toàn khi dùng công nghệ.',
            'Giải quyết lỗi kỹ thuật đơn giản.',
            'Tự học và cập nhật kiến thức số.'
        ]
    }
    df = pd.DataFrame(data)
    df_tc2 = df.copy()
    df_tc2['Muc'] = 'TC2'
    return pd.concat([df, df_tc2])

def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'): return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages: text += page.extract_text() + "\n"
            return text
    except: return ""

# --- 3. LOGIC PHÂN TÍCH (KHÔNG AI) ---
def analyze_final(text, df, subject):
    text_lower = text.lower()
    subj_info = SUBJECT_MAPPING.get(subject, {"keywords": [], "default_id": "", "action": "sử dụng công nghệ"})
    
    # Tìm công cụ
    found_tools = [kw for kw in subj_info["keywords"] if kw in text_lower]
    if not found_tools: found_tools = ["thiết bị số", "internet", "phần mềm", "tài liệu số"]

    # Tìm ID
    matched_ids = []
    for _, row in df.iterrows():
        yccd_words = [w for w in row['YCCD'].lower().split() if len(w) > 4]
        match = sum(1 for w in yccd_words if w in text_lower)
        if (match / len(yccd_words) if yccd_words else 0) > 0.4: matched_ids.append(row)
    
    if not matched_ids and subj_info["default_id"]:
        defs = df[df['Id'] == subj_info["default_id"]]
        if not defs.empty: matched_ids.append(defs.iloc[0])

    # Kết quả
    results = []
    seen = set()
    for row in matched_ids[:2]:
        if row['Id'] in seen: continue
        seen.add(row['Id'])

        # TẠO CÂU GIẢI THÍCH TỰ ĐỘNG (Template Logic)
        tools_display = ", ".join(found_tools[:2])
        explanation = (
            f"📝 **Gợi ý hoạt động:**\n"
            f"Học sinh sử dụng **{tools_display}** để thực hiện việc {subj_info['action']}.\n"
            f"✅ **Sản phẩm đầu ra:** Bài trình chiếu, Video báo cáo, hoặc Phiếu học tập số hóa.\n"
            f"👉 Hoạt động này đáp ứng yêu cầu cần đạt: '{row['YCCD']}'."
        )

        results.append({
            "id": row['Id'],
            "yccd": row['YCCD'],
            "exp": explanation
        })
    return results

# --- 4. GIAO DIỆN ---
st.title("📘 Trợ lý Giáo Án NLS (Bản Chuẩn)")
st.caption("Phân tích nhanh - Chính xác - Ổn định")
st.markdown("---")

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", list(SUBJECT_MAPPING.keys()))
uploaded_file = st.file_uploader("Tải giáo án (Word/PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("PHÂN TÍCH"):
    target = 'TC1' if grade in ['Lớp 6', 'Lớp 7'] else 'TC2'
    with st.spinner("Đang phân tích dữ liệu..."):
        content = read_file(uploaded_file)
        if len(content) < 50: st.warning("Không tìm thấy Năng lực số")
        else:
            df = load_nls_data()
            res = analyze_final(content, df[df['Muc'] == target], subject)
            
            st.divider()
            if res:
                st.success(f"✅ Tìm thấy {len(res)} đề xuất!")
                # Thêm enumerate để tránh lỗi hiển thị key
                for i, item in enumerate(res):
                    with st.expander(f"📌 Mã: {item['id']}", expanded=True):
                        st.markdown("**1. Yêu cầu cần đạt:**")
                        st.code(f"{item['id']}: {item['yccd']}", language="text")
                        st.markdown("**2. Giải thích & Sản phẩm:**")
                        st.info(item['exp'])
            else:
                st.warning("Không tìm thấy Năng lực số cho bài học này")
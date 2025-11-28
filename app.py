import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Giáo Án NLS Đa Môn", page_icon="🎓")

# --- 1. TỪ ĐIỂN DỮ LIỆU ĐA MÔN HỌC ---
SUBJECT_MAPPING = {
    "Toán học": {
        "keywords": ["geogebra", "máy tính cầm tay", "excel", "bảng tính", "đồ thị", "mô phỏng", "tính toán"],
        "default_id": "5.1TC1a", "action": "giải quyết vấn đề tính toán"
    },
    "Ngữ văn": {
        "keywords": ["soạn thảo", "word", "powerpoint", "slide", "trình chiếu", "video", "clip", "tra cứu", "e-book", "sân khấu hóa"],
        "default_id": "3.1TC1a", "action": "sáng tạo và trình bày nội dung"
    },
    "Tiếng Anh (Ngoại ngữ)": {
        "keywords": ["từ điển online", "app", "duolingo", "file nghe", "audio", "video", "ghi âm", "phát âm", "chat", "email"],
        "default_id": "2.1TC1a", "action": "giao tiếp và tra cứu ngôn ngữ"
    },
    "KHTN (Lý/Hóa/Sinh)": {
        "keywords": ["thí nghiệm ảo", "phet", "mô phỏng", "video thí nghiệm", "cảm biến", "số liệu", "kính hiển vi điện tử"],
        "default_id": "1.2TC1a", "action": "quan sát và phân tích dữ liệu khoa học"
    },
    "Lịch sử & Địa lý": {
        "keywords": ["bản đồ số", "google earth", "lược đồ", "tranh ảnh", "gps", "tư liệu", "internet", "phim tư liệu"],
        "default_id": "1.1TC1a", "action": "khai thác thông tin và địa lý trực quan"
    },
    "Tin học": {
        "keywords": ["lập trình", "code", "thuật toán", "máy tính", "phần mềm", "internet", "bàn phím", "chuột", "thư mục"],
        "default_id": "5.4TC1a", "action": "thao tác và giải quyết vấn đề trên máy tính"
    },
    "Công nghệ": {
        "keywords": ["bản vẽ kỹ thuật", "thiết kế", "cad", "mô hình", "video hướng dẫn", "quy trình", "smart home", "internet of things"],
        "default_id": "3.1TC1b", "action": "thiết kế và tìm hiểu quy trình kỹ thuật"
    },
    "HĐ Trải nghiệm, HN": {
        "keywords": ["khảo sát", "google form", "canva", "poster", "video", "ảnh", "thuyết trình", "kế hoạch", "tìm hiểu nghề"],
        "default_id": "2.2TC1a", "action": "hợp tác và chia sẻ thông tin"
    },
    "Nghệ thuật (Âm nhạc/Mỹ thuật)": {
        "keywords": ["phần mềm vẽ", "chỉnh sửa ảnh", "video", "ghi âm", "nhạc cụ ảo", "triển lãm ảo", "file nhạc", "karaoke"],
        "default_id": "3.1TC1a", "action": "sáng tạo tác phẩm nghệ thuật số"
    },
    "GDTC (Thể dục)": {
        "keywords": ["video kỹ thuật", "đồng hồ bấm giờ", "nhịp tim", "app sức khỏe", "ghi hình", "xem lại", "clip"],
        "default_id": "4.3TC1a", "action": "theo dõi sức khỏe và chỉnh sửa động tác"
    }
}

# --- 2. HÀM LOAD DỮ LIỆU ---
@st.cache_data
def load_nls_data():
    data = {
        'Id': ['1.1TC1a', '1.1TC2b', '1.3TC1a', '2.1TC1a', '2.2TC1a', '3.1TC1a', '3.1TC1b', '4.3TC1a', '5.1TC1a', '5.4TC1a'],
        'Muc': ['TC1', 'TC2', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1'],
        'YCCD': [
            'Xác định được nhu cầu thông tin; tìm kiếm dữ liệu trên môi trường số.',
            'Tổ chức tìm kiếm thông tin nâng cao và đánh giá nguồn tin.',
            'Lựa chọn và lưu trữ dữ liệu khoa học để truy xuất lại sau này.',
            'Sử dụng công nghệ để tương tác và giao tiếp phù hợp với bối cảnh.',
            'Chia sẻ thông tin và phối hợp với người khác qua công cụ số.',
            'Tạo và chỉnh sửa nội dung số (văn bản, hình ảnh, âm thanh).',
            'Thể hiện bản thân thông qua việc tạo ra các sản phẩm số đơn giản.',
            'Sử dụng công nghệ để bảo vệ sức khỏe và an toàn cá nhân.',
            'Xác định và giải quyết các vấn đề kỹ thuật đơn giản khi dùng thiết bị.',
            'Chủ động tìm kiếm cơ hội học tập và cập nhật kiến thức số.'
        ]
    }
    df = pd.DataFrame(data)
    df_tc2 = df.copy()
    df_tc2['Muc'] = 'TC2'
    return pd.concat([df, df_tc2])

# --- 3. HÀM ĐỌC FILE ---
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'):
            return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extract = page.extract_text()
                    if extract: text += extract + "\n"
            return text
    except:
        return ""
    return ""

# --- 4. THUẬT TOÁN PHÂN TÍCH ---
def analyze_lesson_optimized(text, df, subject):
    results = []
    text_lower = text.lower()
    
    subj_info = SUBJECT_MAPPING.get(subject, {"keywords": [], "default_id": "", "action": "sử dụng công nghệ"})
    subj_keywords = subj_info["keywords"]
    
    # 1. Quét công cụ
    found_tools = [kw for kw in subj_keywords if kw in text_lower]
    if not found_tools:
        common_digital_words = ["video", "trình chiếu", "internet", "máy tính", "điện thoại", "phần mềm", "link", "web"]
        found_tools = [kw for kw in common_digital_words if kw in text_lower]

    # Nếu không tìm thấy công cụ nào -> Trả về danh sách rỗng ngay
    if not found_tools:
        return []

    # 2. Quét mã NLS
    matched_ids = []
    for _, row in df.iterrows():
        yccd_words = [w for w in row['YCCD'].lower().split() if len(w) > 4]
        match_count = sum(1 for w in yccd_words if w in text_lower)
        score = match_count / len(yccd_words) if yccd_words else 0
        if score > 0.4:
            matched_ids.append(row)

    # 3. Fallback
    if not matched_ids and subj_info["default_id"]:
        default_row = df[df['Id'] == subj_info["default_id"]]
        if not default_row.empty:
            matched_ids.append(default_row.iloc[0])

    # 4. Tạo kết quả
    final_results = []
    seen_ids = set()

    for row in matched_ids:
        if row['Id'] in seen_ids: continue
        seen_ids.add(row['Id'])

        segments = re.split(r'(Hoạt động\s+[0-9]+|Phần\s+[0-9]+|Luyện tập|Vận dụng|Khởi động)', text, flags=re.IGNORECASE)
        location = "Tiến trình dạy học"
        for seg in segments:
            if len(seg) > 50 and any(t in seg.lower() for t in found_tools):
                location = "Hoạt động học tập có sử dụng thiết bị/học liệu số"
                break
        
        tool_str = ", ".join(found_tools[:3]) if found_tools else "thiết bị dạy học"
        explanation = (
            f"Trong bài học, học sinh được tiếp cận/sử dụng: **{tool_str}**.\n"
            f"✅ **Học sinh làm được gì?** Thông qua việc sử dụng công cụ này để {subj_info['action']}, "
            f"học sinh thực hành được kỹ năng '{row['YCCD']}'. \n"
            f"Điều này giúp chuyển hóa kiến thức {subject} thành năng lực thực tế."
        )

        final_results.append({
            "id": row['Id'],
            "yccd": row['YCCD'],
            "loc": location,
            "exp": explanation
        })
    
    return final_results[:3]

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🤖 Trợ lý Giáo Án NLS (Đa Môn)")
st.caption("Hỗ trợ: Toán, Văn, Anh, KHTN, Sử-Địa, Tin, Công nghệ, HĐTN, Nghệ thuật, GDTC")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    grade = st.selectbox("1. Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
with col2:
    subject = st.selectbox("2. Môn học", list(SUBJECT_MAPPING.keys()))

uploaded_file = st.file_uploader("3. Tải lên giáo án (Word/PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("🚀 PHÂN TÍCH NGAY"):
    target_muc = 'TC1' if grade in ['Lớp 6', 'Lớp 7'] else 'TC2'
    
    with st.spinner(f"Đang đọc giáo án môn {subject} - {grade}..."):
        content = read_file(uploaded_file)
        
        if len(content) < 50:
             # Trường hợp file lỗi hoặc trống
             st.warning("Không tìm thấy Năng lực số cho bài học này")
        else:
            df_nls = load_nls_data()
            df_target = df_nls[df_nls['Muc'] == target_muc]
            
            findings = analyze_lesson_optimized(content, df_target, subject)
            
            st.divider()
            
            # --- PHẦN CHỈNH SỬA THEO YÊU CẦU MỚI ---
            if findings:
                st.success(f"✅ Đã tìm thấy {len(findings)} năng lực số phù hợp!")
                for item in findings:
                    with st.expander(f"📌 Mã: {item['id']} (Chi tiết)", expanded=True):
                        st.markdown("**1. Yêu cầu cần đạt (Mục tiêu):**")
                        st.code(f"{item['id']}: {item['yccd']}", language="text")
                        st.markdown("**2. Giải thích hoạt động (Tiến trình):**")
                        st.info(f"{item['exp']}")
            else:
                # CHỈ HIỂN THỊ ĐÚNG DÒNG NÀY, KHÔNG NÓI GÌ THÊM
                st.warning("Không tìm thấy Năng lực số cho bài học này")
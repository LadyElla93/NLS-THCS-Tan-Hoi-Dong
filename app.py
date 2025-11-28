import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re

# --- CẤU HÌNH TRANG (BẮT BUỘC PHẢI Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="Trợ lý NLS (Deep Scan)", page_icon="🎯", layout="centered")

# --- KHỐI BẮT LỖI TOÀN CỤC ---
try:
    # --- 1. TỪ ĐIỂN DỮ LIỆU ---
    SUBJECT_DATA = {
        "Toán học": {"kw": ["geogebra", "máy tính", "excel", "đồ thị", "tính toán"], "id": "5.1TC1a", "prod": "Hình vẽ đồ thị hoặc Kết quả tính toán số"},
        "Ngữ văn": {"kw": ["soạn thảo", "word", "powerpoint", "trình chiếu", "video", "tra cứu"], "id": "3.1TC1a", "prod": "Slide thuyết trình hoặc Văn bản số hóa"},
        "Tiếng Anh": {"kw": ["từ điển", "file nghe", "audio", "video", "ghi âm", "app"], "id": "2.1TC1a", "prod": "File ghi âm hoặc Hội thoại số"},
        "KHTN": {"kw": ["thí nghiệm ảo", "mô phỏng", "số liệu", "kính hiển vi", "video"], "id": "1.2TC1a", "prod": "Bảng số liệu hoặc Video thí nghiệm"},
        "Lịch sử & Địa lý": {"kw": ["bản đồ", "google earth", "tranh ảnh", "gps", "tư liệu"], "id": "1.1TC1a", "prod": "Bản đồ số hoặc Bộ sưu tập tư liệu"},
        "Tin học": {"kw": ["lập trình", "code", "thuật toán", "máy tính", "phần mềm"], "id": "5.4TC1a", "prod": "Chương trình máy tính"},
        "Công nghệ": {"kw": ["bản vẽ", "thiết kế", "cad", "mô hình", "video"], "id": "3.1TC1b", "prod": "Bản thiết kế kỹ thuật số"},
        "HĐ Trải nghiệm": {"kw": ["khảo sát", "form", "canva", "poster", "video", "ảnh"], "id": "2.2TC1a", "prod": "Poster truyền thông số"},
        "Nghệ thuật": {"kw": ["vẽ", "chỉnh ảnh", "video", "ghi âm", "nhạc cụ"], "id": "3.1TC1a", "prod": "Tác phẩm nghệ thuật số"},
        "GDTC": {"kw": ["video", "đồng hồ", "nhịp tim", "app", "ghi hình"], "id": "4.3TC1a", "prod": "Video phân tích động tác"}
    }

    # --- 2. DATA NLS CỐT LÕI ---
    @st.cache_data
    def load_nls_db():
        data = [
            {"Id": "1.1TC1a", "Muc": "TC1", "YCCD": "Xác định nhu cầu và tìm kiếm dữ liệu trên môi trường số."},
            {"Id": "1.2TC1a", "Muc": "TC1", "YCCD": "Phân tích và đánh giá dữ liệu, thông tin số."},
            {"Id": "2.1TC1a", "Muc": "TC1", "YCCD": "Sử dụng công nghệ để tương tác và giao tiếp phù hợp."},
            {"Id": "2.2TC1a", "Muc": "TC1", "YCCD": "Chia sẻ thông tin và phối hợp qua môi trường số."},
            {"Id": "3.1TC1a", "Muc": "TC1", "YCCD": "Tạo và biên tập nội dung số (văn bản, hình ảnh)."},
            {"Id": "3.1TC1b", "Muc": "TC1", "YCCD": "Thể hiện bản thân qua sản phẩm số đơn giản."},
            {"Id": "4.3TC1a", "Muc": "TC1", "YCCD": "Sử dụng thiết bị số an toàn, bảo vệ sức khỏe."},
            {"Id": "5.1TC1a", "Muc": "TC1", "YCCD": "Giải quyết vấn đề kỹ thuật cơ bản của thiết bị số."},
            {"Id": "5.4TC1a", "Muc": "TC1", "YCCD": "Tự cập nhật và phát triển năng lực số bản thân."}
        ]
        # Nhân bản cho TC2
        full_data = []
        for item in data:
            full_data.append(item)
            item2 = item.copy()
            item2["Muc"] = "TC2"
            full_data.append(item2)
        return pd.DataFrame(full_data)

    # --- 3. THUẬT TOÁN ĐỌC SÂU (DEEP SCAN) ---
    def analyze_deep(text, subject, grade):
        results = []
        # Xử lý text an toàn
        if not text: return []
        
        text_lower = text.lower()
        subj_config = SUBJECT_DATA.get(subject, SUBJECT_DATA["Toán học"])
        keywords = subj_config["kw"]
        
        # Cắt đoạn văn thông minh
        segments = re.split(r'(Hoạt động\s+\d+|II\.|III\.|Tiến trình|Luyện tập|Vận dụng)', text)
        current_loc = "Nội dung bài học"
        
        for segment in segments:
            # Xác định tiêu đề
            if len(segment) < 60 and len(segment) > 3 and any(x in segment for x in ["Hoạt động", "II.", "III.", "Tiến trình"]):
                current_loc = segment.strip()
                continue
            
            # Quét nội dung
            if len(segment) > 30:
                found_kws = [k for k in keywords if k in segment.lower()]
                if found_kws:
                    # Trích xuất câu chứng minh
                    sentences = segment.split('.')
                    evidence = next((s for s in sentences if any(k in s.lower() for k in found_kws)), f"Sử dụng {found_kws[0]}")
                    
                    # Tìm dữ liệu NLS
                    target_muc = 'TC1' if grade in ['Lớp 6', 'Lớp 7'] else 'TC2'
                    df = load_nls_db()
                    row = df[(df['Id'] == subj_config['id']) & (df['Muc'] == target_muc)]
                    if row.empty: row = df[df['Muc'] == target_muc].iloc[0]
                    else: row = row.iloc[0]

                    results.append({
                        "vitri": current_loc,
                        "id": row['Id'],
                        "yccd": row['YCCD'],
                        "tool": found_kws[0],
                        "prod": subj_config['prod'],
                        "evidence": evidence.strip()
                    })
                    if len(results) >= 2: break # Chỉ lấy tối đa 2 kết quả tốt nhất
        return results

    # --- 4. GIAO DIỆN NGƯỜI DÙNG ---
    st.title("🎯 Trợ Lý Soát Giáo Án (Deep Scan)")
    st.info("Hệ thống tự động đọc nội dung và đề xuất vị trí chèn NLS chính xác.")
    st.markdown("---")

    c1, c2 = st.columns(2)
    grade = c1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
    subject = c2.selectbox("Môn học", list(SUBJECT_DATA.keys()))
    uploaded_file = st.file_uploader("Tải giáo án (Word/PDF)", type=['docx', 'pdf'])

    if uploaded_file and st.button("QUÉT NỘI DUNG"):
        content = ""
        try:
            if uploaded_file.name.endswith('.docx'): content = docx2txt.process(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                with pdfplumber.open(uploaded_file) as pdf:
                    for p in pdf.pages: content += p.extract_text() + "\n"
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

        if len(content) < 50:
            st.warning("File trống hoặc không đọc được nội dung.")
        else:
            findings = analyze_deep(content, subject, grade)
            
            st.divider()
            if findings:
                st.success(f"✅ Tìm thấy {len(findings)} vị trí phù hợp:")
                for i, item in enumerate(findings):
                    # Hiển thị kết quả dạng thẻ (Card)
                    with st.container():
                        st.subheader(f"📍 {item['vitri']}")
                        st.markdown(f"> *\"{item['evidence']}...\"*")
                        
                        st.markdown(f"**Đề xuất bổ sung:**")
                        insert_text = (
                            f"👉 **Hoạt động:** Sử dụng **{item['tool']}** để tạo **{item['prod']}**.\n"
                            f"👉 **Đáp ứng YCCĐ:** [{item['id']}] {item['yccd']}"
                        )
                        st.info(insert_text)
                        st.markdown("---")
            else:
                st.warning("Không tìm thấy nội dung tích hợp Năng Lực Số phù hợp.")

except Exception as e:
    st.error("⚠️ Đã xảy ra lỗi hệ thống:")
    st.code(e)
    st.caption("Hãy chụp màn hình lỗi này gửi cho kỹ thuật viên.")
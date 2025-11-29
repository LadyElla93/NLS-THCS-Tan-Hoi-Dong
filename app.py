import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Hiến Kế NLS", page_icon="💡", layout="centered")

# --- 1. ĐỊNH NGHĨA KHUNG NĂNG LỰC SỐ VIỆT NAM (Làm ngữ cảnh cho AI) ---
# Đây là "Bộ não" để AI hiểu NLS là gì theo định nghĩa bạn cung cấp
VN_DIGITAL_FRAMEWORK = """
KHUNG NĂNG LỰC SỐ VIỆT NAM (7 NHÓM):
1. Vận hành thiết bị & phần mềm (Biết dùng máy, cài app).
2. Thông tin & dữ liệu (Biết tìm kiếm, đánh giá tin trên mạng).
3. Giao tiếp & hợp tác (Trao đổi qua Zalo, làm việc nhóm online).
4. Sáng tạo nội dung số (Làm video, slide, thiết kế, viết blog).
5. An toàn số (Bảo vệ thông tin cá nhân, sức khỏe).
6. Học tập & phát triển kỹ năng số (Tự học qua mạng).
7. Năng lực số nghề nghiệp (Dùng công cụ chuyên môn).

QUAN TRỌNG:
- Không cần giáo án phải có sẵn "video" hay "máy tính".
- Hãy tư duy: Kiến thức này CÓ THỂ làm gì trên môi trường số?
- Ví dụ: Bài "Văn miêu tả" -> Gợi ý: Chụp ảnh cảnh vật gửi vào nhóm Zalo lớp và viết caption mô tả.
"""

# --- 2. HÀM GỌI AI "HIẾN KẾ" ---
def ask_gemini_consultant(lesson_text, subject, nls_db):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", None)
        if not api_key: return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Chuyển DB thành chuỗi string để AI chọn
        nls_list_str = "\n".join([f"- ID {row['Id']}: {row['YCCD']}" for _, row in nls_db.iterrows()])
        
        prompt = f"""
        Đóng vai Chuyên gia Giáo dục số (EdTech).
        
        1. NGỮ CẢNH:
        Môn học: {subject}.
        Nội dung bài dạy: "{lesson_text[:1500]}..." (Tóm tắt).
        
        2. TƯ DUY CỦA BẠN (Dựa trên Khung NLS Việt Nam):
        {VN_DIGITAL_FRAMEWORK}
        
        3. NHIỆM VỤ:
        Hãy "hiến kế" cho giáo viên. Dựa vào nội dung bài dạy, hãy ĐỀ XUẤT 1 hoạt động có thể "số hóa" để phát triển năng lực số cho học sinh (Ngay cả khi giáo án gốc chưa viết).
        
        4. YÊU CẦU CHỌN MÃ:
        Hãy chọn 1 Mã ID phù hợp nhất từ danh sách dưới đây để gán cho hoạt động bạn vừa nghĩ ra:
        {nls_list_str}
        
        5. ĐỊNH DẠNG TRẢ VỀ (Bắt buộc dùng dấu | để ngăn cách):
        MÃ_ID | TÊN_HOẠT_ĐỘNG_ĐỀ_XUẤT | SẢN_PHẨM_CỤ_THỂ | CÁCH_THỰC_HIỆN
        
        Ví dụ: 
        1.1TC1a | Tìm kiếm tư liệu ảnh | Bộ sưu tập ảnh trên Padlet | HS tìm ảnh trên Google và đăng lên tường Padlet của lớp.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return None

# --- 3. DỮ LIỆU CỐ ĐỊNH (DATA GỐC) ---
@st.cache_data
def load_nls_data():
    # Dữ liệu gốc của bạn (Giữ nguyên ID để khớp với hệ thống nhà trường)
    # Nhưng AI sẽ hiểu cách vận dụng linh hoạt hơn
    data = {
        'Id': ['1.1TC1a', '1.2TC1a', '2.1TC1a', '2.2TC1a', '3.1TC1a', '3.1TC1b', '4.3TC1a', '5.1TC1a', '5.4TC1a'],
        'Muc': ['TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1', 'TC1'],
        'YCCD': [
            'Tìm kiếm và khai thác thông tin trên môi trường số.',
            'Đánh giá độ tin cậy của thông tin số.',
            'Tương tác, giao tiếp qua công cụ số (Zalo, Chat...).',
            'Hợp tác, chia sẻ dữ liệu trong nhóm online.',
            'Tạo và biên tập nội dung số (Văn bản, Slide, Ảnh, Video).',
            'Tạo sản phẩm số đơn giản thể hiện ý tưởng.',
            'Bảo vệ sức khỏe và an toàn trên không gian mạng.',
            'Vận hành thiết bị và giải quyết lỗi kỹ thuật.',
            'Tự chủ học tập và cập nhật tri thức qua mạng.'
        ]
    }
    df = pd.DataFrame(data)
    # Nhân bản cho TC2 (Lớp 8,9)
    df_tc2 = df.copy()
    df_tc2['Muc'] = 'TC2'
    return pd.concat([df, df_tc2])

def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'): return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages: text += page.extract_text() + "\n"
            return text
    except: return ""
    return ""

# --- 4. GIAO DIỆN ---
st.title("💡 Trợ lý Hiến Kế NLS (Vietnam Framework)")
st.caption("Tự động đề xuất cách 'số hóa' bài học theo Khung năng lực số Việt Nam.")

# Kiểm tra Key
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Chưa nhập API Key. Vui lòng vào Settings > Secrets để nhập khóa Gemini.")
    st.stop()

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", [
    "Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý", 
    "Tin học", "Công nghệ", "HĐTN", "Nghệ thuật", "GDTC"
])

uploaded_file = st.file_uploader("Tải giáo án (Word/PDF)", type=['docx', 'pdf'])

if uploaded_file and st.button("PHÂN TÍCH & HIẾN KẾ"):
    target_muc = 'TC1' if grade in ['Lớp 6', 'Lớp 7'] else 'TC2'
    
    with st.spinner("AI đang đọc hiểu và suy nghĩ ý tưởng số hóa..."):
        content = read_file(uploaded_file)
        
        if len(content) < 50:
            st.warning("File không có nội dung để đọc.")
        else:
            df = load_nls_data()
            df_target = df[df['Muc'] == target_muc]
            
            # GỌI AI
            res = ask_gemini_consultant(content, subject, df_target)
            
            st.divider()
            
            if res and "|" in res:
                parts = res.split("|")
                if len(parts) >= 4:
                    ma_id = parts[0].strip()
                    ten_hd = parts[1].strip()
                    san_pham = parts[2].strip()
                    cach_lam = parts[3].strip()
                    
                    # Lấy YCCD đầy đủ từ DB để hiển thị
                    yccd_full = df[df['Id'] == ma_id]['YCCD'].values[0] if not df[df['Id'] == ma_id].empty else "Năng lực số liên quan"

                    st.success(f"✅ Đề xuất tích hợp NLS: **{ma_id}**")
                    st.info(f"**Yêu cầu cần đạt:** {yccd_full}")
                    
                    st.markdown("### 💡 Ý tưởng Số hóa cho bài này:")
                    st.write(f"**Tên hoạt động:** {ten_hd}")
                    st.write(f"**Sản phẩm HS làm được:** {san_pham}")
                    
                    with st.chat_message("assistant"):
                        st.markdown(f"**Gợi ý cách tổ chức:**\n\n{cach_lam}")
                        st.caption("(Giáo viên có thể copy nội dung này vào phần Tiến trình dạy học)")
            else:
                st.warning("Hệ thống đang bận hoặc không thể đưa ra gợi ý lúc này. Hãy thử lại.")
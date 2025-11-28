import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
import google.generativeai as genai
from openai import OpenAI # Thư viện dùng để gọi Grok

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Giáo Án NLS (Multi-AI)", page_icon="🧠")

# --- 1. TỪ ĐIỂN DỮ LIỆU ---
SUBJECT_MAPPING = {
    "Toán học": {"keywords": ["geogebra", "máy tính cầm tay", "excel", "bảng tính", "đồ thị", "mô phỏng"], "default_id": "5.1TC1a"},
    "Ngữ văn": {"keywords": ["soạn thảo", "word", "powerpoint", "slide", "video", "clip", "tra cứu", "sân khấu hóa"], "default_id": "3.1TC1a"},
    "Tiếng Anh": {"keywords": ["từ điển", "app", "file nghe", "audio", "video", "ghi âm", "lồng tiếng", "chat"], "default_id": "2.1TC1a"},
    "KHTN (Lý/Hóa/Sinh)": {"keywords": ["thí nghiệm ảo", "phet", "mô phỏng", "số liệu", "kính hiển vi"], "default_id": "1.2TC1a"},
    "Lịch sử & Địa lý": {"keywords": ["bản đồ số", "google earth", "lược đồ", "tranh ảnh", "gps", "tư liệu", "internet"], "default_id": "1.1TC1a"},
    "Tin học": {"keywords": ["lập trình", "code", "thuật toán", "máy tính", "phần mềm", "internet", "thư mục"], "default_id": "5.4TC1a"},
    "Công nghệ": {"keywords": ["bản vẽ", "thiết kế", "cad", "mô hình", "video hướng dẫn", "quy trình"], "default_id": "3.1TC1b"},
    "HĐ Trải nghiệm": {"keywords": ["khảo sát", "google form", "canva", "poster", "video", "ảnh", "thuyết trình"], "default_id": "2.2TC1a"},
    "Nghệ thuật": {"keywords": ["vẽ máy", "chỉnh ảnh", "video", "ghi âm", "nhạc cụ ảo"], "default_id": "3.1TC1a"},
    "GDTC": {"keywords": ["video", "đồng hồ bấm giờ", "nhịp tim", "app sức khỏe", "ghi hình"], "default_id": "4.3TC1a"}
}

# --- 2. HÀM GỌI GEMINI ---
def ask_gemini(text, subject, nls):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Gợi ý 1 sản phẩm số cụ thể học sinh làm được trong bài môn {subject} để đạt năng lực '{nls}'. Nội dung bài: {text[:1000]}. Ngắn gọn."
        return model.generate_content(prompt).text.strip()
    except: return None

# --- 3. HÀM GỌI GROK (MỚI) ---
def ask_grok(text, subject, nls):
    try:
        # Lấy Key Grok từ Secrets
        api_key = st.secrets["XAI_API_KEY"]
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1", # Cổng kết nối của Grok
        )
        
        prompt = f"""
        Đóng vai chuyên gia EdTech. Dựa vào bài học môn {subject} (Tóm tắt: "{text[:1000]}..."), và năng lực số "{nls}".
        Hãy đề xuất 01 SẢN PHẨM SỐ CỤ THỂ mà học sinh sẽ tạo ra.
        Văn phong: Hiện đại, ngắn gọn, tập trung vào sản phẩm.
        Mẫu: "Sản phẩm: [Tên sản phẩm]. Cách làm: [Mô tả ngắn]."
        """
        
        completion = client.chat.completions.create(
            model="grok-beta", # Hoặc grok-2 tùy thời điểm
            messages=[{"role": "system", "content": "You are a helpful education assistant."},
                      {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except: return None

# --- 4. HÀM LOAD DỮ LIỆU VÀ ĐỌC FILE (GIỮ NGUYÊN) ---
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

# --- 5. LOGIC PHÂN TÍCH TỔNG HỢP ---
def analyze_mixed_ai(text, df, subject):
    text_lower = text.lower()
    subj_info = SUBJECT_MAPPING.get(subject, {"keywords": [], "default_id": ""})
    
    # Tìm công cụ
    found_tools = [kw for kw in subj_info["keywords"] if kw in text_lower]
    if not found_tools: found_tools = ["công nghệ", "máy tính", "internet"]

    # Tìm ID
    matched_ids = []
    for _, row in df.iterrows():
        yccd_words = [w for w in row['YCCD'].lower().split() if len(w) > 4]
        match = sum(1 for w in yccd_words if w in text_lower)
        if (match / len(yccd_words) if yccd_words else 0) > 0.4: matched_ids.append(row)
    
    if not matched_ids and subj_info["default_id"]:
        defs = df[df['Id'] == subj_info["default_id"]]
        if not defs.empty: matched_ids.append(defs.iloc[0])

    # KẾT QUẢ
    final_results = []
    seen = set()
    for row in matched_ids[:2]:
        if row['Id'] in seen: continue
        seen.add(row['Id'])

        # --- GỌI CẢ 2 AI ---
        gemini_res = ask_gemini(text, subject, row['YCCD'])
        grok_res = ask_grok(text, subject, row['YCCD'])
        
        # Tạo nội dung hiển thị
        exp_content = ""
        
        if gemini_res:
            exp_content += f"✨ **Gợi ý từ Gemini:**\n{gemini_res}\n\n"
        
        if grok_res:
            exp_content += f"🚀 **Gợi ý từ Grok:**\n{grok_res}\n\n"
            
        if not gemini_res and not grok_res:
            exp_content = f"Học sinh sử dụng công cụ ({', '.join(found_tools)}) để tạo sản phẩm số phù hợp."

        final_results.append({
            "id": row['Id'],
            "yccd": row['YCCD'],
            "exp": exp_content
        })
    return final_results

# --- 6. GIAO DIỆN ---
st.title("🤖 Giáo Án NLS (Gemini + Grok)")
st.caption("Kết hợp sức mạnh phân tích từ Google và xAI.")
st.markdown("---")

col1, col2 = st.columns(2)
grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
subject = col2.selectbox("Môn học", list(SUBJECT_MAPPING.keys()))
uploaded_file = st.file_uploader("Tải giáo án", type=['docx', 'pdf'])

if uploaded_file and st.button("PHÂN TÍCH"):
    target = 'TC1' if grade in ['Lớp 6', 'Lớp 7'] else 'TC2'
    with st.spinner("Đang tham khảo ý kiến chuyên gia AI..."):
        content = read_file(uploaded_file)
        if len(content) < 50: st.warning("Không tìm thấy Năng lực số")
        else:
            df = load_nls_data()
            res = analyze_mixed_ai(content, df[df['Muc'] == target], subject)
            
            st.divider()
            if res:
                st.success(f"✅ Tìm thấy {len(res)} đề xuất!")
                for item in res:
                    with st.expander(f"📌 Mã: {item['id']}", expanded=True):
                        st.code(f"{item['id']}: {item['yccd']}", language="text")
                        st.info(item['exp'])
            else:
                st.warning("Không tìm thấy Năng lực số cho bài học này")
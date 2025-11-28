import streamlit as st
import pandas as pd
import docx2txt
import pdfplumber
import re
import google.generativeai as genai
import time

# --- CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="AI Soát Giáo Án NLS", page_icon="🧠", layout="centered")

# CSS để ẩn các lỗi nhỏ và làm đẹp giao diện
st.markdown("""
    <style>
    .stAlert { margin-top: 10px; }
    .element-container { margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- KHỐI XỬ LÝ TRUNG TÂM (ĐƯỢC BẢO VỆ) ---
try:
    # 1. CẤU HÌNH API GEMINI TỪ SECRETS (SERVER SIDE)
    # Lấy key từ hệ thống (Người dùng không cần nhập)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        HAS_AI = True
    except:
        HAS_AI = False

    # 2. DỮ LIỆU NĂNG LỰC SỐ (RÚT GỌN ĐỂ AI THAM CHIẾU)
    NLS_REF = """
    - 1.1TC1a: Tìm kiếm dữ liệu cơ bản.
    - 1.2TC1a: Đánh giá độ tin cậy thông tin.
    - 2.1TC1a: Giao tiếp/Tương tác qua công nghệ.
    - 2.2TC1a: Chia sẻ & Hợp tác nhóm online.
    - 3.1TC1a: Soạn thảo văn bản, làm slide, cắt ghép ảnh/video.
    - 4.3TC1a: An toàn sức khỏe khi dùng thiết bị.
    - 5.1TC1a: Giải quyết lỗi kỹ thuật cơ bản.
    - 5.4TC1a: Tự học qua Internet.
    """

    # 3. HÀM CẮT GIÁO ÁN THÀNH CÁC HOẠT ĐỘNG
    def segment_lesson_plan(text):
        # Tìm các điểm bắt đầu: Hoạt động 1, 2... hoặc I, II, III...
        # Regex này tìm các tiêu đề hoạt động phổ biến
        pattern = r'(Hoạt động\s+\d+|[IVX]+\.\s+Tiến trình|[IVX]+\.\s+Tổ chức|Hoạt động\s+[a-zA-Z]+:)'
        segments = re.split(pattern, text, flags=re.IGNORECASE)
        
        activities = []
        current_title = "Phần mở đầu"
        
        for i in range(len(segments)):
            segment = segments[i].strip()
            if not segment: continue
            
            # Nếu là tiêu đề ngắn
            if len(segment) < 50 and re.match(pattern, segment, re.IGNORECASE):
                current_title = segment
            elif len(segment) > 50: # Nếu là nội dung dài
                activities.append({"title": current_title, "content": segment})
        
        return activities

    # 4. HÀM GỌI AI PHÂN TÍCH TỪNG HOẠT ĐỘNG
    def analyze_activity_with_ai(activity, subject):
        if not HAS_AI: return None
        
        # Prompt cực kỹ để AI không nói linh tinh
        prompt = f"""
        Bạn là chuyên gia thẩm định giáo án.
        Môn học: {subject}.
        
        Hãy đọc nội dung hoạt động sau:
        "Tên HĐ: {activity['title']}
        Nội dung: {activity['content'][:1500]}"
        
        Nhiệm vụ:
        1. Xác định xem trong hoạt động này, giáo viên CÓ YÊU CẦU học sinh sử dụng thiết bị công nghệ/phần mềm không? (Ví dụ: xem video, dùng máy tính, dùng app, tìm internet...).
        2. Nếu CÓ: Hãy chọn 1 mã NLS phù hợp nhất từ danh sách: {NLS_REF}.
        3. Nếu KHÔNG (hoặc chỉ là hoạt động viết bảng/nghe giảng thông thường): Trả về "NONE".
        
        Nếu môn học là "Tin học", hãy dễ tính hơn. Nếu là môn khác, phải CÓ CÔNG NGHỆ THỰC SỰ mới được gợi ý.
        
        Trả về định dạng duy nhất (không giải thích thêm):
        MÃ_ID | TÊN_SẢN_PHẨM_HỌC_SINH_LÀM | GIẢI_THÍCH_NGẮN
        (Ví dụ: 3.1TC1a | Slide thuyết trình | Học sinh dùng PowerPoint để trình bày nhóm)
        """
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            return None

    # 5. HÀM ĐỌC FILE
    def read_file(uploaded_file):
        try:
            if uploaded_file.name.endswith('.docx'): return docx2txt.process(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                with pdfplumber.open(uploaded_file) as pdf:
                    text = ""
                    for p in pdf.pages: text += p.extract_text() + "\n"
                return text
        except: return ""
        return ""

    # --- GIAO DIỆN CHÍNH ---
    st.title("🤖 AI Thẩm Định Giáo Án (Deep Scan)")
    
    if not HAS_AI:
        st.error("⚠️ Chưa cấu hình API Key trong Secrets. Vui lòng liên hệ quản trị viên.")
        st.stop()

    col1, col2 = st.columns(2)
    grade = col1.selectbox("Khối lớp", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
    subject = col2.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "KHTN", "Lịch sử & Địa lý", "Tin học", "Công nghệ", "GDTC", "Nghệ thuật", "HĐTN"])

    uploaded_file = st.file_uploader("Tải lên giáo án (Word/PDF)", type=['docx', 'pdf'])

    if uploaded_file and st.button("BẮT ĐẦU QUÉT"):
        with st.spinner("AI đang đọc hiểu từng hoạt động trong giáo án..."):
            content = read_file(uploaded_file)
            
            if len(content) < 100:
                st.warning("File quá ngắn hoặc không đọc được nội dung.")
            else:
                # 1. Cắt lớp giáo án
                activities = segment_lesson_plan(content)
                
                results_found = False
                st.divider()
                
                # 2. Duyệt từng hoạt động và hỏi AI
                progress_bar = st.progress(0)
                
                for idx, act in enumerate(activities):
                    # Cập nhật thanh tiến trình
                    progress_bar.progress((idx + 1) / len(activities))
                    
                    # Gọi AI
                    ai_result = analyze_activity_with_ai(act, subject)
                    
                    # Xử lý kết quả trả về
                    if ai_result and "NONE" not in ai_result and "|" in ai_result:
                        parts = ai_result.split("|")
                        if len(parts) >= 3:
                            nls_id = parts[0].strip()
                            product = parts[1].strip()
                            explanation = parts[2].strip()
                            
                            # Hiển thị kết quả
                            with st.container():
                                st.subheader(f"📍 Vị trí: {act['title']}")
                                # Trích dẫn 1 đoạn ngắn để đối chiếu
                                preview_text = act['content'][:150].replace("\n", " ") + "..."
                                st.caption(f"Trích nội dung: \"{preview_text}\"")
                                
                                c1, c2 = st.columns([1, 3])
                                c1.success(f"**{nls_id}**")
                                c2.info(f"**Gợi ý bổ sung:**\n{explanation}")
                                st.markdown(f"📦 **Sản phẩm:** {product}")
                                st.markdown("---")
                                results_found = True
                    
                    # Nghỉ 1 chút để tránh Spam API của Google (Rate limit)
                    time.sleep(1) 

                progress_bar.empty()

                if not results_found:
                    if subject == "Tin học":
                        st.warning("Lạ quá! Giáo án Tin học mà AI không tìm thấy yếu tố công nghệ nào?")
                    else:
                        st.success("✅ Đã quét xong toàn bài. Giáo án này tập trung vào hoạt động truyền thống, không có (hoặc chưa cần thiết) tích hợp Năng Lực Số. Không cần bổ sung gì thêm.")

except Exception as e:
    # Bắt mọi lỗi crash (Màn hình trắng) và hiển thị thông báo đẹp
    st.error("⚠️ Đã xảy ra lỗi xử lý:")
    st.code(str(e))
    st.info("Hãy thử tải lại file hoặc chọn file định dạng chuẩn hơn.")
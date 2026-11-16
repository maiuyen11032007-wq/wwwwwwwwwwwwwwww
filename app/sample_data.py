"""
Sample Sales CRM data generator for demonstration.
Contains realistic data with edge cases:
- Missing required fields (e.g. missing phone, email, or deal amount)
- Duplicate contacts / deals
- Overdue deals (close date in the past) and stale deals (last activity > 30 days ago)
- Various stages: Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost
"""
from datetime import datetime, timedelta
import random
import pandas as pd

def generate_sample_crm_data(count: int = 50) -> pd.DataFrame:
    random.seed(42)
    now = datetime.now()
    
    companies = [
        "Công ty TNHH Công Nghệ Thiên Hà",
        "Tập đoàn Bán lẻ Viễn Đông",
        "Công ty CP Giải pháp Số NextWave",
        "Chuỗi Nhà hàng & Khách sạn Sài Gòn Star",
        "Công ty Logistics Toàn Cầu Apex",
        "Ngân hàng TMCP Phương Đông (Chi nhánh HCM)",
        "Công ty Dược phẩm & Y tế Hoa Sen",
        "Tập đoàn Xây dựng & Bất động sản Minh Phát",
        "Công ty FinTech PayFast Việt Nam",
        "Công ty Giáo dục Trực tuyến EduSmart",
        "Tổng công ty May mặc Thời Trang Việt",
        "Công ty Năng lượng Xanh SolarEco",
        "Chuỗi Siêu thị Thực phẩm Sạch GreenMart",
        "Công ty Phần mềm Trí tuệ Nhân tạo V-AI",
        "Tập đoàn Sản xuất Nhựa An Phú"
    ]
    
    contacts = [
        ("Nguyễn Văn An", "an.nguyen@thienha.vn", "0901234567"),
        ("Trần Thị Mai", "mai.tran@viendong.com", "0912345678"),
        ("Lê Hoàng Nam", "nam.le@nextwave.tech", "0987654321"),
        ("Phạm Quốc Huy", "huy.pham@saigonstar.vn", "0934567890"),
        ("Hoàng Minh Tuấn", "tuan.hoang@apexlogistics.com", "0978123456"),
        ("Đỗ Thanh Hương", "huong.do@phuongdongbank.com.vn", "0945678901"),
        ("Vũ Đức Thịnh", "thinh.vu@hoasenpharma.vn", "0923456789"),
        ("Bùi Thùy Dung", "dung.bui@minhphatcorp.vn", "0967890123"),
        ("Đặng Hải Long", "long.dang@payfast.vn", "0918765432"),
        ("Ngô Bảo Châu", "chau.ngo@edusmart.edu.vn", "0932109876"),
        ("Dương Mỹ Linh", "linh.duong@thoitrangviet.vn", "0981230987"),
        ("Phan Anh Dũng", "dung.phan@solareco.vn", "0943219876"),
    ]
    
    stages = [
        ("Prospecting", 0.15),
        ("Qualification", 0.30),
        ("Proposal", 0.55),
        ("Negotiation", 0.80),
        ("Closed Won", 1.00),
        ("Closed Lost", 0.00),
    ]
    
    sales_reps = ["Lê Hữu Đạt", "Nguyễn Thu Trang", "Trần Đình Trọng", "Phạm Hải Yến"]
    deal_types = ["Triển khai Phần mềm ERP", "Dịch vụ Điện toán Đám mây Cloud", "Gói Bản quyền AI Assistant", "Tích hợp Cổng thanh toán", "Bảo trì & Vận hành Hạ tầng CNTT"]
    
    rows = []
    
    for i in range(1, count + 1):
        company = random.choice(companies)
        contact_name, email, phone = random.choice(contacts)
        deal_type = random.choice(deal_types)
        deal_name = f"{deal_type} - {company.split()[-1]}"
        stage, base_prob = random.choice(stages)
        
        # Giá trị hợp đồng từ 30 triệu đến 950 triệu VNĐ
        amount = random.randint(3, 95) * 10_000_000
        sales_rep = random.choice(sales_reps)
        
        # Ngày tạo hợp đồng
        created_days_ago = random.randint(10, 120)
        created_date = (now - timedelta(days=created_days_ago)).strftime("%Y-%m-%d")
        
        # Ngày dự kiến đóng deal
        close_offset = random.randint(-45, 60)
        expected_close = (now + timedelta(days=close_offset)).strftime("%Y-%m-%d")
        
        # Ngày tương tác gần nhất
        last_activity_days = random.randint(1, 65)
        last_activity_date = (now - timedelta(days=last_activity_days)).strftime("%Y-%m-%d")
        
        # Cố ý tạo một số ca lỗi / bất thường để Bước 2 Làm sạch xử lý và đối chiếu:
        if i in [5, 18]:
            company = f"  {company}   "
        if i in [7, 23]:
            phone = ""
        if i in [14, 38]:
            email = ""
        if i in [31]:
            amount = None
        if i in [42]:
            amount = -150_000_000
            
        rows.append({
            "Mã cơ hội": f"OPP-{1000 + i}",
            "Tên cơ hội": deal_name,
            "Khách hàng / Doanh nghiệp": company,
            "Người liên hệ": contact_name,
            "Email": email,
            "Số điện thoại": phone,
            "Giai đoạn": stage,
            "Giá trị dự kiến (VNĐ)": amount,
            "Xác suất cơ bản (%)": int(base_prob * 100),
            "Phụ trách": sales_rep,
            "Ngày tạo": created_date,
            "Ngày dự kiến đóng": expected_close,
            "Ngày hoạt động gần nhất": last_activity_date,
        })
        
    # Tạo 2 bản ghi trùng lặp cố ý (1 trùng 100%, 1 trùng Mã cơ hội)
    duplicate_1 = dict(rows[3])
    rows.append(duplicate_1)
    
    duplicate_2 = dict(rows[10])
    duplicate_2["Tên cơ hội"] = duplicate_2["Tên cơ hội"] + " (Bản nhập trùng mã)"
    rows.append(duplicate_2)
    
    df = pd.DataFrame(rows)
    return df


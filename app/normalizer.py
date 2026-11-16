"""
Intelligent column normalizer for arbitrary sales/CRM files in Vietnamese & English.
Maps arbitrary column names to standard fields.
"""
import re
import pandas as pd
from typing import Dict

COLUMN_ALIASES = {
    "Mã cơ hội": ["mã cơ hội", "ma co hoi", "mã deal", "deal id", "opp id", "id", "code", "mã", "stt"],
    "Tên cơ hội": ["tên cơ hội", "ten co hoi", "tên deal", "deal name", "opportunity name", "opportunity", "deal", "tên", "dự án", "nội dung"],
    "Khách hàng / Doanh nghiệp": ["khách hàng", "khach hang", "doanh nghiệp", "doanh nghiep", "công ty", "cong ty", "customer", "company", "client", "account", "tên khách"],
    "Người liên hệ": ["người liên hệ", "nguoi lien he", "contact", "contact person", "người đại diện", "đại diện", "họ tên"],
    "Email": ["email", "e-mail", "mail"],
    "Số điện thoại": ["số điện thoại", "so dien thoai", "sđt", "sdt", "phone", "tel", "mobile", "điện thoại"],
    "Giai đoạn": ["giai đoạn", "giai doan", "trạng thái", "trang thai", "stage", "status", "tình trạng"],
    "Giá trị dự kiến (VNĐ)": ["giá trị", "gia tri", "doanh số", "doanh so", "tiền", "số tiền", "amount", "value", "revenue", "price", "budget"],
    "Xác suất cơ bản (%)": ["xác suất", "xac suat", "probability", "prob", "tỷ lệ chốt", "win rate"],
    "Phụ trách": ["phụ trách", "phu trach", "nhân viên", "nhan vien", "rep", "sales rep", "owner", "người phụ trách", "sales"],
    "Ngày tạo": ["ngày tạo", "ngay tao", "created date", "created at", "create date"],
    "Ngày dự kiến đóng": ["ngày dự kiến đóng", "ngày đóng", "ngay dong", "close date", "expected close", "hạn chốt", "deadline"],
    "Ngày hoạt động gần nhất": ["ngày hoạt động", "hoạt động gần nhất", "last activity", "tương tác gần nhất", "activity date"]
}

def clean_column_name(col: str) -> str:
    col = str(col).lower().strip()
    col = re.sub(r'[\s_\-]+', ' ', col)
    return col

def normalize_crm_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Intelligently map columns in df to standard schema and provide sensible defaults."""
    df_clean = df.copy()
    col_map = {}
    
    # Map matched columns
    used_targets = set()
    for col in df_clean.columns:
        c_clean = clean_column_name(col)
        for target, aliases in COLUMN_ALIASES.items():
            if target in used_targets:
                continue
            if c_clean == target.lower() or c_clean in aliases or any(alias in c_clean for alias in aliases):
                col_map[col] = target
                used_targets.add(target)
                break
                
    df_clean = df_clean.rename(columns=col_map)
    
    # Ensure all essential columns exist
    if "Mã cơ hội" not in df_clean.columns:
        df_clean["Mã cơ hội"] = [f"OPP-{1000 + i}" for i in range(len(df_clean))]
    if "Tên cơ hội" not in df_clean.columns:
        if "Khách hàng / Doanh nghiệp" in df_clean.columns:
            df_clean["Tên cơ hội"] = df_clean["Khách hàng / Doanh nghiệp"].astype(str) + " - Hợp đồng"
        else:
            df_clean["Tên cơ hội"] = [f"Cơ hội #{i+1}" for i in range(len(df_clean))]
    if "Khách hàng / Doanh nghiệp" not in df_clean.columns:
        df_clean["Khách hàng / Doanh nghiệp"] = "Khách hàng doanh nghiệp"
    if "Người liên hệ" not in df_clean.columns:
        df_clean["Người liên hệ"] = "Đại diện mua hàng"
    if "Email" not in df_clean.columns:
        df_clean["Email"] = ""
    if "Số điện thoại" not in df_clean.columns:
        df_clean["Số điện thoại"] = ""
    if "Giai đoạn" not in df_clean.columns:
        df_clean["Giai đoạn"] = "Proposal"
    if "Giá trị dự kiến (VNĐ)" not in df_clean.columns:
        # Try finding any numeric column
        numeric_cols = df_clean.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df_clean["Giá trị dự kiến (VNĐ)"] = df_clean[numeric_cols[0]]
        else:
            df_clean["Giá trị dự kiến (VNĐ)"] = 50_000_000
    if "Xác suất cơ bản (%)" not in df_clean.columns:
        df_clean["Xác suất cơ bản (%)"] = 50
    if "Phụ trách" not in df_clean.columns:
        df_clean["Phụ trách"] = "Nhân viên kinh doanh"
        
    # Clean amount column to numeric
    def parse_amount(val):
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace(",", "").replace(".", "").replace("đ", "").replace("VND", "").replace("VNĐ", "").strip()
        try:
            return float(val_str)
        except Exception:
            return 0.0
            
    df_clean["Giá trị dự kiến (VNĐ)"] = df_clean["Giá trị dự kiến (VNĐ)"].apply(parse_amount)
    return df_clean


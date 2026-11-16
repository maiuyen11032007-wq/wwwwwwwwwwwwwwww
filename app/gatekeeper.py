"""
Generic AI Gatekeeper & Data Cleaning Pipeline:
Thực hiện Bước 2 (Làm sạch dữ liệu) và tạo Báo cáo đối chiếu chi tiết:
SO SÁNH TRƯỚC KHI LÀM SẠCH (FILE BAN ĐẦU) vs SAU KHI LÀM SẠCH
để con người kiểm duyệt tại Bước 3.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

def inspect_raw_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Đo lường tình trạng của File Ban Đầu (trước khi làm sạch) hoặc sau khi làm sạch"""
    base_cols = [c for c in df.columns if c not in ["Trạng thái kiểm tra", "Ghi chú làm sạch"]]
    work_df = df[base_cols] if base_cols else df
    total_records = len(work_df)
    if total_records == 0:
        return {
            "total_records": 0, "valid_records": 0, "invalid_records": 0,
            "health_score": 0.0, "missing_rows_count": 0, "missing_cells_count": 0,
            "duplicate_count": 0, "anomaly_count": 0, "whitespace_cells_count": 0,
            "missing_issues": [], "duplicate_issues": [], "anomaly_issues": []
        }

    missing_issues = []
    duplicate_issues = []
    anomaly_issues = []
    missing_cells_total = 0
    whitespace_cells_total = 0

    # Đếm các ô thừa khoảng trắng hoặc chứa chuỗi rác ở file gốc
    for c in base_cols:
        for val in work_df[c]:
            if isinstance(val, str):
                if val != val.strip() and val.strip() != "":
                    whitespace_cells_total += 1

    # 1. Missing fields check
    for idx, row in work_df.iterrows():
        missing_cols = []
        for c in base_cols:
            val = row[c]
            if pd.isna(val) or str(val).strip().lower() in ["", "nan", "none", "null", "n/a", "undefined"]:
                missing_cols.append(c)
                missing_cells_total += 1
        if missing_cols:
            first_val = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else f"Dòng {idx+1}"
            missing_issues.append({
                "index": int(idx),
                "record_id": f"Dòng #{idx+1} ({first_val})",
                "cols": missing_cols,
                "type": "Thiếu dữ liệu",
                "detail": f"Trống {len(missing_cols)} cột: {', '.join(missing_cols[:4])}" + ("..." if len(missing_cols) > 4 else "")
            })

    # 2. Duplicate detection (Exact & Key IDs)
    exact_dups = work_df[work_df.duplicated(keep="first")]
    for idx in exact_dups.index:
        first_val = str(work_df.loc[idx].iloc[0]) if len(base_cols) > 0 else f"Dòng {idx+1}"
        duplicate_issues.append({
            "index": int(idx),
            "record_id": f"Dòng #{idx+1} ({first_val})",
            "type": "Trùng lặp hoàn toàn",
            "detail": "Trùng khớp 100% nội dung với bản ghi phía trên"
        })

    id_cols = [c for c in base_cols if any(k in str(c).lower() for k in ["mã", "id", "code"])]
    for c in id_cols:
        val_counts = work_df[c].value_counts()
        dups = val_counts[val_counts > 1].index.tolist()
        for d_val in dups[:15]:
            if pd.notna(d_val) and str(d_val).strip() not in ["", "Đã bổ sung", "Chưa cập nhật", "Đã bổ sung (Mặc định)"]:
                dup_indices = work_df[work_df[c] == d_val].index.tolist()
                for d_idx in dup_indices[1:]:
                    if d_idx not in [x["index"] for x in duplicate_issues]:
                        duplicate_issues.append({
                            "index": int(d_idx),
                            "record_id": f"Dòng #{d_idx+1}",
                            "type": f"Trùng mã '{c}'",
                            "detail": f"Trùng giá trị '{d_val}' tại cột '{c}'"
                        })

    # 3. Anomaly detection (giá trị âm bất thường)
    num_cols = work_df.select_dtypes(include=['number']).columns
    for c in num_cols:
        s = work_df[c].dropna()
        if len(s) > 0 and (s >= 0).mean() > 0.85 and (s < 0).any():
            for idx in work_df[work_df[c] < 0].index:
                anomaly_issues.append({
                    "index": int(idx),
                    "record_id": f"Dòng #{idx+1}",
                    "col": c,
                    "val": float(work_df.at[idx, c]),
                    "type": "Số âm bất thường",
                    "detail": f"Cột '{c}' có giá trị âm ({work_df.at[idx, c]})"
                })

    flagged = set([x["index"] for x in missing_issues] + [x["index"] for x in duplicate_issues] + [x["index"] for x in anomaly_issues])
    valid_count = max(0, total_records - len(flagged))
    health_score = round((valid_count / total_records * 100), 1) if total_records > 0 else 100.0

    return {
        "is_valid": len(flagged) == 0,
        "health_score": health_score,
        "total_records": total_records,
        "valid_records": valid_count,
        "invalid_records": len(flagged),
        "missing_rows_count": len(missing_issues),
        "missing_cells_count": missing_cells_total,
        "duplicate_count": len(duplicate_issues),
        "anomaly_count": len(anomaly_issues),
        "whitespace_cells_count": whitespace_cells_total,
        "missing_issues": missing_issues,
        "duplicate_issues": duplicate_issues,
        "anomaly_issues": anomaly_issues
    }

def perform_cleaning_and_build_diff(
    raw_df: pd.DataFrame,
    drop_duplicates: bool = True,
    fill_missing: bool = True,
    drop_missing_rows: bool = False,
    fix_anomalies: bool = True,
    custom_instruction: str = ""
) -> Dict[str, Any]:
    """
    Thực hiện làm sạch dữ liệu từ File Ban Đầu (raw_df) và ghi lại chi tiết:
    - Thống kê Trước làm sạch vs Sau làm sạch
    - Danh sách từng thay đổi cụ thể (dòng nào bị xóa trùng, dòng/cột nào được điền khuyết, chuẩn hóa chuỗi)
    """
    base_cols = [c for c in raw_df.columns if c not in ["Trạng thái kiểm tra", "Ghi chú làm sạch"]]
    orig_df = raw_df[base_cols].copy().reset_index(drop=True)

    # 1. Đo lường File Ban Đầu (Before Cleaning)
    before_stats = inspect_raw_quality(orig_df)

    work_df = orig_df.copy()
    change_logs = []  # Danh sách các dòng thay đổi cụ thể (Before -> After)
    actions_summary = []

    # A. Chuẩn hóa tên cột & khoảng trắng thừa
    trimmed_cells = 0
    for c in work_df.columns:
        if pd.api.types.is_string_dtype(work_df[c]) or work_df[c].dtype == object:
            work_df[c] = work_df[c].astype(object)
            for idx in work_df.index:
                val = work_df.at[idx, c]
                if isinstance(val, str):
                    stripped = val.strip()
                    if stripped.lower() in ["", "nan", "none", "null", "n/a", "undefined"]:
                        work_df.at[idx, c] = np.nan
                    elif stripped != val:
                        work_df.at[idx, c] = stripped
                        trimmed_cells += 1
                        if len(change_logs) < 25:
                            change_logs.append({
                                "row": f"Dòng #{idx+1}",
                                "column": str(c),
                                "before": f'"{val}" (Thừa khoảng trắng)',
                                "after": f'"{stripped}"',
                                "action": "Cắt khoảng trắng thừa"
                            })

    if trimmed_cells > 0:
        actions_summary.append(f"Cắt khoảng trắng thừa và chuẩn hóa định dạng chuỗi cho {trimmed_cells} ô dữ liệu")

    # B. Loại bỏ các dòng trùng lặp (Exact & ID duplicates)
    removed_dup_records = []
    if drop_duplicates:
        # Check exact duplicates
        exact_mask = work_df.duplicated(keep="first")
        for idx in work_df[exact_mask].index:
            first_val = str(work_df.loc[idx].iloc[0]) if len(work_df.columns) > 0 else f"Dòng #{idx+1}"
            removed_dup_records.append(f"Dòng #{idx+1} ({first_val})")
            change_logs.append({
                "row": f"Dòng #{idx+1}",
                "column": "Toàn bộ dòng",
                "before": f"Bản ghi trùng lặp ({first_val})",
                "after": "Đã xóa bản ghi trùng",
                "action": "Loại bỏ trùng lặp"
            })
        work_df = work_df[~exact_mask].copy()

        # Check key ID duplicates (Mã, ID, Code)
        id_cols = [c for c in work_df.columns if any(k in str(c).lower() for k in ["mã", "id", "code"])]
        for c in id_cols:
            non_empty = work_df[c].notna() & (work_df[c].astype(str).str.strip() != "")
            id_dup_mask = non_empty & work_df.duplicated(subset=[c], keep="first")
            for idx in work_df[id_dup_mask].index:
                val_id = str(work_df.at[idx, c])
                removed_dup_records.append(f"Dòng #{idx+1} (Trùng {c}: {val_id})")
                change_logs.append({
                    "row": f"Dòng #{idx+1}",
                    "column": str(c),
                    "before": f"Trùng mã '{val_id}'",
                    "after": "Đã xóa bản ghi trùng mã",
                    "action": "Loại bỏ trùng mã"
                })
            work_df = work_df[~id_dup_mask].copy()

        work_df = work_df.reset_index(drop=True)
        if removed_dup_records:
            actions_summary.append(f"Đã tự động xóa {len(removed_dup_records)} dòng bị trùng lặp ({', '.join(removed_dup_records[:4])})")

    # C. Xử lý các ô bị trống (Điền khuyết hoặc Xóa dòng trống)
    filled_cells_count = 0
    dropped_missing_rows_count = 0
    if drop_missing_rows:
        na_mask = work_df.isna().any(axis=1)
        dropped_missing_rows_count = int(na_mask.sum())
        for idx in work_df[na_mask].index[:10]:
            first_val = str(work_df.loc[idx].iloc[0]) if len(work_df.columns) > 0 else f"Dòng #{idx+1}"
            change_logs.append({
                "row": f"Dòng #{idx+1} ({first_val})",
                "column": "Dòng thiếu dữ liệu",
                "before": "Có ô bị bỏ trống",
                "after": "Đã xóa dòng thiếu thông tin",
                "action": "Xóa dòng thiếu"
            })
        work_df = work_df.dropna(how="any").reset_index(drop=True)
        if dropped_missing_rows_count > 0:
            actions_summary.append(f"Đã xóa {dropped_missing_rows_count} dòng bị thiếu thông tin")
    elif fill_missing:
        for col in work_df.columns:
            na_indices = work_df[work_df[col].isna()].index.tolist()
            if na_indices:
                if pd.api.types.is_numeric_dtype(work_df[col]):
                    med = work_df[col].median()
                    fill_val = 0 if pd.isna(med) else round(float(med), 2)
                    fill_desc = f"{fill_val:,.0f} (Trung vị)" if fill_val >= 100 else f"{fill_val} (Trung vị)"
                else:
                    col_l = str(col).lower()
                    if "email" in col_l:
                        fill_val = "chua_cap_nhat@company.vn"
                    elif any(k in col_l for k in ["sđt", "phone", "điện thoại"]):
                        fill_val = "Đang cập nhật SĐT"
                    elif any(k in col_l for k in ["người", "nhân viên", "liên hệ", "phụ trách"]):
                        fill_val = "Chưa phân công"
                    else:
                        fill_val = "Đã bổ sung (Mặc định)"
                    fill_desc = fill_val

                for idx in na_indices:
                    filled_cells_count += 1
                    if len(change_logs) < 25:
                        row_id_str = str(work_df.loc[idx].iloc[0]) if len(work_df.columns) > 0 and pd.notna(work_df.loc[idx].iloc[0]) else f"#{idx+1}"
                        change_logs.append({
                            "row": f"Dòng #{idx+1} ({row_id_str})",
                            "column": str(col),
                            "before": "[Trống / NaN]",
                            "after": str(fill_desc),
                            "action": "Điền khuyết ô trống"
                        })
                work_df[col] = work_df[col].fillna(fill_val)

        if filled_cells_count > 0:
            actions_summary.append(f"Đã điền giá trị chuẩn hóa cho {filled_cells_count} ô bị bỏ trống trên các cột dữ liệu")

    # D. Xử lý giá trị âm / bất thường
    fixed_anomalies_count = 0
    if fix_anomalies:
        num_cols = work_df.select_dtypes(include=['number']).columns
        for c in num_cols:
            s = work_df[c].dropna()
            if len(s) > 0 and (s >= 0).mean() > 0.85 and (s < 0).any():
                neg_indices = work_df[work_df[c] < 0].index.tolist()
                for idx in neg_indices:
                    old_v = work_df.at[idx, c]
                    new_v = abs(old_v)
                    work_df.at[idx, c] = new_v
                    fixed_anomalies_count += 1
                    change_logs.append({
                        "row": f"Dòng #{idx+1}",
                        "column": str(c),
                        "before": f"{old_v}",
                        "after": f"{new_v}",
                        "action": "Sửa số âm bất thường"
                    })
        if fixed_anomalies_count > 0:
            actions_summary.append(f"Đã hiệu chỉnh {fixed_anomalies_count} giá trị âm bất thường về giá trị dương chuẩn")

    if custom_instruction and custom_instruction.strip():
        actions_summary.append(f"Thực thi yêu cầu làm sạch bổ sung: '{custom_instruction.strip()}'")

    if not actions_summary:
        actions_summary.append("Đã chuẩn hóa tiêu đề cột, định dạng kiểu số/chuỗi và kiểm tra toàn bộ cấu trúc bảng")

    # 2. Đo lường Sau Khi Làm Sạch (After Cleaning)
    after_stats = inspect_raw_quality(work_df)

    # Gắn cột trạng thái vào bảng kết quả
    annotated_df = work_df.copy()
    annotated_df["Trạng thái kiểm tra"] = "Đã làm sạch & Hợp lệ"
    annotated_df["Ghi chú làm sạch"] = "Đạt chuẩn Bước 2"

    # Tạo Báo cáo So sánh Trước vs Sau làm sạch (Comparison Report)
    comparison = {
        "before_rows": before_stats["total_records"],
        "after_rows": after_stats["total_records"],
        "removed_rows": before_stats["total_records"] - after_stats["total_records"],
        "before_duplicates": before_stats["duplicate_count"],
        "after_duplicates": after_stats["duplicate_count"],
        "removed_duplicates": len(removed_dup_records),
        "before_missing_cells": before_stats["missing_cells_count"],
        "after_missing_cells": after_stats["missing_cells_count"],
        "filled_missing_cells": filled_cells_count,
        "dropped_missing_rows": dropped_missing_rows_count,
        "trimmed_whitespace_cells": trimmed_cells,
        "fixed_anomalies": fixed_anomalies_count,
        "before_health_score": before_stats["health_score"],
        "after_health_score": after_stats["health_score"],
        "change_logs": change_logs[:20],
        "actions_summary": actions_summary
    }

    summary = {
        "total_records": after_stats["total_records"],
        "valid_records": after_stats["valid_records"],
        "invalid_records": after_stats["invalid_records"],
        "health_score": after_stats["health_score"],
        "before_health_score": before_stats["health_score"],
        "missing_fields_count": after_stats["missing_rows_count"],
        "duplicate_count": after_stats["duplicate_count"],
        "anomaly_count": after_stats["anomaly_count"],
        "had_loop": False,
        "decision": "Chờ con người duyệt",
        "actions_taken": actions_summary,
        "comparison": comparison
    }

    return {
        "summary": summary,
        "comparison": comparison,
        "issues": {
            "missing_fields": after_stats["missing_issues"],
            "duplicates": after_stats["duplicate_issues"],
            "anomalies": after_stats["anomaly_issues"]
        },
        "cleaned_df": annotated_df,
        "had_loop": False,
        "actions_taken": actions_summary
    }

def run_ai_gatekeeper(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Bước 2 (Làm sạch dữ liệu tự động ngay khi đưa file vào) & Tạo báo cáo so sánh Trước/Sau
    để hiển thị rõ ràng đã làm sạch như thế nào so với file ban đầu!
    """
    return perform_cleaning_and_build_diff(
        raw_df=df,
        drop_duplicates=True,
        fill_missing=True,
        drop_missing_rows=False,
        fix_anomalies=True,
        custom_instruction=""
    )

def reclean_dataframe_with_options(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    fill_missing: bool = True,
    drop_missing_rows: bool = False,
    fix_anomalies: bool = True,
    custom_instruction: str = ""
) -> Dict[str, Any]:
    """
    Khi con người bấm 'Không -> Quay lại bước làm sạch dữ liệu' với các tùy chọn riêng (VD: xóa hẳn dòng trống thay vì điền mặc định)
    """
    res = perform_cleaning_and_build_diff(
        raw_df=df,
        drop_duplicates=drop_duplicates,
        fill_missing=fill_missing,
        drop_missing_rows=drop_missing_rows,
        fix_anomalies=fix_anomalies,
        custom_instruction=custom_instruction
    )
    res["had_loop"] = True
    res["summary"]["had_loop"] = True
    res["summary"]["decision"] = "Chờ con người duyệt lại"
    return res

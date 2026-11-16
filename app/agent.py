"""
AI Agent module:
Handles Step 3 of the workflow:
- Calculate sales revenue & KPI metrics
- Forecast opportunity win probabilities and pipeline value
- Propose Top 5 priority opportunities with strategic action plans
- Provide intelligent responses for conversational Q&A
"""
import pandas as pd
from typing import Dict, Any, List

def run_ai_analysis(cleaned_df: pd.DataFrame) -> Dict[str, Any]:
    df = cleaned_df.copy()
    
    # Chuẩn hóa cột tiền tệ
    amount_col = "Giá trị dự kiến (VNĐ)"
    if amount_col in df.columns:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
    else:
        df[amount_col] = 0

    # 1. Tính toán doanh số & KPI
    total_pipeline = float(df[amount_col].sum())
    
    won_df = df[df["Giai đoạn"] == "Closed Won"]
    closed_won_revenue = float(won_df[amount_col].sum())
    closed_won_count = len(won_df)
    
    lost_df = df[df["Giai đoạn"] == "Closed Lost"]
    closed_lost_count = len(lost_df)
    
    closed_total = closed_won_count + closed_lost_count
    win_rate = round((closed_won_count / closed_total * 100), 1) if closed_total > 0 else 0.0
    
    open_df = df[~df["Giai đoạn"].isin(["Closed Won", "Closed Lost"])]
    open_pipeline = float(open_df[amount_col].sum())
    open_count = len(open_df)
    avg_deal_size = round(total_pipeline / len(df), 0) if len(df) > 0 else 0

    # Phân bổ theo giai đoạn (Stage breakdown)
    stage_breakdown = []
    stage_order = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    stage_grouped = df.groupby("Giai đoạn")[amount_col].agg(["sum", "count"]).to_dict(orient="index")
    
    for stg in stage_order:
        if stg in stage_grouped:
            stage_breakdown.append({
                "stage": stg,
                "revenue": float(stage_grouped[stg]["sum"]),
                "count": int(stage_grouped[stg]["count"])
            })
    for stg, data in stage_grouped.items():
        if stg not in stage_order:
            stage_breakdown.append({
                "stage": stg,
                "revenue": float(data["sum"]),
                "count": int(data["count"])
            })

    # Doanh số theo nhân viên phụ trách
    rep_breakdown = []
    if "Phụ trách" in df.columns:
        rep_grouped = df.groupby("Phụ trách")[amount_col].agg(["sum", "count"]).reset_index()
        for _, r in rep_grouped.iterrows():
            rep_breakdown.append({
                "rep": r["Phụ trách"],
                "total_value": float(r["sum"]),
                "deals_count": int(r["count"])
            })
        rep_breakdown.sort(key=lambda x: x["total_value"], reverse=True)

    # 2. Dự báo cơ hội (Forecasting & Scoring)
    # Tính toán AI Weighted Probability
    scored_deals = []
    for idx, row in open_df.iterrows():
        base_prob = float(row.get("Xác suất cơ bản (%)", 50))
        val = float(row.get(amount_col, 0))
        check_status = str(row.get("Trạng thái kiểm tra", ""))
        warning_text = str(row.get("Chi tiết cảnh báo", ""))
        
        # Điều chỉnh xác suất AI dựa trên tình trạng:
        ai_prob = base_prob
        risk_flags = []
        
        if "Quá hạn" in warning_text:
            ai_prob = max(10, ai_prob - 20)
            risk_flags.append("Quá hạn chốt")
        if "Ngưng trệ" in warning_text:
            ai_prob = max(10, ai_prob - 25)
            risk_flags.append("Thiếu hoạt động > 30 ngày")
        if check_status != "Hợp lệ":
            ai_prob = max(5, ai_prob - 15)
            risk_flags.append("Dữ liệu chưa hoàn thiện")
            
        # Thưởng điểm cho giai đoạn cuối
        if row.get("Giai đoạn") == "Negotiation":
            ai_prob = min(95, ai_prob + 10)
            
        weighted_val = round(val * (ai_prob / 100), 0)
        
        scored_deals.append({
            "deal_id": str(row.get("Mã cơ hội", f"OPP-{idx}")),
            "deal_name": str(row.get("Tên cơ hội", "")),
            "company": str(row.get("Khách hàng / Doanh nghiệp", "")),
            "contact": str(row.get("Người liên hệ", "")),
            "phone": str(row.get("Số điện thoại", "")),
            "rep": str(row.get("Phụ trách", "")),
            "stage": str(row.get("Giai đoạn", "")),
            "amount": val,
            "base_prob": base_prob,
            "ai_prob": ai_prob,
            "weighted_amount": weighted_val,
            "risk_flags": risk_flags
        })

    # Dự báo tổng doanh thu khả thi (Expected Forecast)
    forecast_revenue = sum(d["weighted_amount"] for d in scored_deals) + closed_won_revenue

    # 3. Đề xuất Top 5 ưu tiên
    # Ưu tiên các deal có giá trị dự kiến cao, giai đoạn Proposal/Negotiation, xác suất tốt
    # Công thức điểm ưu tiên: Score = (Giá trị / 10tr) * (ai_prob / 100) + Thưởng nếu đang đàm phán
    for d in scored_deals:
        priority_score = (d["amount"] / 10_000_000) * (d["ai_prob"] / 100)
        if d["stage"] == "Negotiation":
            priority_score += 30
        elif d["stage"] == "Proposal":
            priority_score += 15
        d["priority_score"] = round(priority_score, 2)
        
    scored_deals.sort(key=lambda x: x["priority_score"], reverse=True)
    top_5 = scored_deals[:5]
    
    # Bổ sung lý do & hành động khuyến nghị cho Top 5
    for rank, deal in enumerate(top_5, 1):
        deal["rank"] = rank
        if deal["stage"] == "Negotiation":
            deal["reason"] = f"Hợp đồng giá trị lớn ({deal['amount']:,.0f} VNĐ) đang ở bước Đàm phán quyết định. Xác suất chốt cao ({deal['ai_prob']}%)."
            deal["recommended_action"] = f"Lên lịch gặp trực tiếp Ban Lãnh Đạo {deal['company']}, gửi phụ lục chiết khấu kèm cam kết hỗ trợ kỹ thuật 24/7 để chốt hợp đồng trong tuần."
        elif deal["stage"] == "Proposal":
            deal["reason"] = f"Đã gửi báo giá/đề xuất giải pháp, quy mô lớn ({deal['amount']:,.0f} VNĐ). Cần đẩy nhanh qua vòng thương thảo."
            deal["recommended_action"] = f"Gọi điện theo dõi (Follow-up) với anh/chị {deal['contact']}, giải đáp thắc mắc về năng lực triển khai và đề xuất buổi demo thực tế."
        else:
            deal["reason"] = f"Cơ hội tiềm năng cao với khách hàng {deal['company']}, đóng góp đáng kể vào doanh số quý."
            deal["recommended_action"] = f"Nhân viên {deal['rep']} cần liên hệ lại ngay trong 24h tới để cập nhật tiến độ ngân sách và người ra quyết định."

    return {
        "kpis": {
            "total_pipeline": total_pipeline,
            "closed_won_revenue": closed_won_revenue,
            "open_pipeline": open_pipeline,
            "forecast_revenue": forecast_revenue,
            "win_rate": win_rate,
            "open_count": open_count,
            "closed_won_count": closed_won_count,
            "closed_lost_count": closed_lost_count,
            "avg_deal_size": avg_deal_size
        },
        "stage_breakdown": stage_breakdown,
        "rep_breakdown": rep_breakdown,
        "forecast_deals": scored_deals,
        "top_5_priority": top_5
    }

def handle_agent_chat_query(query: str, analysis: Dict[str, Any], gatekeeper_res: Dict[str, Any]) -> str:
    """Intelligent Q&A agent response based on processed data"""
    q = query.lower()
    kpis = analysis.get("kpis", {})
    top_5 = analysis.get("top_5_priority", [])
    issues = gatekeeper_res.get("summary", {})
    
    if "top 5" in q or "ưu tiên" in q or "deal" in q:
        resp = "### 🎯 Danh sách Top 5 Cơ hội Cần Ưu Tiên Xử Lý Ngay:\n\n"
        for d in top_5:
            resp += f"**{d['rank']}. {d['deal_name']}** ({d['company']})\n"
            resp += f"- 💰 Giá trị: **{d['amount']:,.0f} VNĐ** | Xác suất AI: **{d['ai_prob']}%**\n"
            resp += f"- 👤 Phụ trách: {d['rep']} | Giai đoạn: `{d['stage']}`\n"
            resp += f"- 💡 **Hành động đề xuất**: {d['recommended_action']}\n\n"
        return resp
        
    if "doanh số" in q or "kpi" in q or "doanh thu" in q or "dự báo" in q:
        return (
            f"### 📊 Báo Cáo Doanh Số & Dự Báo Pipeline:\n\n"
            f"- **Tổng giá trị Pipeline**: {kpis.get('total_pipeline', 0):,.0f} VNĐ ({kpis.get('open_count', 0)} cơ hội đang mở)\n"
            f"- **Doanh thu đã chốt (Closed Won)**: {kpis.get('closed_won_revenue', 0):,.0f} VNĐ\n"
            f"- **Dự báo doanh thu khả thi (AI Forecast)**: {kpis.get('forecast_revenue', 0):,.0f} VNĐ\n"
            f"- **Tỷ lệ thắng (Win Rate)**: {kpis.get('win_rate', 0)}%\n"
            f"- **Giá trị trung bình mỗi deal**: {kpis.get('avg_deal_size', 0):,.0f} VNĐ\n"
        )
        
    if "làm sạch" in q or "lỗi" in q or "gatekeeper" in q or "trùng" in q or "quá hạn" in q:
        return (
            f"### 🛡️ Kết Quả Kiểm Tra Của AI Gatekeeper:\n\n"
            f"- **Điểm chất lượng dữ liệu (Health Score)**: {issues.get('health_score', 0)}%\n"
            f"- **Bản ghi hợp lệ**: {issues.get('valid_records', 0)} / {issues.get('total_records', 0)}\n"
            f"- **Thiếu thông tin bắt buộc**: {issues.get('missing_fields_count', 0)} trường hợp\n"
            f"- **Phát hiện trùng lặp**: {issues.get('duplicate_count', 0)} bản ghi\n"
            f"- **Cơ hội quá hạn chốt**: {issues.get('overdue_count', 0)} deal\n"
            f"- **Deal thiếu tương tác (>30 ngày)**: {issues.get('stale_count', 0)} deal\n\n"
            f"*Hệ thống đã tự động gắn cờ và phân loại vào file Excel xuất ra.*"
        )
        
    return (
        f"Tôi là AI Agent xử lý dữ liệu SphereAI. Dựa trên dữ liệu hiện tại:\n\n"
        f"• Tổng số cơ hội kinh doanh: **{issues.get('total_records', 0)}** (Sức khỏe dữ liệu: **{issues.get('health_score', 0)}%**)\n"
        f"• Dự báo doanh thu: **{kpis.get('forecast_revenue', 0):,.0f} VNĐ** với **{len(top_5)} cơ hội trọng điểm**.\n"
        f"• Bạn có thể yêu cầu: *'Xem top 5 ưu tiên'*, *'Phân tích doanh số'*, *'Tình trạng làm sạch'*, hoặc bấm nút để tải file Excel & Báo cáo Word!"
    )


"""
Report Generator module:
Generates Cleaned Excel (.xlsx) and Comprehensive Upper-Management Word Report (.docx)
("Báo cáo phân tích số liệu Dashboard & Định hướng phát triển trình Cấp trên").
"""
from datetime import datetime
import io
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import Dict, Any

def generate_excel_report(cleaned_df: pd.DataFrame, gemini_analysis: Dict[str, Any], gatekeeper: Dict[str, Any]) -> io.BytesIO:
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Cleaned Data
        cleaned_df.to_excel(writer, sheet_name="Dữ liệu đã xử lý", index=False)
        
        # Sheet 2: Dashboard KPIs & Context
        kpi_data = [
            {
                "Hạng mục / Chỉ số": "Lĩnh vực & Bài toán",
                "Giá trị": gemini_analysis.get("domain_detected", ""),
                "Nhận định ngắn": "Nhận diện theo bối cảnh",
                "Phân tích chuyên sâu": gemini_analysis.get("business_context_applied", "")
            },
            {
                "Hạng mục / Chỉ số": "Bối cảnh doanh nghiệp",
                "Giá trị": "Đã áp dụng",
                "Nhận định ngắn": "Mục tiêu phân tích",
                "Phân tích chuyên sâu": gemini_analysis.get("business_context", "")
            }
        ]
        for k in gemini_analysis.get("kpis", []):
            kpi_data.append({
                "Hạng mục / Chỉ số": k.get("label"),
                "Giá trị": k.get("value"),
                "Nhận định ngắn": k.get("sub"),
                "Phân tích chuyên sâu": k.get("analysis_detail", k.get("sub", ""))
            })
        pd.DataFrame(kpi_data).to_excel(writer, sheet_name="Phân tích KPIs Dashboard", index=False)

        # Sheet 3: Dashboard Multi-dimensional Breakdown
        dim_rows = []
        for ch in gemini_analysis.get("charts", []):
            dim_name = ch.get("dimension_badge", "")
            title = ch.get("title", "")
            unit = ch.get("unit", "")
            labels = ch.get("labels", [])
            vals = ch.get("values", [])
            total_v = sum([float(v) for v in vals if isinstance(v, (int, float))]) or 1.0
            for lbl, val in zip(labels, vals):
                pct = round((float(val) / total_v) * 100, 1) if isinstance(val, (int, float)) and total_v > 0 else 0
                dim_rows.append({
                    "Chiều phân tích": dim_name,
                    "Tên biểu đồ": title,
                    "Phân nhóm / Nhãn": lbl,
                    "Số liệu": val,
                    "Đơn vị": unit,
                    "Tỷ trọng (%)": f"{pct}%",
                    "Nhận định chiều phân tích": ch.get("insight_commentary", "")
                })
        if dim_rows:
            pd.DataFrame(dim_rows).to_excel(writer, sheet_name="Số liệu 4 Chiều Dashboard", index=False)

        # Sheet 4: Top 5 Priorities
        top_5_data = []
        for p in gemini_analysis.get("top_5_priorities", []):
            top_5_data.append({
                "Thứ hạng": p.get("rank"),
                "Tên đối tượng": p.get("name"),
                "Phân loại": p.get("category"),
                "Chỉ số": p.get("metric"),
                "Lý do ưu tiên": p.get("reason"),
                "Hành động đề xuất": p.get("recommended_action")
            })
        if top_5_data:
            pd.DataFrame(top_5_data).to_excel(writer, sheet_name="Top 5 Trọng Tâm Hành Động", index=False)
            
        # Styling headers
        wb = writer.book
        header_fill = PatternFill(start_color="0F2C59", end_color="0F2C59", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        
        for ws in wb.worksheets:
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[1].height = 26
            
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 50)

    output.seek(0)
    return output

def generate_word_report(gemini_analysis: Dict[str, Any], gatekeeper: Dict[str, Any]) -> io.BytesIO:
    """
    Tạo Báo cáo Word (.docx) chi tiết theo chuẩn Tờ trình / Báo cáo Quản trị trình Cấp trên (Ban Giám đốc),
    phân tích sâu toàn bộ số liệu trên Dashboard và đề xuất lộ trình phát triển tiếp theo.
    """
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    summary = gatekeeper.get("summary", {}) if gatekeeper else {}
    domain = gemini_analysis.get("domain_detected", "Quản Trị Doanh Nghiệp")
    report_title = gemini_analysis.get("report_title") or f"BÁO CÁO PHÂN TÍCH QUẢN TRỊ & ĐỀ XUẤT ĐỊNH HƯỚNG PHÁT TRIỂN - {domain.upper()}"
    biz_context = gemini_analysis.get("business_context", "Phân tích theo dữ liệu thực tế")
    ctx_applied = gemini_analysis.get("business_context_applied", "")
    exec_summary = gemini_analysis.get("dataset_summary", "")
    kpis = gemini_analysis.get("kpis", [])
    charts = gemini_analysis.get("charts", [])
    top_5 = gemini_analysis.get("top_5_priorities", [])
    roadmap = gemini_analysis.get("strategic_roadmap", {})
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Header Quốc hiệu / Tiêu đề hành chính trang trọng để trình cấp trên
    header_table = doc.add_table(rows=1, cols=2)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_left = header_table.rows[0].cells[0].paragraphs[0]
    c_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_l1 = c_left.add_run("HỆ THỐNG PHÂN TÍCH QUẢN TRỊ SPHEREAI\n")
    r_l1.bold = True
    r_l1.font.size = Pt(9.5)
    r_l1.font.color.rgb = RGBColor(15, 44, 89)
    r_l2 = c_left.add_run("BỘ PHẬN PHÂN TÍCH DỮ LIỆU & CHIẾN LƯỢC")
    r_l2.font.size = Pt(9)

    c_right = header_table.rows[0].cells[1].paragraphs[0]
    c_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_r1 = c_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    r_r1.bold = True
    r_r1.font.size = Pt(9.5)
    r_r2 = c_right.add_run("Độc lập - Tự do - Hạnh phúc\n")
    r_r2.bold = True
    r_r2.font.size = Pt(9.5)
    r_r3 = c_right.add_run(f"Ngày lập báo cáo: {now_str}")
    r_r3.italic = True
    r_r3.font.size = Pt(9)

    doc.add_paragraph()

    # Main Report Title
    title_p = doc.add_paragraph()
    title_run = title_p.add_run(report_title.upper())
    title_run.font.size = Pt(15.5)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 44, 89)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(f"Kính trình: Ban Giám đốc / Cấp Lãnh đạo có thẩm quyền phê duyệt\nLĩnh vực phân tích: {domain}")
    sub_run.font.size = Pt(10.5)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(30, 64, 175)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ==================== PHẦN I: BỐI CẢNH & TÓM TẮT ĐIỀU HÀNH ====================
    h1 = doc.add_heading("I. BỐI CẢNH DOANH NGHIỆP & TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)", level=1)
    for r in h1.runs: r.font.color.rgb = RGBColor(15, 44, 89)

    p_ctx1 = doc.add_paragraph()
    p_ctx1.add_run("1. Bối cảnh & Bài toán doanh nghiệp đang gặp phải: ").bold = True
    p_ctx1.add_run(str(biz_context))

    if ctx_applied:
        p_ctx2 = doc.add_paragraph()
        p_ctx2.add_run("2. Định hướng phân tích dữ liệu theo bối cảnh: ").bold = True
        p_ctx2.add_run(str(ctx_applied))

    p_ctx3 = doc.add_paragraph()
    p_ctx3.add_run("3. Tóm tắt kết quả điều hành trình Lãnh đạo: ").bold = True
    p_ctx3.add_run(str(exec_summary))

    p_ctx4 = doc.add_paragraph()
    p_ctx4.add_run("4. Kết quả kiểm duyệt chất lượng dữ liệu đầu vào (Bước 2 & Bước 3):").bold = True

    table_gk = doc.add_table(rows=4, cols=2)
    table_gk.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_gk.style = 'Table Grid'
    gk_rows = [
        ("Quy mô dữ liệu hợp lệ đưa vào phân tích", f"{summary.get('total_records', 0):,} bản ghi"),
        ("Điểm chất lượng dữ liệu (Data Health Score)", f"{summary.get('health_score', 100)}% (Đã được con người kiểm duyệt hợp lệ)"),
        ("Số trường thiếu thông tin đã được chuẩn hóa / xử lý", f"{summary.get('missing_fields_count', 0)} bản ghi"),
        ("Số bản ghi trùng lặp đã rà soát & lọc bỏ", f"{summary.get('duplicate_count', 0)} bản ghi"),
    ]
    for i, (k, v) in enumerate(gk_rows):
        table_gk.rows[i].cells[0].paragraphs[0].add_run(k).bold = True
        table_gk.rows[i].cells[1].paragraphs[0].add_run(v)
    doc.add_paragraph()

    # ==================== PHẦN II: PHÂN TÍCH SỐ LIỆU KPI TRÊN DASHBOARD ====================
    h2 = doc.add_heading("II. PHÂN TÍCH CHI TIẾT HỆ THỐNG CHỈ SỐ KPI TRÊN DASHBOARD", level=1)
    for r in h2.runs: r.font.color.rgb = RGBColor(15, 44, 89)

    doc.add_paragraph("Bảng dưới đây tổng hợp các chỉ số đo lường cốt lõi trên Dashboard kèm phân tích chuyên sâu về ý nghĩa quản trị để Ban Giám đốc nắm bắt toàn diện:")

    if kpis:
        table_kpi = doc.add_table(rows=len(kpis) + 1, cols=3)
        table_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
        table_kpi.style = 'Table Grid'
        hdr_cells = table_kpi.rows[0].cells
        hdr_cells[0].paragraphs[0].add_run("Chỉ số KPI trên Dashboard").bold = True
        hdr_cells[1].paragraphs[0].add_run("Giá trị đo lường").bold = True
        hdr_cells[2].paragraphs[0].add_run("Phân tích ý nghĩa quản trị & Tác động").bold = True

        for i, k in enumerate(kpis, 1):
            row_cells = table_kpi.rows[i].cells
            row_cells[0].paragraphs[0].add_run(str(k.get("label", ""))).bold = True
            val_run = row_cells[1].paragraphs[0].add_run(str(k.get("value", "")))
            val_run.bold = True
            val_run.font.color.rgb = RGBColor(22, 101, 52)
            detail_txt = k.get("analysis_detail") or k.get("sub", "")
            row_cells[2].paragraphs[0].add_run(str(detail_txt))
        doc.add_paragraph()

    # ==================== PHẦN III: PHÂN TÍCH SÂU THEO 4 CHIỀU DỮ LIỆU DASHBOARD ====================
    h3 = doc.add_heading("III. PHÂN TÍCH SÂU THEO CÁC CHIỀU DỮ LIỆU TRÊN DASHBOARD", level=1)
    for r in h3.runs: r.font.color.rgb = RGBColor(15, 44, 89)

    doc.add_paragraph("Dữ liệu của doanh nghiệp đã được bóc tách theo 4 chiều phân tích trọng tâm trên Dashboard. Dưới đây là số liệu chi tiết và nhận định quản trị cho từng chiều:")

    for idx, ch in enumerate(charts, 1):
        dim_badge = ch.get("dimension_badge", f"Chiều phân tích {idx}")
        ch_title = ch.get("title", "")
        unit = ch.get("unit", "")
        labels = ch.get("labels", [])
        values = ch.get("values", [])
        commentary = ch.get("insight_commentary", "")
        total_v = sum([float(v) for v in values if isinstance(v, (int, float))]) or 1.0

        sub_h = doc.add_heading(f"{idx}. {dim_badge}: {ch_title}", level=2)
        for r in sub_h.runs: r.font.color.rgb = RGBColor(30, 64, 175)

        p_comm = doc.add_paragraph()
        p_comm.add_run("• Phân tích & Nhận định số liệu: ").bold = True
        p_comm.add_run(str(commentary))

        if labels and values:
            t_ch = doc.add_table(rows=len(labels) + 1, cols=3)
            t_ch.alignment = WD_TABLE_ALIGNMENT.CENTER
            t_ch.style = 'Table Grid'
            t_ch.rows[0].cells[0].paragraphs[0].add_run("Phân nhóm / Hạng mục").bold = True
            t_ch.rows[0].cells[1].paragraphs[0].add_run(f"Giá trị ({unit or 'Số lượng'})").bold = True
            t_ch.rows[0].cells[2].paragraphs[0].add_run("Tỷ trọng đóng góp (%)").bold = True

            for r_i, (l_item, v_item) in enumerate(zip(labels, values), 1):
                pct = round((float(v_item) / total_v) * 100, 1) if isinstance(v_item, (int, float)) and total_v > 0 else 0
                val_fmt = f"{v_item:,.0f}" if isinstance(v_item, (int, float)) and v_item >= 100 else str(v_item)
                t_ch.rows[r_i].cells[0].paragraphs[0].add_run(str(l_item))
                t_ch.rows[r_i].cells[1].paragraphs[0].add_run(f"{val_fmt} {unit}".strip()).bold = True
                t_ch.rows[r_i].cells[2].paragraphs[0].add_run(f"{pct}%")
            doc.add_paragraph()

    # ==================== PHẦN IV: ĐIỂM NGHẼN, RỦI RO & TOP 5 TRỌNG TÂM ====================
    h4 = doc.add_heading("IV. NHẬN DIỆN ĐIỂM NGHẼN, RỦI RO & TOP 5 TRỌNG TÂM CẦN XỬ LÝ NGAY", level=1)
    for r in h4.runs: r.font.color.rgb = RGBColor(15, 44, 89)

    bottlenecks = roadmap.get("bottlenecks_and_risks", [])
    if bottlenecks:
        p_b_title = doc.add_paragraph()
        p_b_title.add_run("1. Các điểm nghẽn và rủi ro trọng yếu phát hiện từ số liệu Dashboard:").bold = True
        for b in bottlenecks:
            p_b = doc.add_paragraph(style='List Bullet')
            p_b.add_run(str(b))

    p_t5_title = doc.add_paragraph()
    p_t5_title.add_run("2. Danh mục Top 5 đối tượng / hạng mục trọng tâm cần ưu tiên nguồn lực xử lý:").bold = True

    if top_5:
        t_top5 = doc.add_table(rows=len(top_5) + 1, cols=5)
        t_top5.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_top5.style = 'Table Grid'
        headers_t5 = ["Hạng", "Đối tượng / Hạng mục", "Chỉ số", "Nguyên nhân / Lý do ưu tiên", "Giải pháp hành động cụ thể"]
        for c_i, h_text in enumerate(headers_t5):
            t_top5.rows[0].cells[c_i].paragraphs[0].add_run(h_text).bold = True

        for r_i, item in enumerate(top_5, 1):
            t_top5.rows[r_i].cells[0].paragraphs[0].add_run(f"#{item.get('rank', r_i)}").bold = True
            t_top5.rows[r_i].cells[1].paragraphs[0].add_run(f"{item.get('name', '')}\n({item.get('category', '')})").bold = True
            t_top5.rows[r_i].cells[2].paragraphs[0].add_run(str(item.get("metric", "")))
            t_top5.rows[r_i].cells[3].paragraphs[0].add_run(str(item.get("reason", "")))
            act_r = t_top5.rows[r_i].cells[4].paragraphs[0].add_run(str(item.get("recommended_action", "")))
            act_r.bold = True
            act_r.font.color.rgb = RGBColor(180, 83, 9)
        doc.add_paragraph()

    # ==================== PHẦN V: ĐỊNH HƯỚNG PHÁT TRIỂN TIẾP THEO & KIẾN NGHỊ TRÌNH CẤP TRÊN ====================
    h5 = doc.add_heading("V. ĐỊNH HƯỚNG PHÁT TRIỂN TIẾP THEO & KIẾN NGHỊ TRÌNH CẤP TRÊN PHÊ DUYỆT", level=1)
    for r in h5.runs: r.font.color.rgb = RGBColor(15, 44, 89)

    short_term = roadmap.get("short_term_actions", [])
    if short_term:
        p_st = doc.add_paragraph()
        p_st.add_run("1. Giải pháp hành động ngắn hạn (Trong 30 ngày tới - Tháo gỡ điểm nghẽn tức thời):").bold = True
        for s_item in short_term:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(str(s_item))

    long_term = roadmap.get("medium_long_term_orientation", [])
    if long_term:
        p_lt = doc.add_paragraph()
        p_lt.add_run("2. Định hướng phát triển trung và dài hạn (Quý tới / 6 - 12 tháng):").bold = True
        for l_item in long_term:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(str(l_item))

    proposals = roadmap.get("proposals_for_upper_management", [])
    if proposals:
        p_pr = doc.add_paragraph()
        p_pr.add_run("3. Kiến nghị & Đề xuất trình Cấp trên / Ban Giám đốc xem xét phê duyệt:").bold = True
        for prop in proposals:
            p = doc.add_paragraph(style='List Bullet')
            r_prop = p.add_run(str(prop))
            r_prop.bold = True

    doc.add_paragraph()
    # Khung chữ ký trình Cấp trên
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_left = sig_table.rows[0].cells[0].paragraphs[0]
    sig_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sig_left.add_run("NGƯỜI LẬP BÁO CÁO / ĐƠN VỊ TRÌNH\n").bold = True
    sig_left.add_run("(Ký và ghi rõ họ tên)\n\n\n\n")

    sig_right = sig_table.rows[0].cells[1].paragraphs[0]
    sig_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sig_right.add_run("Ý KIẾN PHÊ DUYỆT CỦA CẤP TRÊN / BAN GIÁM ĐỐC\n").bold = True
    sig_right.add_run("(Phê duyệt định hướng & giao chỉ tiêu thực hiện)\n\n\n\n")

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

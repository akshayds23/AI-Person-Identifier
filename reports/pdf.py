"""VisionAI Campus - PDF Report Generator"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer)
from datetime import datetime
from config import SCHOOL_NAME
from database.models import SettingsModel


class PDFReportGenerator:
    @staticmethod
    def generate_attendance(filepath: str, data: list):
        school = SettingsModel.get("school_name", SCHOOL_NAME)
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Header
        elements.append(Paragraph(school, styles["Title"]))
        elements.append(Paragraph("Attendance Report", styles["Heading2"]))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 20))

        # Table
        table_data = [["Name", "Roll No", "Class", "Date", "Time", "Confidence"]]
        for r in data:
            conf = r.get("confidence", 0)
            table_data.append([
                r.get("name", ""), r.get("roll_no", ""),
                r.get("class", ""), str(r.get("date", "")),
                str(r.get("time", "")),
                f"{conf:.0%}" if conf else "—",
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#06b6d4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8fafc")]),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

        # Summary
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"Total Records: {len(data)}", styles["Normal"]
        ))

        doc.build(elements)

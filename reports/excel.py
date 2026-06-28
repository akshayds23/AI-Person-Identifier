"""VisionAI Campus - Excel Report Generator"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from config import SCHOOL_NAME
from database.models import SettingsModel


class ExcelReportGenerator:
    @staticmethod
    def generate_attendance(filepath: str, data: list):
        school = SettingsModel.get("school_name", SCHOOL_NAME)
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance"

        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill("solid", fgColor="06B6D4")
        center = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )
        alt_fill = PatternFill("solid", fgColor="F8FAFC")

        # Title row
        ws.merge_cells("A1:F1")
        ws["A1"] = f"{school} — Attendance Report"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = center

        ws.merge_cells("A2:F2")
        ws["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws["A2"].alignment = center

        # Headers
        headers = ["Name", "Roll No", "Class", "Date", "Time", "Confidence"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin_border

        # Data
        for i, r in enumerate(data):
            row = i + 5
            conf = r.get("confidence", 0)
            values = [
                r.get("name", ""), r.get("roll_no", ""),
                r.get("class", ""), str(r.get("date", "")),
                str(r.get("time", "")),
                f"{conf:.0%}" if conf else "—",
            ]
            for col, v in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=v)
                cell.alignment = center
                cell.border = thin_border
                if i % 2 == 1:
                    cell.fill = alt_fill

        # Auto-width
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 16

        # Summary
        summary_row = len(data) + 6
        ws.cell(row=summary_row, column=1, value=f"Total: {len(data)} records")
        ws.cell(row=summary_row, column=1).font = Font(bold=True)

        wb.save(filepath)

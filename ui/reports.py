"""
VisionAI Campus - Reports Page
================================
Attendance and visitor report generation with export.
"""

from datetime import date, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QTabWidget, QComboBox,
                                QDateEdit, QFileDialog, QFrame)
from PySide6.QtCore import Qt, QDate

from database.models import AttendanceModel, VisitorModel, StudentModel
from reports.excel import ExcelReportGenerator
from reports.pdf import PDFReportGenerator
from reports.csv_export import CSVExporter
from ui.widgets.notification import NotificationManager
from utils.logger import logger


class ReportsPage(QWidget):
    """Attendance and visitor reports with export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📊  Reports")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_attendance_tab(), "Attendance Reports")
        tabs.addTab(self._build_visitor_tab(), "Visitor Reports")
        layout.addWidget(tabs, 1)

    def _build_attendance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Filters
        filters = QHBoxLayout()

        filters.addWidget(QLabel("Period:"))
        self._att_period = QComboBox()
        self._att_period.setFixedHeight(40)
        self._att_period.addItems(["Today", "This Week", "This Month", "Custom"])
        self._att_period.currentIndexChanged.connect(self._on_att_period_change)
        filters.addWidget(self._att_period)

        filters.addWidget(QLabel("Class:"))
        self._att_class = QComboBox()
        self._att_class.setFixedHeight(40)
        self._att_class.addItem("All", "")
        for cls in StudentModel.get_classes():
            self._att_class.addItem(cls, cls)
        filters.addWidget(self._att_class)

        filters.addWidget(QLabel("From:"))
        self._att_from = QDateEdit()
        self._att_from.setDate(QDate.currentDate())
        self._att_from.setCalendarPopup(True)
        self._att_from.setFixedHeight(40)
        filters.addWidget(self._att_from)

        filters.addWidget(QLabel("To:"))
        self._att_to = QDateEdit()
        self._att_to.setDate(QDate.currentDate())
        self._att_to.setCalendarPopup(True)
        self._att_to.setFixedHeight(40)
        filters.addWidget(self._att_to)

        gen_btn = QPushButton("📊 Generate")
        gen_btn.setObjectName("primaryButton")
        gen_btn.setFixedHeight(40)
        gen_btn.clicked.connect(self._generate_attendance_report)
        filters.addWidget(gen_btn)

        layout.addLayout(filters)

        # Summary
        self._att_summary = QLabel("Select a period and click Generate")
        self._att_summary.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 8px;")
        layout.addWidget(self._att_summary)

        # Table
        self._att_table = QTableWidget()
        self._att_table.setColumnCount(6)
        self._att_table.setHorizontalHeaderLabels(
            ["Name", "Roll No", "Class", "Date", "Time", "Confidence"]
        )
        self._att_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._att_table.setAlternatingRowColors(True)
        self._att_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._att_table, 1)

        # Export buttons
        export_row = QHBoxLayout()
        export_row.addStretch()

        pdf_btn = QPushButton("📄 Export PDF")
        pdf_btn.setFixedHeight(40)
        pdf_btn.clicked.connect(lambda: self._export_attendance("pdf"))
        export_row.addWidget(pdf_btn)

        excel_btn = QPushButton("📊 Export Excel")
        excel_btn.setFixedHeight(40)
        excel_btn.clicked.connect(lambda: self._export_attendance("excel"))
        export_row.addWidget(excel_btn)

        csv_btn = QPushButton("📋 Export CSV")
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(lambda: self._export_attendance("csv"))
        export_row.addWidget(csv_btn)

        layout.addLayout(export_row)
        return page

    def _build_visitor_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("From:"))
        self._vis_from = QDateEdit()
        self._vis_from.setDate(QDate.currentDate())
        self._vis_from.setCalendarPopup(True)
        self._vis_from.setFixedHeight(40)
        filters.addWidget(self._vis_from)

        filters.addWidget(QLabel("To:"))
        self._vis_to = QDateEdit()
        self._vis_to.setDate(QDate.currentDate())
        self._vis_to.setCalendarPopup(True)
        self._vis_to.setFixedHeight(40)
        filters.addWidget(self._vis_to)

        gen_btn = QPushButton("📊 Generate")
        gen_btn.setObjectName("primaryButton")
        gen_btn.setFixedHeight(40)
        gen_btn.clicked.connect(self._generate_visitor_report)
        filters.addWidget(gen_btn)

        layout.addLayout(filters)

        self._vis_table = QTableWidget()
        self._vis_table.setColumnCount(5)
        self._vis_table.setHorizontalHeaderLabels(
            ["ID", "Entry Time", "Exit Time", "Status", "Confidence"]
        )
        self._vis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._vis_table.setAlternatingRowColors(True)
        self._vis_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._vis_table, 1)

        export_row = QHBoxLayout()
        export_row.addStretch()
        csv_btn = QPushButton("📋 Export CSV")
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._export_visitor_csv)
        export_row.addWidget(csv_btn)
        layout.addLayout(export_row)

        return page

    def _on_att_period_change(self, idx):
        today = date.today()
        if idx == 0:  # Today
            self._att_from.setDate(QDate.currentDate())
            self._att_to.setDate(QDate.currentDate())
        elif idx == 1:  # Week
            start = today - timedelta(days=today.weekday())
            self._att_from.setDate(QDate(start.year, start.month, start.day))
            self._att_to.setDate(QDate.currentDate())
        elif idx == 2:  # Month
            self._att_from.setDate(QDate(today.year, today.month, 1))
            self._att_to.setDate(QDate.currentDate())

    def _generate_attendance_report(self):
        start = self._att_from.date().toString("yyyy-MM-dd")
        end = self._att_to.date().toString("yyyy-MM-dd")
        cls = self._att_class.currentData() or ""

        self._att_data = AttendanceModel.get_report(start, end, cls)
        self._att_table.setRowCount(len(self._att_data))

        for i, r in enumerate(self._att_data):
            self._att_table.setItem(i, 0, QTableWidgetItem(r.get("name", "")))
            self._att_table.setItem(i, 1, QTableWidgetItem(r.get("roll_no", "")))
            self._att_table.setItem(i, 2, QTableWidgetItem(r.get("class", "")))
            self._att_table.setItem(i, 3, QTableWidgetItem(str(r.get("date", ""))))
            self._att_table.setItem(i, 4, QTableWidgetItem(str(r.get("time", ""))))
            conf = r.get("confidence", 0)
            self._att_table.setItem(i, 5, QTableWidgetItem(
                f"{conf:.0%}" if conf else "—"
            ))

        self._att_summary.setText(
            f"📋 {len(self._att_data)} records from {start} to {end}"
        )

    def _export_attendance(self, fmt: str):
        if not hasattr(self, '_att_data') or not self._att_data:
            NotificationManager.get_instance().show("Generate a report first", "warning")
            return

        ext_map = {"pdf": "PDF (*.pdf)", "excel": "Excel (*.xlsx)", "csv": "CSV (*.csv)"}
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", ext_map[fmt])
        if not path:
            return

        try:
            if fmt == "pdf":
                PDFReportGenerator.generate_attendance(path, self._att_data)
            elif fmt == "excel":
                ExcelReportGenerator.generate_attendance(path, self._att_data)
            elif fmt == "csv":
                CSVExporter.export_attendance(path, self._att_data)
            NotificationManager.get_instance().show(f"Report exported to {path}", "success")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            NotificationManager.get_instance().show(f"Export failed: {e}", "error")

    def _generate_visitor_report(self):
        start = self._vis_from.date().toString("yyyy-MM-dd")
        end = self._vis_to.date().toString("yyyy-MM-dd")

        self._vis_data = VisitorModel.get_by_date_range(start, end)
        self._vis_table.setRowCount(len(self._vis_data))

        for i, v in enumerate(self._vis_data):
            self._vis_table.setItem(i, 0, QTableWidgetItem(str(v["visitor_id"])))
            self._vis_table.setItem(i, 1, QTableWidgetItem(str(v.get("entry_time", ""))))
            self._vis_table.setItem(i, 2, QTableWidgetItem(str(v.get("exit_time", "") or "—")))
            self._vis_table.setItem(i, 3, QTableWidgetItem(v.get("status", "")))
            conf = v.get("confidence", 0)
            self._vis_table.setItem(i, 4, QTableWidgetItem(f"{conf:.0%}" if conf else "—"))

    def _export_visitor_csv(self):
        if not hasattr(self, '_vis_data') or not self._vis_data:
            NotificationManager.get_instance().show("Generate a report first", "warning")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export", "", "CSV (*.csv)")
        if path:
            CSVExporter.export_visitors(path, self._vis_data)
            NotificationManager.get_instance().show("Exported", "success")

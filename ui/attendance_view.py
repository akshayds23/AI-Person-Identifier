"""
VisionAI Campus - Attendance View Page
========================================
Attendance monitoring and history viewing.
"""

from datetime import date
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QComboBox, QDateEdit, QFrame)
from PySide6.QtCore import Qt, QDate

from database.models import AttendanceModel, StudentModel
from ui.widgets.notification import NotificationManager


class AttendancePage(QWidget):
    """Attendance monitoring and history page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("📋  Attendance")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Filters
        filters = QHBoxLayout()
        filters.setSpacing(12)

        filters.addWidget(QLabel("Class:"))
        self._class_combo = QComboBox()
        self._class_combo.setFixedHeight(40)
        self._class_combo.setMinimumWidth(120)
        self._class_combo.addItem("All Classes", "")
        for cls in StudentModel.get_classes():
            self._class_combo.addItem(cls, cls)
        self._class_combo.currentIndexChanged.connect(self._load_data)
        filters.addWidget(self._class_combo)

        filters.addWidget(QLabel("Date:"))
        self._date_edit = QDateEdit()
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setFixedHeight(40)
        self._date_edit.dateChanged.connect(self._load_data)
        filters.addWidget(self._date_edit)

        filters.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self._load_data)
        filters.addWidget(refresh_btn)

        layout.addLayout(filters)

        # Stats row
        stats = QHBoxLayout()
        self._present_label = QLabel("Present: 0")
        self._present_label.setStyleSheet(
            "color: #10b981; font-size: 16px; font-weight: 600; padding: 8px;"
        )
        stats.addWidget(self._present_label)

        self._total_label = QLabel("Total Students: 0")
        self._total_label.setStyleSheet(
            "color: #94a3b8; font-size: 16px; padding: 8px;"
        )
        stats.addWidget(self._total_label)

        self._percent_label = QLabel("Attendance: —")
        self._percent_label.setStyleSheet(
            "color: #06b6d4; font-size: 16px; font-weight: 600; padding: 8px;"
        )
        stats.addWidget(self._percent_label)

        stats.addStretch()
        layout.addLayout(stats)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Roll No", "Class", "Section", "Time", "Confidence"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self._table, 1)

        self._load_data()

    def _load_data(self):
        cls = self._class_combo.currentData() or ""
        target_date = self._date_edit.date().toString("yyyy-MM-dd")

        records = AttendanceModel.get_by_date(target_date, cls)
        self._table.setRowCount(len(records))

        for i, r in enumerate(records):
            self._table.setItem(i, 0, QTableWidgetItem(r.get("name", "")))
            self._table.setItem(i, 1, QTableWidgetItem(r.get("roll_no", "")))
            self._table.setItem(i, 2, QTableWidgetItem(r.get("class", "")))
            self._table.setItem(i, 3, QTableWidgetItem(r.get("section", "")))
            self._table.setItem(i, 4, QTableWidgetItem(str(r.get("time", ""))))
            conf = r.get("confidence", 0)
            self._table.setItem(i, 5, QTableWidgetItem(f"{conf:.0%}" if conf else "—"))

        present = len(records)
        total = StudentModel.count()
        pct = (present / total * 100) if total > 0 else 0

        self._present_label.setText(f"Present: {present}")
        self._total_label.setText(f"Total Students: {total}")
        self._percent_label.setText(f"Attendance: {pct:.1f}%")

    def refresh(self):
        self._load_data()

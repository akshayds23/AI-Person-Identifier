"""
VisionAI Campus - Visitor View Page
=====================================
Visitor monitoring and log page.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QFrame)
from PySide6.QtCore import Qt, QTimer

from database.models import VisitorModel
from ui.widgets.stat_card import StatCard


class VisitorPage(QWidget):
    """Visitor tracking and log page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🚶  Visitor Management")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Stat cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._in_card = StatCard("➡️", "0", "Entered", "green")
        self._out_card = StatCard("⬅️", "0", "Exited", "amber")
        self._occ_card = StatCard("🏢", "0", "Occupancy", "cyan")
        self._total_card = StatCard("👥", "0", "Total Today", "purple")

        cards_row.addWidget(self._in_card)
        cards_row.addWidget(self._out_card)
        cards_row.addWidget(self._occ_card)
        cards_row.addWidget(self._total_card)
        layout.addLayout(cards_row)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Visitor Log"))
        lbl = toolbar.itemAt(0).widget()
        lbl.setObjectName("sectionLabel")
        lbl.setStyleSheet("font-size: 16px;")
        toolbar.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Entry Time", "Exit Time", "Status", "Confidence"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self._table, 1)

        # Auto-refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start(10000)  # every 10s

        self._load_data()

    def _load_data(self):
        visitors = VisitorModel.get_today()
        counts = VisitorModel.get_today_count()

        self._total_card.set_value(str(counts["total"]))
        self._occ_card.set_value(str(counts["inside"]))

        self._table.setRowCount(len(visitors))
        for i, v in enumerate(visitors):
            self._table.setItem(i, 0, QTableWidgetItem(str(v["visitor_id"])))
            self._table.setItem(i, 1, QTableWidgetItem(str(v.get("entry_time", ""))))
            self._table.setItem(i, 2, QTableWidgetItem(str(v.get("exit_time", "") or "—")))
            self._table.setItem(i, 3, QTableWidgetItem(v.get("status", "")))
            conf = v.get("confidence", 0)
            self._table.setItem(i, 4, QTableWidgetItem(f"{conf:.0%}" if conf else "—"))

    def update_counts(self, in_count: int, out_count: int, occupancy: int):
        self._in_card.set_value(str(in_count))
        self._out_card.set_value(str(out_count))
        self._occ_card.set_value(str(occupancy))

    def refresh(self):
        self._load_data()

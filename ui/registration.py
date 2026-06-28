"""
VisionAI Campus - Student Management Page
============================================
Full CRUD UI for student registration with face capture.
"""

import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QFrame,
                                QComboBox, QDialog, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap, QImage

from database.models import StudentModel, SettingsModel
from ui.widgets.notification import NotificationManager
from ui.widgets.camera_view import CameraView
from config import PHOTOS_DIR
from utils.helpers import generate_photo_filename
from utils.logger import logger


class FaceCaptureDialog(QDialog):
    """Dialog to capture face photos from camera."""

    face_captured = Signal(str)  # photo path

    def __init__(self, student_name: str, roll_no: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Capture Face — {student_name}")
        self.setFixedSize(640, 520)

        self._name = student_name
        self._roll_no = roll_no
        self._cap = None
        self._photos = []
        self._max_photos = 5

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Camera preview
        self._preview = QLabel("Starting camera...")
        self._preview.setObjectName("cameraView")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setMinimumHeight(360)
        layout.addWidget(self._preview)

        # Status
        info = QHBoxLayout()
        self._status = QLabel(f"Photos: 0/{self._max_photos}")
        self._status.setStyleSheet("color: #94a3b8; font-size: 14px;")
        info.addWidget(self._status)
        info.addStretch()

        self._capture_btn = QPushButton(f"📸  Capture (0/{self._max_photos})")
        self._capture_btn.setObjectName("primaryButton")
        self._capture_btn.setFixedHeight(42)
        self._capture_btn.setCursor(Qt.PointingHandCursor)
        self._capture_btn.clicked.connect(self._take_photo)
        info.addWidget(self._capture_btn)

        done_btn = QPushButton("✓ Done")
        done_btn.setObjectName("successButton")
        done_btn.setFixedHeight(42)
        done_btn.clicked.connect(self.accept)
        info.addWidget(done_btn)

        layout.addLayout(info)

        # Start camera
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_frame)
        self._start_camera()

    def _start_camera(self):
        try:
            camera_idx = int(SettingsModel.get("camera_index", "0"))
        except ValueError:
            camera_idx = 0
        self._cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
        if self._cap.isOpened():
            self._timer.start(33)  # ~30fps
        else:
            self._preview.setText("❌ Camera not available")

    def _update_frame(self):
        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                self._current_frame = frame
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                self._preview.setPixmap(
                    QPixmap.fromImage(img).scaled(
                        self._preview.size(), Qt.KeepAspectRatio, Qt.FastTransformation
                    )
                )

    def _take_photo(self):
        if not hasattr(self, '_current_frame'):
            return
        if len(self._photos) >= self._max_photos:
            return

        fname = generate_photo_filename(self._name, self._roll_no, len(self._photos))
        path = PHOTOS_DIR / fname
        cv2.imwrite(str(path), self._current_frame)
        self._photos.append(str(path))

        count = len(self._photos)
        self._status.setText(f"Photos: {count}/{self._max_photos}")
        self._capture_btn.setText(f"📸  Capture ({count}/{self._max_photos})")

        if count >= self._max_photos:
            self._capture_btn.setEnabled(False)

        self.face_captured.emit(str(path))

    def get_photos(self) -> list:
        return self._photos

    def closeEvent(self, event):
        self._timer.stop()
        if self._cap:
            self._cap.release()
        event.accept()


class StudentManagementPage(QWidget):
    """Student registration and management page."""

    def __init__(self, recognizer=None, parent=None):
        super().__init__(parent)
        self._recognizer = recognizer

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Left: Form
        form_frame = QFrame()
        form_frame.setObjectName("glassCard")
        form_frame.setFixedWidth(360)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Student Registration"))
        lbl = form_layout.itemAt(0).widget()
        lbl.setObjectName("sectionLabel")

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Full Name")
        self._name_input.setFixedHeight(40)
        form_layout.addWidget(self._name_input)

        self._roll_input = QLineEdit()
        self._roll_input.setPlaceholderText("Roll Number")
        self._roll_input.setFixedHeight(40)
        form_layout.addWidget(self._roll_input)

        self._class_input = QLineEdit()
        self._class_input.setPlaceholderText("Class (e.g., 10)")
        self._class_input.setFixedHeight(40)
        form_layout.addWidget(self._class_input)

        self._section_input = QLineEdit()
        self._section_input.setPlaceholderText("Section (e.g., A)")
        self._section_input.setFixedHeight(40)
        form_layout.addWidget(self._section_input)

        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("Phone (optional)")
        self._phone_input.setFixedHeight(40)
        form_layout.addWidget(self._phone_input)

        self._guardian_input = QLineEdit()
        self._guardian_input.setPlaceholderText("Guardian Name (optional)")
        self._guardian_input.setFixedHeight(40)
        form_layout.addWidget(self._guardian_input)

        # Photo label
        self._photo_label = QLabel("No photo captured")
        self._photo_label.setStyleSheet("color: #64748b; padding: 8px;")
        self._photo_label.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self._photo_label)

        # Capture button
        capture_btn = QPushButton("📸  Capture Face")
        capture_btn.setObjectName("accentButton")
        capture_btn.setFixedHeight(42)
        capture_btn.setCursor(Qt.PointingHandCursor)
        capture_btn.clicked.connect(self._capture_face)
        form_layout.addWidget(capture_btn)

        # Save / Update / Delete buttons
        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._save_btn.setObjectName("successButton")
        self._save_btn.setFixedHeight(40)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._save_student)
        btn_row.addWidget(self._save_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.setFixedHeight(40)
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_student)
        btn_row.addWidget(self._delete_btn)

        form_layout.addLayout(btn_row)

        clear_btn = QPushButton("Clear Form")
        clear_btn.setFixedHeight(36)
        clear_btn.clicked.connect(self._clear_form)
        form_layout.addWidget(clear_btn)

        form_layout.addStretch()
        layout.addWidget(form_frame)

        # Right: Table
        right = QVBoxLayout()

        # Toolbar
        toolbar = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Search students...")
        self._search_input.setObjectName("searchInput")
        self._search_input.setFixedHeight(40)
        self._search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_input, 1)

        import_btn = QPushButton("📥 Import CSV")
        import_btn.setFixedHeight(40)
        import_btn.clicked.connect(self._import_csv)
        toolbar.addWidget(import_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(export_btn)

        right.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Roll No", "Class", "Section", "Phone", "Guardian"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_select)
        right.addWidget(self._table, 1)

        # Count
        self._count_label = QLabel("Total: 0 students")
        self._count_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        right.addWidget(self._count_label)

        layout.addLayout(right, 1)

        # State
        self._selected_id = None
        self._photo_path = ""

        # Load data
        self._load_students()

    def _load_students(self, query: str = ""):
        students = StudentModel.search(query) if query else StudentModel.get_all()
        self._table.setRowCount(len(students))
        for i, s in enumerate(students):
            self._table.setItem(i, 0, QTableWidgetItem(s["name"]))
            self._table.setItem(i, 1, QTableWidgetItem(s["roll_no"]))
            self._table.setItem(i, 2, QTableWidgetItem(s["class"]))
            self._table.setItem(i, 3, QTableWidgetItem(s.get("section", "")))
            self._table.setItem(i, 4, QTableWidgetItem(s.get("phone", "")))
            self._table.setItem(i, 5, QTableWidgetItem(s.get("guardian", "")))
            # Store ID in first column's data
            self._table.item(i, 0).setData(Qt.UserRole, s["student_id"])

        self._count_label.setText(f"Total: {len(students)} students")

    def _on_search(self, text: str):
        self._load_students(text)

    def _on_select(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        row = self._table.currentRow()
        self._selected_id = self._table.item(row, 0).data(Qt.UserRole)
        self._name_input.setText(self._table.item(row, 0).text())
        self._roll_input.setText(self._table.item(row, 1).text())
        self._class_input.setText(self._table.item(row, 2).text())
        self._section_input.setText(self._table.item(row, 3).text())
        self._phone_input.setText(self._table.item(row, 4).text())
        self._guardian_input.setText(self._table.item(row, 5).text())
        self._delete_btn.setEnabled(True)
        self._save_btn.setText("Update")

    def _save_student(self):
        name = self._name_input.text().strip()
        roll = self._roll_input.text().strip()
        cls = self._class_input.text().strip()

        if not name or not roll or not cls:
            NotificationManager.get_instance().show(
                "Name, Roll No, and Class are required", "warning"
            )
            return

        if self._selected_id:
            StudentModel.update(
                self._selected_id,
                name=name, roll_no=roll,
                **{"class": cls},
                section=self._section_input.text().strip(),
                phone=self._phone_input.text().strip(),
                guardian=self._guardian_input.text().strip(),
                photo_path=self._photo_path,
            )
            NotificationManager.get_instance().show(f"Student '{name}' updated", "success")
        else:
            sid = StudentModel.add(
                name=name, roll_no=roll, cls=cls,
                section=self._section_input.text().strip(),
                phone=self._phone_input.text().strip(),
                guardian=self._guardian_input.text().strip(),
                photo_path=self._photo_path,
            )
            if sid:
                self._selected_id = sid
                NotificationManager.get_instance().show(f"Student '{name}' added", "success")
            else:
                NotificationManager.get_instance().show("Failed to add student", "error")
                return

        self._load_students()
        self._clear_form()

    def _delete_student(self):
        if not self._selected_id:
            return
        name = self._name_input.text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete student '{name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            StudentModel.delete(self._selected_id)
            NotificationManager.get_instance().show(f"Student '{name}' deleted", "info")
            self._load_students()
            self._clear_form()

    def _clear_form(self):
        self._selected_id = None
        self._photo_path = ""
        self._name_input.clear()
        self._roll_input.clear()
        self._class_input.clear()
        self._section_input.clear()
        self._phone_input.clear()
        self._guardian_input.clear()
        self._photo_label.setText("No photo captured")
        self._delete_btn.setEnabled(False)
        self._save_btn.setText("Save")
        self._table.clearSelection()

    def _capture_face(self):
        name = self._name_input.text().strip() or "Student"
        roll = self._roll_input.text().strip() or "000"
        dialog = FaceCaptureDialog(name, roll, self)
        if dialog.exec() == QDialog.Accepted:
            photos = dialog.get_photos()
            if photos:
                self._photo_path = photos[0]
                self._photo_label.setText(f"✅ {len(photos)} photo(s) captured")

                # Register face if recognizer available and student saved
                if self._recognizer and self._selected_id and photos:
                    frame = cv2.imread(photos[0])
                    if frame is not None:
                        self._recognizer.register_face(frame, self._selected_id)
                        NotificationManager.get_instance().show(
                            "Face registered successfully", "success"
                        )

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Students CSV", "", "CSV Files (*.csv)"
        )
        if path:
            s, f, errors = StudentModel.import_csv(path)
            NotificationManager.get_instance().show(
                f"Imported: {s} success, {f} failed", "success" if f == 0 else "warning"
            )
            self._load_students()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Students", "", "CSV Files (*.csv)"
        )
        if path:
            if StudentModel.export_csv(path):
                NotificationManager.get_instance().show("Students exported", "success")

    def set_recognizer(self, recognizer):
        self._recognizer = recognizer

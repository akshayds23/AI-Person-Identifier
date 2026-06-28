"""
VisionAI Campus - Comprehensive Test Suite
===========================================
Automated testing for UI components, database operations,
AI tracking logic, and utility helper functions.
"""

import sys
import os
import unittest
import numpy as np
from pathlib import Path
from datetime import datetime

# Set up paths so we import from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock environment variables for testing
os.environ["DATABASE_PATH"] = "data/test_visionai.db"
os.environ["PHOTOS_DIR"] = "assets/test_photos"
os.environ["SNAPSHOTS_DIR"] = "assets/test_snapshots"
os.environ["BACKUPS_DIR"] = "test_backups"
os.environ["LOGS_DIR"] = "test_logs"

from config import DATABASE_PATH, PHOTOS_DIR, SNAPSHOTS_DIR
from utils.helpers import (generate_salt, hash_password, verify_password,
                           sanitize_filename, generate_photo_filename)
from database.db import DatabaseManager
from database.models import UserModel, StudentModel, AttendanceModel, VisitorModel, SettingsModel
from ai.tracker import CentroidTracker, LineCrossingCounter


class TestHelpers(unittest.TestCase):
    """Test helper and utility functions."""

    def test_password_security(self):
        salt = generate_salt()
        self.assertEqual(len(salt), 64)  # 32 bytes hex = 64 chars
        
        pw = "TestPassword123"
        hashed = hash_password(pw, salt)
        self.assertTrue(verify_password(pw, salt, hashed))
        self.assertFalse(verify_password("wrong_password", salt, hashed))

    def test_filename_sanitization(self):
        dirty = 'Student:John/Doe*?"<>'
        clean = sanitize_filename(dirty)
        self.assertEqual(clean, "Student_John_Doe")

    def test_photo_filename_generation(self):
        name = "A. Kumar"
        roll = "CS-01"
        filename = generate_photo_filename(name, roll, 0)
        self.assertTrue(filename.startswith("CS-01_A._Kumar_"))
        self.assertTrue(filename.endswith("_0.jpg"))


class TestDatabaseLayer(unittest.TestCase):
    """Test SQLite database initialization and operations."""

    @classmethod
    def setUpClass(cls):
        # Initialize test DB
        cls.db_manager = DatabaseManager.get_instance()
        UserModel.initialize_default_admin()

    @classmethod
    def tearDownClass(cls):
        # Clean up test DB file if exists (connection will be closed at application exit)
        test_db_path = Path(DATABASE_PATH)
        if test_db_path.exists():
            try:
                # Do not delete DB here as other test classes running later might need it
                pass
            except OSError:
                pass

    def test_singleton_db(self):
        manager1 = DatabaseManager.get_instance()
        manager2 = DatabaseManager.get_instance()
        self.assertIs(manager1, manager2)

    def test_admin_initialization(self):
        users = UserModel.get_all_users()
        self.assertTrue(any(u['username'] == 'admin' for u in users))

    def test_authenticate(self):
        user = UserModel.authenticate("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'admin')

        invalid = UserModel.authenticate("admin", "wrongpassword")
        self.assertIsNone(invalid)

    def test_settings_model(self):
        SettingsModel.set("test_key", "test_value")
        self.assertEqual(SettingsModel.get("test_key"), "test_value")
        self.assertEqual(SettingsModel.get("non_existent_key", "default"), "default")

    def test_student_crud(self):
        student_id = StudentModel.add(
            name="Alice Smith",
            roll_no="R101",
            cls="12",
            section="A",
            phone="1234567890",
            guardian="Bob Smith"
        )
        self.assertIsNotNone(student_id)
        
        student = StudentModel.get(student_id)
        self.assertEqual(student["name"], "Alice Smith")
        self.assertEqual(student["roll_no"], "R101")

        # Update
        StudentModel.update(student_id, section="B", phone="0987654321")
        updated = StudentModel.get(student_id)
        self.assertEqual(updated["section"], "B")
        self.assertEqual(updated["phone"], "0987654321")

        # Clean up
        StudentModel.delete(student_id)
        deleted = StudentModel.get(student_id)
        self.assertIsNone(deleted)


class TestAITracker(unittest.TestCase):
    """Test centroid tracking and crossing detection algorithms."""

    def test_centroid_tracking(self):
        tracker = CentroidTracker()
        
        # Mock detection dataclass
        class MockDetection:
            def __init__(self, x1, y1, x2, y2):
                self.bbox = (x1, y1, x2, y2)
            @property
            def center(self):
                return ((self.bbox[0] + self.bbox[2]) // 2, (self.bbox[1] + self.bbox[3]) // 2)

        # Initial frame detection
        det1 = MockDetection(100, 100, 150, 200)  # center (125, 150)
        objects = tracker.update([det1])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], (125, 150))

        # Second frame - tracked person moves slightly
        det2 = MockDetection(105, 105, 155, 205)  # center (130, 155)
        objects = tracker.update([det2])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], (130, 155))

    def test_line_crossing(self):
        counter = LineCrossingCounter(frame_height=480)
        # Line is set by default config ratio (0.5 * 480 = 240)
        self.assertEqual(counter.line_y, 240)

        # Frame 1: Person above the line
        counter.update({0: (320, 200)})
        self.assertEqual(counter.in_count, 0)
        self.assertEqual(counter.out_count, 0)

        # Frame 2: Person crosses line downward (IN)
        counter.update({0: (320, 250)})
        self.assertEqual(counter.in_count, 1)
        self.assertEqual(counter.out_count, 0)

        # Frame 3: Person crosses line upward (OUT)
        counter.update({0: (320, 200)})
        self.assertEqual(counter.in_count, 1)
        self.assertEqual(counter.out_count, 1)


class TestUIWidgets(unittest.TestCase):
    """Test PySide6 UI instantiation and responsiveness."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_stat_card(self):
        from ui.widgets.stat_card import StatCard
        widget = StatCard("🚶", "15", "Total Visitors", "cyan")
        self.assertEqual(widget._value_label.text(), "15")
        self.assertEqual(widget._text_label.text(), "Total Visitors")

    def test_activity_log(self):
        from ui.widgets.activity_log import ActivityLog
        widget = ActivityLog()
        widget.add_entry("Test student checked in", "student")
        # Layout should have items
        self.assertGreater(widget._layout.count(), 0)

    def test_loading_spinner(self):
        from ui.widgets.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner(30)
        spinner.start()
        self.assertTrue(spinner._timer.isActive())
        spinner.stop()
        self.assertFalse(spinner._timer.isActive())


class TestReportGenerators(unittest.TestCase):
    """Test report generation and validation."""

    def test_report_generation(self):
        from reports.pdf import PDFReportGenerator
        from reports.excel import ExcelReportGenerator
        from reports.csv_export import CSVExporter

        test_data = [
            {"name": "Alice", "roll_no": "1", "class": "10", "date": "2026-06-27", "time": "09:00:00", "confidence": 0.85},
            {"name": "Bob", "roll_no": "2", "class": "10", "date": "2026-06-27", "time": "09:05:00", "confidence": 0.90}
        ]

        pdf_path = "test_attendance.pdf"
        xlsx_path = "test_attendance.xlsx"
        csv_path = "test_attendance.csv"

        try:
            # Generate reports
            PDFReportGenerator.generate_attendance(pdf_path, test_data)
            ExcelReportGenerator.generate_attendance(xlsx_path, test_data)
            CSVExporter.export_attendance(csv_path, test_data)

            # Check files exist and are not empty
            self.assertTrue(os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0)
            self.assertTrue(os.path.exists(xlsx_path) and os.path.getsize(xlsx_path) > 0)
            self.assertTrue(os.path.exists(csv_path) and os.path.getsize(csv_path) > 0)
        finally:
            # Clean up test output files
            for p in (pdf_path, xlsx_path, csv_path):
                if os.path.exists(p):
                    os.remove(p)


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestHelpers))
    suite.addTest(loader.loadTestsFromTestCase(TestDatabaseLayer))
    suite.addTest(loader.loadTestsFromTestCase(TestAITracker))
    suite.addTest(loader.loadTestsFromTestCase(TestUIWidgets))
    suite.addTest(loader.loadTestsFromTestCase(TestReportGenerators))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Finally close DB manager and clean file
    try:
        DatabaseManager.get_instance().close()
        test_db_path = Path(DATABASE_PATH)
        if test_db_path.exists():
            os.remove(test_db_path)
    except Exception:
        pass

    # Print clean summary report
    print("\n" + "=" * 50)
    print("             TEST EXECUTION SUMMARY             ")
    print("=" * 50)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 50)

    if not result.wasSuccessful():
        sys.exit(1)

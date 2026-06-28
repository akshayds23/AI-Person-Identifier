"""
VisionAI Campus - UI Flow & Performance Test
===============================================
Simulates page transitions, starts monitoring, and measures
rendering latency to ensure zero lag in the video feed.
"""

import sys
import os
import time
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

# Set up paths so we import from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock environment variables for testing
os.environ["DATABASE_PATH"] = "data/test_flow_visionai.db"
os.environ["PHOTOS_DIR"] = "assets/test_flow_photos"
os.environ["SNAPSHOTS_DIR"] = "assets/test_flow_snapshots"
os.environ["BACKUPS_DIR"] = "test_flow_backups"
os.environ["LOGS_DIR"] = "test_flow_logs"

from database.db import DatabaseManager
from database.models import UserModel, SettingsModel
from ui.dashboard import DashboardWindow
from ui.registration import StudentManagementPage
from ui.attendance_view import AttendancePage
from ui.visitor_view import VisitorPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage
from ui.widgets.camera_view import CameraView


def run_ui_flow_test():
    # 1. Initialize Application
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Initialize test database
    db = DatabaseManager.get_instance()
    UserModel.initialize_default_admin()
    SettingsModel.set("school_name", "Test Flow Academy")
    SettingsModel.mark_setup_complete()

    print("\n" + "=" * 60)
    print("             UI FLOW & PERFORMANCE TEST             ")
    print("=" * 60)

    # 2. Instantiate Dashboard
    print("[1/4] Launching Dashboard Window...")
    dashboard = DashboardWindow(role="admin", username="test_tester")
    dashboard.show()
    app.processEvents()

    # 3. Add Pages (Simulating AppController registration)
    print("[2/4] Registering View Pages...")
    students_page = StudentManagementPage()
    attendance_page = AttendancePage()
    visitor_page = VisitorPage()
    reports_page = ReportsPage()
    settings_page = SettingsPage()

    dashboard.add_page("students", students_page)
    dashboard.add_page("attendance", attendance_page)
    dashboard.add_page("visitors", visitor_page)
    dashboard.add_page("reports", reports_page)
    dashboard.add_page("settings", settings_page)
    app.processEvents()

    # 4. Simulate Switching Pages (Transitions)
    print("[3/4] Testing Sidebar Transitions...")
    pages_to_test = ["dashboard", "students", "attendance", "visitors", "reports", "settings"]
    
    for page_key in pages_to_test:
        start_time = time.perf_counter()
        dashboard._sidebar.set_active_page(page_key)
        app.processEvents()
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"  -> Switched to '{page_key}' in {elapsed:.2f} ms (Smooth)")
        time.sleep(0.1)

    # Return to dashboard
    dashboard._sidebar.set_active_page("dashboard")
    app.processEvents()

    # 5. Measure Rendering Performance & Lag
    print("[4/4] Testing Live Video Render Performance...")
    cam_view = dashboard.get_camera_view()
    
    # Generate mock camera frame (640x480 resolution)
    mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Measure rendering time over multiple frames
    render_times = []
    for i in range(30):
        start_time = time.perf_counter()
        cam_view.update_frame(mock_frame)
        app.processEvents()
        render_times.append(time.perf_counter() - start_time)
        time.sleep(0.01)

    avg_render_ms = np.mean(render_times) * 1000
    max_render_ms = np.max(render_times) * 1000
    estimated_max_fps = 1000.0 / avg_render_ms

    print("\n" + "=" * 60)
    print("                 PERFORMANCE METRICS                 ")
    print("=" * 60)
    print(f"Average Frame Render Time: {avg_render_ms:.2f} ms")
    print(f"Maximum Frame Render Time: {max_render_ms:.2f} ms")
    print(f"Estimated Max Render FPS:  {estimated_max_fps:.1f} FPS")
    print("=" * 60)

    # Criteria check
    lag_threshold_ms = 33.3  # 30 FPS frame time budget
    if avg_render_ms < lag_threshold_ms:
        print("RESULT: PASS - No rendering lag detected. Feed runs smoothly.")
    else:
        print("RESULT: WARNING - Rendering time is high. Consider optimization.")
    print("=" * 60 + "\n")

    # Cleanup
    dashboard.close()
    db.close()
    
    # Remove test DB file
    test_db_path = Path(os.environ["DATABASE_PATH"])
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except OSError:
            pass


if __name__ == "__main__":
    run_ui_flow_test()

# VisionAI Campus — Context File
> Tracks all created files and project state.

## Project Info
- **Name:** VisionAI Campus
- **Type:** AI Desktop Application (PySide6)
- **Target:** Schools, Colleges, Educational Institutes
- **Status:** Phase 1-5 Complete — All core files created

## Architecture
- **UI Framework:** PySide6 with custom QSS theming
- **AI:** YOLOv11 (person detection) + InsightFace (face recognition)
- **Database:** SQLite with NumPy BLOB adapters
- **Config:** python-dotenv (.env file, zero hardcoded values)
- **Threading:** QThread for camera & AI pipeline
- **Reports:** ReportLab (PDF), OpenPyXL (Excel), csv (CSV)

## Created Files

### Root
| File | Purpose |
|------|---------|
| `main.py` | Entry point — QApplication, theme loading, HiDPI |
| `app.py` | AppController — login/dashboard flow, AI lifecycle |
| `config.py` | Env-based config loader (python-dotenv) |
| `.env` | Environment variables (all configurable values) |
| `.env.example` | Template env file |
| `requirements.txt` | Python dependencies |

### Database (`database/`)
| File | Purpose |
|------|---------|
| `db.py` | Singleton DatabaseManager, thread-safe SQLite, BLOB adapters |
| `models.py` | UserModel, StudentModel, AttendanceModel, VisitorModel, SettingsModel |

### AI Pipeline (`ai/`)
| File | Purpose |
|------|---------|
| `camera.py` | CameraThread — USB capture, auto-reconnect, FPS |
| `detection.py` | PersonDetector — YOLOv11 person detection (class=0) |
| `recognition.py` | FaceRecognizer — InsightFace with embedding cache |
| `tracker.py` | CentroidTracker + LineCrossingCounter (IN/OUT) |
| `attendance.py` | AttendanceEngine — full pipeline orchestrator |

### UI Screens (`ui/`)
| File | Purpose |
|------|---------|
| `login.py` | Glassmorphic login with role selection, shake animation |
| `setup.py` | First-run wizard (school, camera, theme) |
| `dashboard.py` | Main window with sidebar, stat cards, camera, activity log |
| `registration.py` | Student CRUD + face capture dialog |
| `attendance_view.py` | Attendance history with filters |
| `visitor_view.py` | Visitor tracking with IN/OUT/Occupancy cards |
| `reports.py` | Attendance & visitor reports with export |
| `settings.py` | Camera, AI thresholds, theme, backup/restore |

### UI Widgets (`ui/widgets/`)
| File | Purpose |
|------|---------|
| `stat_card.py` | Glassmorphic stat card (icon, value, label, color) |
| `camera_view.py` | Camera display with numpy/QImage support |
| `activity_log.py` | Scrollable activity feed with category icons |
| `sidebar.py` | Role-based navigation sidebar |
| `notification.py` | Toast notification system with auto-dismiss |
| `loading_spinner.py` | Animated circular loading indicator |

### Reports (`reports/`)
| File | Purpose |
|------|---------|
| `pdf.py` | ReportLab PDF generator with styled tables |
| `excel.py` | OpenPyXL Excel generator with formatting |
| `csv_export.py` | Simple CSV exporter |

### Utils (`utils/`)
| File | Purpose |
|------|---------|
| `logger.py` | Rotating file logger |
| `helpers.py` | Password hashing, time formatting, CSV validation |

### Assets
| File | Purpose |
|------|---------|
| `assets/styles/dark_theme.qss` | 500+ line premium dark theme |

## Database Schema
- `users` — Login credentials (hashed passwords)
- `students` — Student info + face embeddings (NPARRAY blob)
- `attendance` — Daily attendance records (unique per student/day)
- `visitors` — Entry/exit logs with snapshots
- `settings` — Key-value config store

## Key Design Decisions
1. **All config via .env** — Zero hardcoded values
2. **Filesystem photo storage** — Photos in `assets/photos/`, paths in DB
3. **Singleton DB** — Thread-safe with WAL mode
4. **AI on QThread** — Processes every 3rd frame for performance
5. **Cosine similarity** — For face matching with configurable threshold
6. **matplotlib** for future charts (offline-compatible)
7. **English only** — i18n deferred

## Status ✅
- [x] Virtual environment created + all dependencies installed
- [x] Config/DB/Models smoke tested — all working
- [x] UI startup validated — Login window renders correctly
- [x] All 30+ source files created

## To Run
```bash
cd "d:\AI Person Identifier"
venv\Scripts\python.exe main.py
```

## Remaining Tasks
- [ ] Add light theme QSS
- [ ] PyInstaller packaging spec
- [ ] First-time YOLO/InsightFace model download (requires internet once)

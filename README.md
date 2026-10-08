# VisionAI Campus - AI Person Identifier

Desktop application that takes attendance and counts visitors from a live camera feed, built for schools and colleges.
A person detector, a face-recognition model and a tracker run in a background pipeline, so the UI stays responsive.

## What it does

- **Automatic attendance** - recognises registered students from the camera and marks them present once per cooldown window.
- **Visitor counting** - tracks every person in frame and counts IN / OUT crossings over a configurable line, with live occupancy.
- **Student registration** - add students and capture face samples; embeddings are stored and cached for fast matching.
- **Reports** - attendance and visitor reports with filters, exported to PDF, Excel or CSV.
- **Roles and setup** - login with roles, first-run setup wizard, backup and restore, all thresholds adjustable in Settings.

## How it works

```
Camera thread (OpenCV, auto-reconnect)
   -> every Nth frame
PersonDetector    YOLOv11n, person class only, confidence threshold
FaceRecognizer    InsightFace (buffalo_l) embeddings, cosine similarity vs. cached student embeddings
CentroidTracker   assigns stable IDs across frames; LineCrossingCounter -> IN / OUT
AttendanceEngine  orchestrates the pipeline, applies cooldowns, writes to SQLite
   -> Qt signals -> dashboard (live view, stat cards, activity log)
```

| Layer | Technology |
|---|---|
| Detection | Ultralytics YOLOv11 |
| Recognition | InsightFace + ONNX Runtime, SciPy cosine distance |
| Tracking | Centroid tracker with disappearance decay |
| UI | PySide6 (Qt), QThread workers, custom QSS theme |
| Storage | SQLite (thread-safe singleton, NumPy BLOB adapters for embeddings) |
| Reports | ReportLab (PDF), OpenPyXL (Excel), CSV |

Design choices worth noting:
- **Process every Nth frame** (`AI_PROCESS_EVERY_N_FRAMES`) to keep CPU use low on ordinary laptops while the video stays smooth.
- **Recognition cooldown** so one student standing in view is not marked present repeatedly.
- **All values come from `.env`** (camera, model paths, thresholds, storage paths) - nothing is hard-coded.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # adjust camera index, thresholds, paths
python main.py
```

Place the YOLO weights at `models/yolo11n.pt` (Ultralytics downloads them on first use) - InsightFace downloads `buffalo_l` automatically.
**Change the default admin password (`DEFAULT_ADMIN_PASSWORD`) before first run.**

## Project layout

```
ai/         camera, detection, recognition, tracker, attendance pipeline
database/   SQLite manager and models (users, students, attendance, visitors, settings)
ui/         login, setup wizard, dashboard, registration, attendance, visitors, reports, settings
reports/    PDF / Excel / CSV exporters
tests/      UI flow and pipeline tests (python tests/run_all_tests.py)
```

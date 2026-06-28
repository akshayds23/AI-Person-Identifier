"""VisionAI Campus - CSV Exporter"""

import csv


class CSVExporter:
    @staticmethod
    def export_attendance(filepath: str, data: list):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Roll No", "Class", "Date", "Time", "Confidence"])
            for r in data:
                conf = r.get("confidence", 0)
                writer.writerow([
                    r.get("name", ""), r.get("roll_no", ""),
                    r.get("class", ""), str(r.get("date", "")),
                    str(r.get("time", "")),
                    f"{conf:.2f}" if conf else "",
                ])

    @staticmethod
    def export_visitors(filepath: str, data: list):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Entry Time", "Exit Time", "Status", "Confidence"])
            for v in data:
                conf = v.get("confidence", 0)
                writer.writerow([
                    v.get("visitor_id", ""),
                    str(v.get("entry_time", "")),
                    str(v.get("exit_time", "") or ""),
                    v.get("status", ""),
                    f"{conf:.2f}" if conf else "",
                ])

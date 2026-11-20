import calendar
import csv
import datetime
import io
from typing import Any

from sqlalchemy.orm import Session

import models


def get_sample_csv_content() -> str:
    """Return standard sample CSV for bulk health worker onboarding."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["worker_code", "name", "role", "center", "phone"])
    writer.writerow(["HW101", "Pooja Kumari", "ASHA Worker", "Patna Central", "+91-9876543210"])
    writer.writerow(["HW102", "Sunita Devi", "ANM", "Danapur", "+91-9876543211"])
    writer.writerow(["HW103", "Anita Singh", "ASHA Worker", "Maner", "+91-9876543212"])
    writer.writerow(["HW104", "Rekha Sharma", "Medical Officer", "Phulwari Sharif", "+91-9876543213"])
    writer.writerow(["HW105", "Geeta Verma", "ASHA Worker", "Bakhtiyarpur", "+91-9876543214"])
    return output.getvalue()


def parse_and_import_workers(file_content: bytes | str, db: Session) -> dict[str, Any]:
    """Parse CSV content and import health workers, gracefully skipping duplicates."""
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
    else:
        text = file_content

    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames:
        return {"total_rows": 0, "created": 0, "skipped": 0, "errors": ["Empty or invalid CSV file"]}

    header_map = {}
    for fn in reader.fieldnames:
        if not fn:
            continue
        clean_fn = fn.strip().lower().replace(" ", "_").replace("-", "_")
        if clean_fn in ("worker_code", "workercode", "code", "id"):
            header_map[fn] = "worker_code"
        elif clean_fn in ("name", "worker_name", "full_name"):
            header_map[fn] = "name"
        elif clean_fn in ("role", "designation", "position"):
            header_map[fn] = "role"
        elif clean_fn in ("center", "sub_center", "phc", "facility", "location"):
            header_map[fn] = "center"
        elif clean_fn in ("phone", "mobile", "contact", "phone_number"):
            header_map[fn] = "phone"

    required_keys = {"name", "center", "phone"}
    found_keys = set(header_map.values())
    if not required_keys.issubset(found_keys):
        missing = required_keys - found_keys
        return {
            "total_rows": 0,
            "created": 0,
            "skipped": 0,
            "errors": [f"Missing required columns in CSV: {', '.join(sorted(missing))}"],
        }

    total_rows = 0
    created_count = 0
    skipped_count = 0
    errors: list[str] = []

    existing_workers = db.query(models.HealthWorker).all()
    existing_codes = {w.worker_code.strip().upper(): w for w in existing_workers if w.worker_code}
    existing_name_centers = {(w.name.strip().lower(), w.center.strip().lower()) for w in existing_workers}

    new_workers_to_add: list[models.HealthWorker] = []

    for idx, raw_row in enumerate(reader, start=2):
        total_rows += 1
        row = {}
        for orig_key, mapped_key in header_map.items():
            val = raw_row.get(orig_key, "")
            row[mapped_key] = val.strip() if val else ""

        name = row.get("name", "")
        center = row.get("center", "")
        phone = row.get("phone", "")
        role = row.get("role") or "ASHA Worker"
        worker_code = row.get("worker_code")

        if not name or not center or not phone:
            errors.append(f"Row {idx}: Name, Center, and Phone cannot be blank.")
            continue

        if not worker_code:
            worker_code = f"HW{1000 + len(existing_codes) + len(new_workers_to_add) + 1}"

        norm_code = worker_code.upper()
        norm_pair = (name.lower(), center.lower())

        if norm_code in existing_codes or norm_pair in existing_name_centers:
            skipped_count += 1
            continue

        new_worker = models.HealthWorker(
            worker_code=worker_code,
            name=name,
            role=role,
            center=center,
            phone=phone,
            joined_on=datetime.date.today(),
        )
        new_workers_to_add.append(new_worker)
        existing_codes[norm_code] = new_worker
        existing_name_centers.add(norm_pair)

    if new_workers_to_add:
        db.add_all(new_workers_to_add)
        db.add(
            models.AuditLog(
                action="Bulk CSV Import",
                entity="HealthWorker",
                performed_by="supervisor",
                description=f"Imported {len(new_workers_to_add)} workers via CSV (skipped {skipped_count})",
            )
        )
        db.commit()
        created_count = len(new_workers_to_add)

    return {
        "total_rows": total_rows,
        "created": created_count,
        "skipped": skipped_count,
        "errors": errors,
    }


def generate_attendance_csv(db: Session, month_str: str, center: str | None = None) -> str:
    """Generate monthly attendance matrix CSV with UTF-8 BOM for Excel compatibility."""
    try:
        parts = month_str.strip().split("-")
        year = int(parts[0])
        month = int(parts[1])
        if month < 1 or month > 12:
            raise ValueError
    except Exception:
        raise ValueError("Invalid month format. Expected YYYY-MM (e.g. 2026-11)")

    _, num_days = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)

    worker_query = db.query(models.HealthWorker)
    if center and center.strip() and center.strip().lower() != "all":
        worker_query = worker_query.filter(models.HealthWorker.center == center.strip())

    workers = worker_query.order_by(models.HealthWorker.center, models.HealthWorker.name).all()

    att_query = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.date >= start_date,
        models.AttendanceRecord.date <= end_date,
    )
    if center and center.strip() and center.strip().lower() != "all":
        att_query = att_query.join(models.HealthWorker).filter(models.HealthWorker.center == center.strip())

    records = att_query.all()
    record_map: dict[tuple[int, int], str] = {
        (r.worker_id, r.date.day): r.status for r in records
    }

    status_abbrev = {
        "present": "P",
        "absent": "A",
        "half-day": "H",
        "leave": "L",
    }

    output = io.StringIO()
    output.write("\ufeff")

    writer = csv.writer(output)
    day_headers = [f"Day {d}" for d in range(1, num_days + 1)]
    writer.writerow([
        "Worker Code",
        "Name",
        "Role",
        "Center",
        "Phone",
        *day_headers,
        "Present Days",
        "Total Logged",
        "Attendance %",
    ])

    for w in workers:
        row_days = []
        present_count = 0.0
        logged_count = 0

        for d in range(1, num_days + 1):
            st = record_map.get((w.id, d))
            if st:
                abbrev = status_abbrev.get(st.lower(), st[:1].upper())
                row_days.append(abbrev)
                logged_count += 1
                if st.lower() in ("present", "p"):
                    present_count += 1.0
                elif st.lower() in ("half-day", "h"):
                    present_count += 0.5
            else:
                row_days.append("-")

        pct = round((present_count / logged_count * 100), 1) if logged_count > 0 else 0.0

        writer.writerow([
            w.worker_code,
            w.name,
            w.role,
            w.center,
            w.phone,
            *row_days,
            present_count,
            logged_count,
            f"{pct}%",
        ])

    return output.getvalue()

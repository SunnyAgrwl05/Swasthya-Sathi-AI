"""Run once: python seed.py
Creates demo health workers with 30 days of attendance history.
"""

import datetime
import random

from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.HealthWorker).count() == 0:

    workers = [
        models.HealthWorker(
            worker_code="HW001",
            name="Kajal Kumari",
            role="ASHA Worker",
            center="PHC Patna",
            phone="+91 9876500001",
        ),
        models.HealthWorker(
            worker_code="HW002",
            name="Sunny Kumar",
            role="ANM",
            center="PHC Bakhtiyarpur",
            phone="+91 9876500002",
        ),
        models.HealthWorker(
            worker_code="HW003",
            name="Neha Kumari",
            role="Anganwadi Worker",
            center="Sub-center Fatuha",
            phone="+91 9876500003",
        ),
        models.HealthWorker(
            worker_code="HW004",
            name="Rahul Kumar",
            role="ASHA Worker",
            center="Sub-center Gaya",
            phone="+91 9876500004",
        ),
        models.HealthWorker(
            worker_code="HW005",
            name="Aman Raj",
            role="ANM",
            center="PHC Patna",
            phone="+91 9876500005",
        ),
    ]

    db.add_all(workers)
    db.commit()

    for w in workers:
        db.refresh(w)

    today = datetime.date.today()

    weights = {
        "Kajal Kumari": [0.95, 0.02, 0.02, 0.01],
        "Sunny Kumar": [0.88, 0.08, 0.02, 0.02],
        "Neha Kumari": [0.58, 0.32, 0.05, 0.05],
        "Rahul Kumar": [0.91, 0.05, 0.02, 0.02],
        "Aman Raj": [0.65, 0.25, 0.05, 0.05],
    }

    statuses = [
        "present",
        "absent",
        "half-day",
        "leave",
    ]

    for w in workers:
        for i in range(1, 31):
            d = today - datetime.timedelta(days=i)

            status = random.choices(
                statuses,
                weights=weights[w.name],
            )[0]

            db.add(
                models.AttendanceRecord(
                    worker_id=w.id,
                    date=d,
                    status=status,
                    marked_by="seed",
                )
            )

    db.commit()

    print(f"✅ Successfully seeded {len(workers)} demo health workers.")

else:
    print("Workers already exist, skipping seed.")

db.close()


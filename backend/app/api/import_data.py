"""
Data Import API
- Load demo data (seed synthetic data)
- CSV upload for tasks, trains, block windows
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import io
import csv
from app.core.auth import get_current_user
from app.core.database import get_admin_db
from app.services.synthetic_data import get_all_synthetic_data
from app.services.priority_engine import calculate_priority_score

router = APIRouter()


@router.post("/load-demo-data")
async def load_demo_data(current_user: dict = Depends(get_current_user)):
    """
    Populate the database with synthetic demo data.
    This generates realistic simulated railway maintenance data.
    NOT real Indian Railways data.
    """
    try:
        db = get_admin_db()

        # Generate synthetic data
        data = get_all_synthetic_data()

        results = {
            "corridors": 0,
            "tasks": 0,
            "trains": 0,
            "forecasts": 0,
            "windows": 0,
            "errors": [],
        }

        batch_size = 100

        try:
            db.table("corridors").upsert(data["corridors"], on_conflict="corridor_id").execute()
            results["corridors"] = len(data["corridors"])
        except Exception as e:
            results["errors"].append(f"Corridor batch: {str(e)[:100]}")

        try:
            scored_tasks = [calculate_priority_score(task) for task in data["tasks"]]
            try:
                db.table("maintenance_tasks").upsert(
                    scored_tasks, on_conflict="task_id"
                ).execute()
            except Exception:
                legacy_tasks = [
                    {key: value for key, value in task.items()
                     if key not in {"score_breakdown", "priority_explanation"}}
                    for task in scored_tasks
                ]
                db.table("maintenance_tasks").upsert(
                    legacy_tasks, on_conflict="task_id"
                ).execute()
            results["tasks"] = len(scored_tasks)
        except Exception as e:
            results["errors"].append(f"Task batch: {str(e)[:100]}")

        for key, table_name in (
            ("trains", "train_schedule"),
            ("forecasts", "goods_forecast"),
            ("windows", "block_windows"),
        ):
            records = data[key]
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    db.table(table_name).insert(batch).execute()
                    results[key] += len(batch)
                except Exception as e:
                    results["errors"].append(f"{key} batch {i}: {str(e)[:100]}")

        return {
            "message": "Demo data loaded successfully",
            "results": results,
            "data_note": "SIMULATED_PROTOTYPE_DATA — Not real Indian Railways operational data",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-data")
async def clear_data(current_user: dict = Depends(get_current_user)):
    """Clear all data (admin only, prototype reset)"""
    if current_user.get("role") not in ("Admin",):
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        db = get_admin_db()
        db.table("block_tasks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("optimized_blocks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("optimization_runs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("maintenance_tasks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("train_schedule").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("goods_forecast").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("block_windows").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return {"message": "All data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/csv/tasks")
async def upload_tasks_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload maintenance tasks from CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Must be a CSV file")

    try:
        content = await file.read()
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

        required = ["task_id", "department", "task_type", "corridor_id", "duration_hours", "criticality"]
        rows = list(reader)

        if not rows:
            raise HTTPException(status_code=400, detail="Empty CSV file")

        # Validate headers
        headers = rows[0].keys()
        missing = [r for r in required if r not in headers]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing}"
            )

        db = get_admin_db()
        inserted = 0
        errors = []
        warnings = []
        seen_ids = set()
        corridor_result = db.table("corridors").select("corridor_id").execute()
        valid_corridors = {row["corridor_id"] for row in (corridor_result.data or [])}
        csv_ids = [row.get("task_id", "").strip() for row in rows if row.get("task_id")]
        existing_result = db.table("maintenance_tasks").select("task_id")
        if csv_ids:
            existing_result = existing_result.in_("task_id", csv_ids)
        existing_result = existing_result.execute()
        existing_ids = {row["task_id"] for row in (existing_result.data or [])}
        valid_departments = {"Engineering", "S&T", "Traction Distribution"}

        for row in rows:
            task_id = row.get("task_id", "").strip()
            try:
                if not task_id:
                    raise ValueError("missing task_id")
                if task_id in seen_ids:
                    warnings.append(f"Duplicate task_id {task_id} in CSV")
                    continue
                seen_ids.add(task_id)
                if task_id in existing_ids:
                    warnings.append(f"Task {task_id} already exists; row skipped")
                    continue
                if row["department"] not in valid_departments:
                    raise ValueError(f"invalid department: {row['department']}")
                if row["corridor_id"] not in valid_corridors:
                    raise ValueError(f"unknown corridor: {row['corridor_id']}")

                duration_hours = float(row["duration_hours"])
                if duration_hours <= 0:
                    raise ValueError("duration_hours must be positive")
                scores = {
                    "criticality": int(row["criticality"]),
                    "urgency": int(row.get("urgency", 3)),
                    "safety_risk": int(row.get("safety_risk", 3)),
                    "asset_importance": int(row.get("asset_importance", 3)),
                }
                if any(value < 1 or value > 5 for value in scores.values()):
                    raise ValueError("priority fields must be between 1 and 5")
                task = {
                    "task_id": task_id,
                    "department": row["department"],
                    "task_type": row["task_type"],
                    "asset_type": row.get("asset_type", "Unknown"),
                    "asset_name": row.get("asset_name", row["task_type"]),
                    "corridor_id": row["corridor_id"],
                    "location": row.get("location", ""),
                    "duration_hours": duration_hours,
                    **scores,
                    "due_date": row.get("due_date") or None,
                    "overdue": row.get("overdue", "false").lower() == "true",
                    "status": row.get("status", "Pending"),
                    "description": row.get("description", ""),
                }
                scored = calculate_priority_score(task)
                task_record = dict(scored)
                db.table("maintenance_tasks").insert(task_record).execute()
                inserted += 1
            except Exception as e:
                errors.append(f"Row {task_id or '?'}: {str(e)[:100]}")

        return {
            "message": f"Imported {inserted} of {len(rows)} tasks",
            "received": len(rows),
            "total": len(rows),
            "inserted": inserted,
            "imported": inserted,
            "rejected": len(rows) - inserted,
            "warnings": warnings,
            "warnings_count": len(warnings),
            "errors": errors[:10],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

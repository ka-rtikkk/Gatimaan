"""
Maintenance Tasks API
Endpoints for managing and viewing maintenance tasks from TMS/SMMS/TDMS
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from app.core.auth import get_current_user
from app.core.database import get_db, get_admin_db
from app.services.priority_engine import calculate_priority_score, calculate_priorities_bulk, get_priority_distribution
from app.services.synthetic_data import get_all_synthetic_data

router = APIRouter()


def _with_priority_details(task: dict) -> dict:
    if task.get("score_breakdown") and task.get("priority_explanation") and "final_planning_score" in task:
        return task
    scored = calculate_priority_score(task)
    return {
        **task,
        "score_breakdown": scored.get("score_breakdown"),
        "priority_explanation": scored.get("priority_explanation"),
    }


@router.get("")
async def get_tasks(
    department: Optional[str] = Query(None),
    corridor_id: Optional[str] = Query(None),
    priority_category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user),
):
    """Get all maintenance tasks with optional filters"""
    try:
        db = get_db()
        query = db.table("maintenance_tasks").select("*")

        if department:
            query = query.eq("department", department)
        if corridor_id:
            query = query.eq("corridor_id", corridor_id)
        if priority_category:
            query = query.eq("priority_category", priority_category)
        if status:
            query = query.eq("status", status)

        result = query.order("priority_score", desc=True).range(offset, offset + limit - 1).execute()
        tasks = [_with_priority_details(task) for task in (result.data or [])]

        return {
            "tasks": tasks,
            "total": len(tasks),
            "data_note": "SIMULATED_PROTOTYPE_DATA",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single task with full priority breakdown"""
    try:
        db = get_db()
        result = db.table("maintenance_tasks").select("*").eq("task_id", task_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found")
        return _with_priority_details(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-priorities")
async def calculate_priorities(current_user: dict = Depends(get_current_user)):
    """
    Recalculate priority scores for all tasks and update in database.
    Uses the explainable weighted priority scoring engine.
    """
    try:
        db = get_db()
        result = db.table("maintenance_tasks").select("*").execute()
        tasks = result.data or []

        if not tasks:
            return {"message": "No tasks found", "scored": 0}

        scored = calculate_priorities_bulk(tasks)

        # Persist all score updates in one request and report the outcome.
        admin_db = get_admin_db()
        failures = []
        try:
            score_records = [
                {key: value for key, value in task.items() if key not in {"id", "created_at"}}
                for task in scored
            ]
            try:
                admin_db.table("maintenance_tasks").upsert(
                    score_records, on_conflict="task_id"
                ).execute()
            except Exception:
                legacy_records = [
                    {key: value for key, value in task.items()
                     if key not in {"score_breakdown", "priority_explanation"}}
                    for task in scored
                ]
                admin_db.table("maintenance_tasks").upsert(
                    legacy_records, on_conflict="task_id"
                ).execute()
            updated = len(scored)
        except Exception as exc:
            updated = 0
            failures.append(f"bulk update: {str(exc)[:100]}")

        distribution = get_priority_distribution(scored)

        return {
            "message": "Priorities recalculated",
            "total_tasks": len(tasks),
            "updated": updated,
            "failed": len(failures),
            "errors": failures[:10],
            "distribution": distribution,
            "top_tasks": scored[:5],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def tasks_summary(current_user: dict = Depends(get_current_user)):
    """Get task statistics summary"""
    try:
        db = get_db()
        result = db.table("maintenance_tasks").select("*").execute()
        tasks = result.data or []

        total = len(tasks)
        by_status = {}
        by_dept = {}
        by_priority = {}

        for t in tasks:
            s = t.get("status", "Unknown")
            d = t.get("department", "Unknown")
            p = t.get("priority_category", "LOW")
            by_status[s] = by_status.get(s, 0) + 1
            by_dept[d] = by_dept.get(d, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1

        overdue_count = sum(1 for t in tasks if t.get("overdue"))

        return {
            "total": total,
            "overdue": overdue_count,
            "by_status": by_status,
            "by_department": by_dept,
            "by_priority": by_priority,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

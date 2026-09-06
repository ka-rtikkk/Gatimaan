"""Analytics API - Before vs After comparison"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Get analytics and impact metrics for the dashboard"""
    try:
        db = get_db()

        # Get optimization runs
        runs = db.table("optimization_runs").select("*").order(
            "created_at", desc=True
        ).limit(10).execute()

        # Get optimized blocks
        blocks = db.table("optimized_blocks").select("*").execute()
        blocks_data = blocks.data or []

        # Get tasks
        tasks = db.table("maintenance_tasks").select("*").execute()
        tasks_data = tasks.data or []

        # Compute analytics
        total_tasks = len(tasks_data)
        completed = sum(1 for t in tasks_data if t.get("status") == "Completed")
        overdue = sum(1 for t in tasks_data if t.get("overdue"))
        pending = sum(1 for t in tasks_data if t.get("status") == "Pending")
        scheduled = sum(1 for t in tasks_data if t.get("status") == "Scheduled")

        priority_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for t in tasks_data:
            cat = t.get("priority_category", "LOW") or "LOW"
            if cat in priority_dist:
                priority_dist[cat] += 1

        dept_dist = {}
        for t in tasks_data:
            d = t.get("department", "Unknown")
            dept_dist[d] = dept_dist.get(d, 0) + 1

        # Block stats
        total_blocks = len(blocks_data)
        total_block_hours = sum(b.get("duration_hours", 0) for b in blocks_data)
        multi_dept_blocks = sum(
            1 for b in blocks_data if len(b.get("departments_involved", [])) > 1
        )
        total_conflicts = sum(b.get("train_conflicts", 0) for b in blocks_data)

        # Compare only against the latest persisted independent baseline.
        latest_run = (runs.data or [None])[0]
        comparison = None
        if latest_run:
            comparison = {
                "baseline_block_hours": latest_run.get("baseline_block_hours"),
                "optimized_block_hours": latest_run.get("optimized_block_hours"),
                "improvement_percentage": latest_run.get("improvement_percentage"),
                "baseline_blocks": latest_run.get("baseline_blocks"),
                "optimized_blocks": latest_run.get("separate_blocks"),
                "baseline_tasks_scheduled": latest_run.get("baseline_tasks_scheduled"),
                "optimized_tasks_scheduled": latest_run.get("tasks_scheduled"),
                "baseline_conflicts": latest_run.get("baseline_conflicts"),
                "optimized_conflicts": latest_run.get("train_conflicts"),
                "note": "Computed from the latest generated plan and its independent departmental baseline.",
            }

        from datetime import date, timedelta
        today = date.today()
        weekly_trend = []
        for i in range(7):
            day = today - timedelta(days=6 - i)
            day_blocks = [b for b in blocks_data if str(b.get("date", "")) == str(day)]
            weekly_trend.append({
                "date": day.isoformat(),
                "day": day.strftime("%a"),
                "blocks": len(day_blocks),
                "hours": round(sum(b.get("duration_hours", 0) for b in day_blocks), 1),
                "tasks": sum(b.get("tasks_completed", 0) for b in day_blocks),
                "utilization": round(
                    sum(b.get("utilization", 0) for b in day_blocks) / len(day_blocks), 4
                ) if day_blocks and all(b.get("utilization") is not None for b in day_blocks) else None,
            })

        return {
            "summary": {
                "total_tasks": total_tasks,
                "completed": completed,
                "overdue": overdue,
                "pending": pending,
                "scheduled": scheduled,
                "total_blocks": total_blocks,
                "total_block_hours": round(total_block_hours, 1),
                "multi_dept_blocks": multi_dept_blocks,
                "total_conflicts": total_conflicts,
                "asset_availability": None,
                "asset_availability_note": "Not measurable: historical asset-state and operating-hour data are not in the prototype.",
            },
            "priority_distribution": priority_dist,
            "department_distribution": dept_dist,
            "comparison": comparison,
            "weekly_trend": weekly_trend,
            "recent_runs": runs.data or [],
            "data_note": "SIMULATED_PROTOTYPE_DATA",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corridors")
async def get_corridor_analytics(current_user: dict = Depends(get_current_user)):
    """Get per-corridor analytics"""
    try:
        db = get_db()
        corridors = db.table("corridors").select("*").execute()
        tasks = db.table("maintenance_tasks").select("*").execute()
        blocks = db.table("optimized_blocks").select("*").execute()

        corridor_data = []
        for c in (corridors.data or []):
            cid = c["corridor_id"]
            c_tasks = [t for t in (tasks.data or []) if t.get("corridor_id") == cid]
            c_blocks = [b for b in (blocks.data or []) if b.get("corridor_id") == cid]

            corridor_data.append({
                **c,
                "task_count": len(c_tasks),
                "overdue_tasks": sum(1 for t in c_tasks if t.get("overdue")),
                "critical_tasks": sum(1 for t in c_tasks if t.get("priority_category") == "CRITICAL"),
                "block_count": len(c_blocks),
                "block_hours": round(sum(b.get("duration_hours", 0) for b in c_blocks), 1),
            })

        return {"corridors": corridor_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

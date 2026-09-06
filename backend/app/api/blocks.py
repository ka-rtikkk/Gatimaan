"""
Block Planning API — Core optimization endpoints
POST /blocks/generate-plan  ← Hero endpoint
GET  /blocks/plans
GET  /blocks/plans/{id}
POST /blocks/simulate-scenario
POST /blocks/reschedule
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from time import perf_counter
import logging
import uuid

from app.core.auth import get_current_user
from app.core.database import get_db, get_admin_db
from app.services.priority_engine import calculate_priorities_bulk
from app.services.compatibility_engine import find_compatible_groups
from app.services.optimizer import (
    run_ortools_optimizer,
    generate_baseline_plan,
    compute_improvement_metrics,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class OptimizationResult(BaseModel):
    """Canonical response contract for every generated planning result."""
    run_id: str
    planning_horizon: str
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    baseline_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    improvement: Dict[str, Any] = Field(default_factory=dict)
    unscheduled_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    data_sources: Dict[str, Any] = Field(default_factory=dict)
    data_note: str


class GeneratePlanRequest(BaseModel):
    planning_horizon: str = "week"  # today | week | month
    corridor_id: Optional[str] = None
    force_demo: bool = False


class SimulateScenarioRequest(BaseModel):
    block_id: str
    scenario_type: str = "train_conflict"


@router.post("/generate-plan")
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    ============================================================
    HERO ENDPOINT — Gatimaan Optimization Pipeline
    ============================================================
    Step 1: Fetch pending maintenance tasks
    Step 2: Calculate priority scores (Priority Engine)
    Step 3: Fetch train schedule and block windows
    Step 4: Identify compatible task groups (Compatibility Engine)
    Step 5: Run OR-Tools CP-SAT optimization
    Step 6: Generate baseline comparison
    Step 7: Store results in Supabase
    Step 8: Return optimized plan
    """
    started_at = perf_counter()
    try:
        db = get_admin_db()

        # ── Step 1: Fetch tasks ──────────────────────────────────────
        tasks_query = db.table("maintenance_tasks").select("*").in_(
            "status", ["Pending", "Overdue", "Scheduled"]
        )
        if request.corridor_id:
            tasks_query = tasks_query.eq("corridor_id", request.corridor_id)

        tasks_result = tasks_query.execute()
        tasks = tasks_result.data or []
        logger.info("plan stage=maintenance_tasks count=%d", len(tasks))

        if not tasks:
            return OptimizationResult(
                run_id=str(uuid.uuid4()),
                planning_horizon=request.planning_horizon,
                metrics={"total_tasks": 0, "tasks_scheduled": 0},
                data_sources={"maintenance_tasks": {"count": 0}},
                data_note="SIMULATED_PROTOTYPE_DATA — No pending tasks found",
            ).model_dump()

        # ── Step 2: Priority scoring ─────────────────────────────────
        scored_tasks = calculate_priorities_bulk(tasks)
        logger.info("plan stage=priority_engine count=%d", len(scored_tasks))

        # Persist all score updates in one request to keep the demo responsive.
        score_records = [
            {
                key: value for key, value in task.items()
                if key not in {"id", "created_at"}
            }
            for task in scored_tasks
        ]
        try:
            db.table("maintenance_tasks").upsert(
                score_records, on_conflict="task_id"
            ).execute()
        except Exception:
            legacy_records = [
                {key: value for key, value in task.items()
                 if key not in {"score_breakdown", "priority_explanation"}}
                for task in scored_tasks
            ]
            try:
                db.table("maintenance_tasks").upsert(
                    legacy_records, on_conflict="task_id"
                ).execute()
            except Exception:
                logger.exception("plan stage=priority_persistence failed")

        # ── Step 3: Fetch train schedule and block windows ───────────
        trains_result = db.table("train_schedule").select("*").execute()
        train_schedule = trains_result.data or []
        forecasts_result = db.table("goods_forecast").select("*").execute()
        goods_forecasts = forecasts_result.data or []
        corridors_result = db.table("corridors").select("corridor_id").execute()
        corridor_count = len(corridors_result.data or [])

        windows_query = db.table("block_windows").select("*").eq("available", True)
        if request.corridor_id:
            windows_query = windows_query.eq("corridor_id", request.corridor_id)
        windows_result = windows_query.execute()
        block_windows = windows_result.data or []
        logger.info(
            "plan stage=source_data trains=%d goods_forecasts=%d block_windows=%d corridors=%d",
            len(train_schedule), len(goods_forecasts), len(block_windows), corridor_count,
        )

        # ── Step 4: Find compatible task groups ──────────────────────
        task_groups = find_compatible_groups(scored_tasks, block_windows)
        logger.info("plan stage=compatibility groups=%d", len(task_groups))

        # ── Step 5: Run OR-Tools optimization ────────────────────────
        optimized_blocks, opt_metrics = run_ortools_optimizer(
            task_groups=task_groups,
            block_windows=block_windows,
            train_schedule=train_schedule,
            planning_horizon=request.planning_horizon,
            goods_forecasts=goods_forecasts,
        )
        logger.info(
            "plan stage=optimizer blocks=%d tasks_scheduled=%d status=%s",
            len(optimized_blocks), opt_metrics.get("tasks_scheduled", 0),
            opt_metrics.get("solver_status", "unknown"),
        )

        # ── Step 6: Generate baseline (manual/decentralized) ─────────
        baseline_blocks, baseline_metrics = generate_baseline_plan(
            tasks=scored_tasks,
            block_windows=block_windows,
            train_schedule=train_schedule,
            goods_forecasts=goods_forecasts,
            planning_horizon=request.planning_horizon,
        )

        improvement = compute_improvement_metrics(
            baseline_metrics, opt_metrics, optimized_blocks, scored_tasks
        )

        scheduled_task_ids = {
            task_id
            for block in optimized_blocks
            for task_id in block.get("task_ids", [])
        }
        eligible_dates = {
            str(window.get("date")) for window in block_windows
            if window.get("available", True)
        }
        unscheduled_tasks = []
        for task in scored_tasks:
            if task.get("task_id") in scheduled_task_ids:
                continue
            has_corridor_window = any(
                window.get("corridor_id") == task.get("corridor_id")
                and str(window.get("date")) in eligible_dates
                and float(window.get("maximum_duration", 0) or 0) >= float(task.get("duration_hours", 0) or 0)
                for window in block_windows
            )
            unscheduled_tasks.append({
                "task_id": task.get("task_id"),
                "department": task.get("department"),
                "corridor_id": task.get("corridor_id"),
                "priority_category": task.get("priority_category"),
                "priority_score": task.get("priority_score"),
                "existing_priority_score": task.get("existing_priority_score", task.get("priority_score")),
                "ml_risk_probability": task.get("ml_risk_probability"),
                "final_planning_score": task.get("final_planning_score", task.get("priority_score")),
                "reason": (
                    "Not selected by optimizer because feasible capacity was allocated to higher-priority tasks"
                    if has_corridor_window else
                    "No compatible available maintenance window in the selected horizon"
                ),
            })

        # ── Step 7: Store results in Supabase ────────────────────────
        run_id = str(uuid.uuid4())
        run_data = {
            "id": run_id,
            "planning_horizon": request.planning_horizon,
            "total_tasks": opt_metrics.get("total_tasks", 0),
            "tasks_scheduled": opt_metrics.get("tasks_scheduled", 0),
            "total_block_hours": opt_metrics.get("total_block_hours", 0),
            "separate_blocks": opt_metrics.get("separate_blocks", 0),
            "train_conflicts": opt_metrics.get("train_conflicts", 0),
            "estimated_asset_availability": None,
            "baseline_block_hours": improvement.get("baseline_block_hours"),
            "optimized_block_hours": improvement.get("optimized_block_hours"),
            "improvement_percentage": improvement.get("improvement_percentage"),
            "average_utilization": opt_metrics.get("average_utilization", 0),
            "baseline_blocks": improvement.get("baseline_blocks", 0),
            "baseline_tasks_scheduled": improvement.get("baseline_tasks_scheduled", 0),
            "baseline_conflicts": improvement.get("baseline_conflicts", 0),
            "baseline_multi_department_blocks": improvement.get("baseline_multi_department_blocks", 0),
        }

        try:
            db.table("optimization_runs").insert(run_data).execute()
        except Exception:
            legacy_run_data = {
                key: value for key, value in run_data.items()
                if key not in {
                    "average_utilization", "baseline_blocks",
                    "baseline_tasks_scheduled", "baseline_conflicts",
                    "baseline_multi_department_blocks",
                }
            }
            try:
                db.table("optimization_runs").insert(legacy_run_data).execute()
            except Exception:
                logger.exception("plan stage=run_persistence failed")

        block_records = [{
            "block_id": block["block_id"],
            "corridor_id": block["corridor_id"],
            "date": block["date"],
            "start_time": block["start_time"],
            "end_time": block["end_time"],
            "duration_hours": block["duration_hours"],
            "optimization_score": block.get("optimization_score"),
            "train_conflicts": block.get("train_conflicts", 0),
            "tasks_completed": block.get("tasks_completed", 0),
            "departments_involved": block.get("departments_involved", []),
            "estimated_downtime": block.get("estimated_downtime"),
            "window_duration_hours": block.get("window_duration_hours"),
            "utilization": block.get("utilization"),
            "explanation": block.get("explanation"),
            "run_id": run_id,
        } for block in optimized_blocks]
        try:
            if block_records:
                try:
                    db.table("optimized_blocks").insert(block_records).execute()
                except Exception:
                    legacy_blocks = [
                        {key: value for key, value in block.items()
                         if key not in {"window_duration_hours", "utilization"}}
                        for block in block_records
                    ]
                    db.table("optimized_blocks").insert(legacy_blocks).execute()
            task_links = [
                {"block_id": block["block_id"], "task_id": task_id}
                for block in optimized_blocks
                for task_id in block.get("task_ids", [])
            ]
            if task_links:
                db.table("block_tasks").insert(task_links).execute()
                db.table("maintenance_tasks").update({"status": "Scheduled"}).in_(
                    "task_id", [link["task_id"] for link in task_links]
                ).execute()
        except Exception:
            logger.exception("plan stage=persistence failed; returning in-memory result")

        result = OptimizationResult(
            run_id=run_id,
            planning_horizon=request.planning_horizon,
            blocks=optimized_blocks,
            baseline_blocks=baseline_blocks,
            metrics=opt_metrics,
            improvement=improvement,
            unscheduled_tasks=unscheduled_tasks,
            data_sources={
                "maintenance_tasks": {"count": len(tasks), "kind": "synthetic_or_csv"},
                "train_schedule": {"count": len(train_schedule), "kind": "synthetic_coa_timetable"},
                "goods_forecast": {"count": len(goods_forecasts), "kind": "synthetic_forecast"},
                "block_windows": {"count": len(block_windows), "kind": "synthetic_corridor_availability"},
                "corridors": {"count": corridor_count, "kind": "synthetic_reference_data"},
            },
            data_note="SIMULATED_PROTOTYPE_DATA — No real TMS, SMMS, TDMS, or COA connection",
        )
        logger.info(
            "plan complete run_id=%s duration_seconds=%.3f blocks=%d tasks_scheduled=%d",
            run_id, perf_counter() - started_at, len(optimized_blocks),
            opt_metrics.get("tasks_scheduled", 0),
        )
        return result.model_dump()

    except Exception as e:
        logger.exception("plan failed duration_seconds=%.3f", perf_counter() - started_at)
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@router.get("/plans")
async def get_plans(
    limit: int = Query(20, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Get recent optimization runs"""
    try:
        db = get_db()
        runs = db.table("optimization_runs").select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()
        return {"runs": runs.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{run_id}")
async def get_plan(run_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific optimization run with its blocks"""
    try:
        db = get_db()
        run = db.table("optimization_runs").select("*").eq("id", run_id).execute()
        blocks = db.table("optimized_blocks").select("*").eq("run_id", run_id).execute()

        if not run.data:
            raise HTTPException(status_code=404, detail="Plan not found")

        return {
            "run": run.data[0],
            "blocks": blocks.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimized")
async def get_optimized_blocks(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    corridor_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get all optimized blocks for calendar/planner views"""
    try:
        db = get_db()
        query = db.table("optimized_blocks").select("*")
        if corridor_id:
            query = query.eq("corridor_id", corridor_id)
        if date_from:
            query = query.gte("date", date_from)
        if date_to:
            query = query.lte("date", date_to)

        result = query.order("date").order("start_time").execute()
        blocks = result.data or []

        window_result = db.table("block_windows").select(
            "corridor_id,date,start_time,maximum_duration"
        ).execute()
        window_durations = {
            (str(window.get("corridor_id")), str(window.get("date")), str(window.get("start_time"))): window.get("maximum_duration")
            for window in (window_result.data or [])
        }

        block_ids = [block["block_id"] for block in blocks]
        links_result = db.table("block_tasks").select("block_id,task_id").in_(
            "block_id", block_ids
        ).execute() if block_ids else None
        links = links_result.data or [] if links_result else []
        task_ids_by_block: Dict[str, List[str]] = {}
        for link in links:
            task_ids_by_block.setdefault(link["block_id"], []).append(link["task_id"])
        all_task_ids = [link["task_id"] for link in links]
        task_result = db.table("maintenance_tasks").select("*").in_(
            "task_id", all_task_ids
        ).execute() if all_task_ids else None
        tasks_by_id = {task["task_id"]: task for task in (task_result.data or [] if task_result else [])}

        # Enrich all blocks from the two batched relationship queries.
        enriched = []
        for block in blocks:
            task_ids = task_ids_by_block.get(block["block_id"], [])
            tasks = [tasks_by_id[task_id] for task_id in task_ids if task_id in tasks_by_id]

            departments = block.get("departments_involved") or []
            window_duration = block.get("window_duration_hours") or window_durations.get(
                (str(block.get("corridor_id")), str(block.get("date")), str(block.get("start_time")))
            )
            utilization = block.get("utilization")
            if utilization is None and window_duration:
                utilization = round(
                    min(1.0, float(block.get("duration_hours", 0) or 0) / float(window_duration)), 4
                )
            enriched.append({
                **block,
                "task_ids": task_ids,
                "tasks": tasks,
                "multi_department": len(departments) > 1,
                "has_critical": any(
                    task.get("priority_category") == "CRITICAL" for task in tasks
                ),
                "has_overdue": any(task.get("overdue", False) for task in tasks),
                "window_duration_hours": window_duration,
                "utilization": utilization,
            })

        return {"blocks": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate-scenario")
async def simulate_scenario(
    request: SimulateScenarioRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Simulate a conflict scenario.
    Introduces an unexpected train into a block and re-optimizes.
    """
    try:
        db = get_db()
        block_result = db.table("optimized_blocks").select("*").eq(
            "block_id", request.block_id
        ).execute()

        if not block_result.data:
            raise HTTPException(status_code=404, detail="Block not found")

        block = block_result.data[0]

        # Mark original block as conflicting
        db.table("optimized_blocks").update({
            "train_conflicts": (block.get("train_conflicts", 0) + 1),
            "explanation": block.get("explanation", "") + "\n\n[CONFLICT DETECTED: Unexpected train scheduled during this block]",
        }).eq("block_id", request.block_id).execute()

        # Find a later window for rescheduling
        corridor_id = block.get("corridor_id")
        block_date = block.get("date")

        windows = db.table("block_windows").select("*").eq(
            "corridor_id", corridor_id
        ).eq("date", block_date).eq("available", True).execute()

        alt_window = None
        for w in (windows.data or []):
            if w.get("start_time", "00:00") > block.get("end_time", "00:00"):
                if w.get("maximum_duration", 0) >= block.get("duration_hours", 1):
                    alt_window = w
                    break

        if not alt_window:
            # Use next day
            alt_window = {
                "start_time": "18:00:00",
                "end_time": "21:00:00",
                "date": block_date,
                "maximum_duration": 3.0,
            }

        # Generate rescheduled block
        from app.services.optimizer import generate_block_id
        new_block_id = generate_block_id()
        new_explanation = (
            f"RESCHEDULED by Gatimaan after conflict detection.\n"
            f"Original block {request.block_id} had an unexpected train conflict.\n"
            f"System automatically identified the next available window on same corridor.\n"
            f"All original tasks have been rescheduled to {alt_window['start_time'][:5]}–{alt_window['end_time'][:5]}.\n"
            f"\n[Simulated scenario — not real operational data]"
        )

        new_block = {
            "block_id": new_block_id,
            "corridor_id": corridor_id,
            "date": alt_window.get("date", block_date),
            "start_time": alt_window.get("start_time"),
            "end_time": alt_window.get("end_time"),
            "duration_hours": block.get("duration_hours"),
            "optimization_score": block.get("optimization_score", 80),
            "train_conflicts": 0,
            "tasks_completed": block.get("tasks_completed", 0),
            "departments_involved": block.get("departments_involved", []),
            "estimated_downtime": block.get("estimated_downtime"),
            "explanation": new_explanation,
        }

        try:
            db.table("optimized_blocks").insert(new_block).execute()
            task_links = db.table("block_tasks").select("task_id").eq(
                "block_id", request.block_id
            ).execute()
            for task_link in task_links.data or []:
                db.table("block_tasks").insert({
                    "block_id": new_block_id,
                    "task_id": task_link["task_id"],
                }).execute()
        except Exception:
            pass

        return {
            "original_block": block,
            "conflict_detected": True,
            "rescheduled_block": new_block,
            "message": f"Block rescheduled from {block.get('start_time', '')} to {alt_window.get('start_time', '')}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Type annotation fix
from typing import Optional

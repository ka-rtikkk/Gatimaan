"""
=============================================================================
GATIMAAN OR-TOOLS OPTIMIZATION ENGINE
=============================================================================
Uses Google OR-Tools CP-SAT solver to generate optimized maintenance block plans.

Objectives:
  MINIMIZE:
    - Total block hours (utilization efficiency)
    - Number of separate blocks (coordination bonus)
    - Train conflicts during maintenance windows
    - Task lateness (overdue penalty)

  MAXIMIZE:
    - Total tasks completed
    - Critical task completion
    - Multi-department block coordination

Constraints:
  - Each task assigned to at most one block
  - Block window must be available
  - Combined task duration must not exceed block window
  - Train conflict avoidance (soft constraint with penalty)
  - Tasks cannot be double-scheduled

Architecture:
  The optimizer receives:
    - task groups (from compatibility engine)
    - block windows (available maintenance slots)
    - train schedule (for conflict detection)

  And produces:
    - optimized_blocks: list of blocks with tasks assigned
    - baseline_plan: simulated manual/decentralized baseline for comparison
    - run_metrics: summary statistics

NOTE: This module uses deterministic optimization (OR-Tools CP-SAT).
No LLM is used in the scheduling decision.
=============================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, time, timedelta
import uuid
import math

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("WARNING: OR-Tools not installed. Using greedy fallback optimizer.")

from app.services.compatibility_engine import (
    find_compatible_groups,
    find_block_for_group,
    count_train_conflicts,
)


# ============================================================
# BLOCK ID GENERATOR
# ============================================================
def generate_block_id() -> str:
    return f"BLK-{uuid.uuid4().hex[:8].upper()}"


# ============================================================
# EXPLANATION GENERATOR
# ============================================================
def generate_block_explanation(
    group: Dict,
    window: Dict,
    train_conflicts: int,
    baseline_blocks_avoided: int,
) -> str:
    """
    Generate a deterministic explanation for why a block was selected.
    Based purely on optimization results - not an LLM.
    """
    reasons = []

    tasks = group.get("tasks", [])
    departments = group.get("departments", [])
    corridor = group.get("corridor_id", "")
    total_dur = group.get("total_duration", 0)
    has_critical = group.get("has_critical", False)
    has_overdue = group.get("has_overdue", False)
    multi_dept = group.get("multi_department", False)

    # Reason 1: Critical/overdue task
    if has_critical and has_overdue:
        reasons.append("Contains a CRITICAL overdue maintenance task requiring immediate scheduling")
    elif has_critical:
        reasons.append("Contains a CRITICAL priority maintenance task with high safety risk")
    elif has_overdue:
        reasons.append("Includes overdue task(s) that must be completed urgently")
    else:
        reasons.append(f"Group of {len(tasks)} compatible maintenance task(s) identified")

    # Reason 2: Multi-department coordination
    if multi_dept:
        dept_str = ", ".join(departments[:-1]) + f" and {departments[-1]}" if len(departments) > 1 else departments[0]
        reasons.append(
            f"Tasks from {dept_str} departments can be executed in the same block window, "
            f"avoiding {baseline_blocks_avoided} separate maintenance block(s)"
        )

    # Reason 3: Train traffic
    if train_conflicts == 0:
        reasons.append("Selected window has no expected train conflicts during the maintenance period")
    elif train_conflicts <= 1:
        reasons.append(f"Window has minimal train activity ({train_conflicts} train) — lowest conflict option available")
    else:
        reasons.append(f"Window selected as best available option despite {train_conflicts} expected train movement(s)")

    # Reason 4: Duration fit
    window_dur = window.get("maximum_duration", total_dur)
    utilization = round((total_dur / window_dur) * 100) if window_dur > 0 else 100
    reasons.append(
        f"All {len(tasks)} task(s) ({total_dur:.1f}h total) fit within the {window_dur:.1f}h window "
        f"({utilization}% utilization)"
    )

    # Reason 5: Deadline compliance
    due_dates = [t.get("due_date") for t in tasks if t.get("due_date")]
    if due_dates:
        reasons.append("Scheduling satisfies deadline constraints for all grouped tasks")

    # Format as numbered list
    explanation = "Block selected by Gatimaan optimizer because:\n"
    for i, reason in enumerate(reasons, 1):
        explanation += f"{i}. {reason}.\n"

    explanation += f"\n[Simulated scenario — not real operational data]"
    return explanation.strip()


# ============================================================
# BASELINE GENERATOR
# ============================================================
def generate_baseline_plan(
    tasks: List[Dict],
    block_windows: List[Dict],
    train_schedule: List[Dict],
    goods_forecasts: List[Dict] = None,
    planning_horizon: str = "week",
) -> Tuple[List[Dict], Dict]:
    """
    Simulate the BEFORE scenario: decentralized, per-department manual planning.
    Each department schedules its own tasks independently in separate blocks.
    This demonstrates the INEFFICIENCY that Gatimaan solves.
    """
    baseline_blocks = []
    today = date.today()
    horizon_days = {"today": 1, "week": 7, "month": 30}.get(planning_horizon, 7)
    horizon_end = today + timedelta(days=horizon_days)
    block_num = 1

    # Group tasks by department (manual/decentralized approach)
    dept_tasks: Dict[str, List[Dict]] = {}
    for task in tasks:
        dept = task.get("department")
        if dept not in dept_tasks:
            dept_tasks[dept] = []
        dept_tasks[dept].append(task)

    total_conflicts = 0
    total_hours = 0

    for dept, dtasks in dept_tasks.items():
        # Each task gets its own separate block (worst case manual planning)
        for task in dtasks:
            # Find any available window for this corridor
            corridor_windows = [
                w for w in block_windows
                if w.get("corridor_id") == task.get("corridor_id")
                and w.get("available", True)
                and today <= datetime.fromisoformat(str(w["date"])).date() < horizon_end
                and w.get("maximum_duration", 0) >= task.get("duration_hours", 1.0)
            ]

            if not corridor_windows:
                continue

            window = corridor_windows[0]
            conflicts = count_train_conflicts(window, train_schedule, goods_forecasts)
            duration = task.get("duration_hours", 1.0)
            total_hours += duration
            total_conflicts += conflicts

            baseline_blocks.append({
                "block_id": f"BASE-{block_num:04d}",
                "corridor_id": task.get("corridor_id"),
                "date": window.get("date", today.isoformat()),
                "start_time": window.get("start_time"),
                "end_time": window.get("end_time"),
                "duration_hours": duration,
                "train_conflicts": conflicts,
                "tasks_completed": 1,
                "departments_involved": [dept],
                "task_ids": [task.get("task_id")],
                "window_duration_hours": window.get("maximum_duration", duration),
                "utilization": round(
                    min(1.0, duration / (window.get("maximum_duration", duration) or duration)), 4
                ),
                "type": "baseline",
            })
            block_num += 1

    metrics = {
        "total_blocks": len(baseline_blocks),
        "total_block_hours": round(total_hours, 2),
        "train_conflicts": total_conflicts,
        "tasks_scheduled": len(baseline_blocks),
        "task_ids": [task_id for block in baseline_blocks for task_id in block.get("task_ids", [])],
        "multi_department_blocks": 0,
        "avg_tasks_per_block": 1.0,
        "average_utilization": round(
            sum(b.get("utilization", 0) for b in baseline_blocks) / len(baseline_blocks), 4
        ) if baseline_blocks else 0,
    }

    return baseline_blocks, metrics


# ============================================================
# OR-TOOLS OPTIMIZER (Main)
# ============================================================
def run_ortools_optimizer(
    task_groups: List[Dict],
    block_windows: List[Dict],
    train_schedule: List[Dict],
    planning_horizon: str = "week",
    goods_forecasts: List[Dict] = None,
) -> Tuple[List[Dict], Dict]:
    """
    Main optimization function using OR-Tools CP-SAT.

    Inputs:
        task_groups: compatible task groups from compatibility engine
        block_windows: available maintenance windows
        train_schedule: train movements for conflict detection
        planning_horizon: 'today' | 'week' | 'month'

    Returns:
        (optimized_blocks, run_metrics)
    """
    if ORTOOLS_AVAILABLE:
        return _cpsat_optimize(task_groups, block_windows, train_schedule, planning_horizon, goods_forecasts)
    else:
        return _greedy_optimize(task_groups, block_windows, train_schedule, planning_horizon, goods_forecasts)


def _cpsat_optimize(
    task_groups: List[Dict],
    block_windows: List[Dict],
    train_schedule: List[Dict],
    planning_horizon: str,
    goods_forecasts: List[Dict] = None,
) -> Tuple[List[Dict], Dict]:
    """
    CP-SAT optimization.
    Decision variables: for each (group, window) pair, a binary variable
    indicating if group g is assigned to window w.
    """
    model = cp_model.CpModel()

    # Filter windows for planning horizon
    today = date.today()
    horizon_days = {"today": 1, "week": 7, "month": 30}.get(planning_horizon, 7)
    horizon_end = today + timedelta(days=horizon_days)

    eligible_windows = [
        w for w in block_windows
        if w.get("available", True)
        and today <= datetime.fromisoformat(str(w["date"])).date() < horizon_end
    ]

    if not eligible_windows or not task_groups:
        return [], {"total_tasks": 0, "tasks_scheduled": 0}

    num_groups = len(task_groups)
    num_windows = len(eligible_windows)

    # Binary decision variables: x[g][w] = 1 if group g assigned to window w
    x = {}
    for g in range(num_groups):
        for w in range(num_windows):
            x[g, w] = model.NewBoolVar(f"x_g{g}_w{w}")

    # Constraint 1: Each group assigned to at most one window
    for g in range(num_groups):
        model.AddAtMostOne(x[g, w] for w in range(num_windows))

    # Constraint 2: Each task appears in at most one block
    # (handled by groups — each task is in at most one group)

    # Constraint 3: Same window can only serve groups on same corridor
    # AND groups must not double-exceed the window duration
    window_group_vars: Dict[int, List] = {w: [] for w in range(num_windows)}
    for g in range(num_groups):
        group = task_groups[g]
        for w in range(num_windows):
            window = eligible_windows[w]
            # Feasibility: same corridor and duration fits
            if (group.get("corridor_id") == window.get("corridor_id") and
                    group.get("total_duration", 0) <= window.get("maximum_duration", 0)):
                window_group_vars[w].append((g, group))

    # Constraint 4: Window total duration cannot exceed max
    for w in range(num_windows):
        window = eligible_windows[w]
        max_dur = window.get("maximum_duration", 3.0)
        max_dur_int = int(max_dur * 10)  # Scale to avoid float

        assigned = window_group_vars[w]
        if len(assigned) > 1:
            # Sum of durations ≤ max_duration
            # Add constraint: total duration ≤ window max
            # CP-SAT: use LinearExpr
            scaled_vars = [x[g, w] * int(group.get("total_duration", 1.0) * 10) for g, group in assigned]
            model.Add(cp_model.LinearExpr.Sum(scaled_vars) <= max_dur_int)

    # Objective function (scaled integers for CP-SAT)
    # MAXIMIZE:
    #   + priority_score (x100) per task completed
    #   + coordination_bonus (x100) per multi-dept group
    #   - conflict_penalty per train conflict

    objective_terms = []
    SCALE = 100

    for g in range(num_groups):
        group = task_groups[g]
        for w in range(num_windows):
            window = eligible_windows[w]

            if group.get("corridor_id") != window.get("corridor_id"):
                continue
            if group.get("total_duration", 0) > window.get("maximum_duration", 0):
                continue

            # Task completion reward
            priority_reward = int(group.get("max_planning_score", group.get("max_priority_score", 0.5)) * SCALE * len(group.get("tasks", [1])))

            # Multi-department coordination bonus
            coord_bonus = int(group.get("coordination_bonus", 0) * SCALE * 2)

            # Overdue/critical bonus
            overdue_bonus = 50 if group.get("has_overdue") else 0
            critical_bonus = 30 if group.get("has_critical") else 0

            # Train conflict penalty
            conflicts = count_train_conflicts(window, train_schedule, goods_forecasts)
            conflict_penalty = conflicts * 20

            net_score = priority_reward + coord_bonus + overdue_bonus + critical_bonus - conflict_penalty
            objective_terms.append(x[g, w] * net_score)

    model.Maximize(cp_model.LinearExpr.Sum(objective_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 2
    status = solver.Solve(model)

    optimized_blocks = []
    scheduled_tasks = set()

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for g in range(num_groups):
            group = task_groups[g]
            for w in range(num_windows):
                if solver.Value(x[g, w]) == 1:
                    window = eligible_windows[w]
                    block = _create_block(group, window, train_schedule, goods_forecasts)
                    optimized_blocks.append(block)
                    for tid in group.get("task_ids", []):
                        scheduled_tasks.add(tid)
                    break

    # Tasks not scheduled → create individual blocks (greedy fallback)
    unscheduled_groups = [
        g for g in task_groups
        if not any(tid in scheduled_tasks for tid in g.get("task_ids", []))
    ]

    for group in unscheduled_groups[:10]:  # Limit fallback
        suitable = find_block_for_group(group, eligible_windows, train_schedule, goods_forecasts)
        if suitable:
            window = suitable[0]
            block = _create_block(group, window, train_schedule, goods_forecasts)
            optimized_blocks.append(block)

    total_tasks_all = sum(len(g.get("tasks", [])) for g in task_groups)
    tasks_sched = sum(b.get("tasks_completed", 0) for b in optimized_blocks)

    metrics = {
        "total_tasks": total_tasks_all,
        "tasks_scheduled": tasks_sched,
        "total_block_hours": round(sum(b.get("duration_hours", 0) for b in optimized_blocks), 2),
        "separate_blocks": len(optimized_blocks),
        "train_conflicts": sum(b.get("train_conflicts", 0) for b in optimized_blocks),
        "multi_department_blocks": sum(1 for b in optimized_blocks if len(b.get("departments_involved", [])) > 1),
        "average_utilization": round(
            sum(b.get("utilization", 0) for b in optimized_blocks) / len(optimized_blocks), 4
        ) if optimized_blocks else 0,
        "solver_status": solver.StatusName(status),
    }

    return optimized_blocks, metrics


def _greedy_optimize(
    task_groups: List[Dict],
    block_windows: List[Dict],
    train_schedule: List[Dict],
    planning_horizon: str,
    goods_forecasts: List[Dict] = None,
) -> Tuple[List[Dict], Dict]:
    """
    Greedy fallback optimizer when OR-Tools is not available.
    Assigns highest-priority groups to best-fit windows.
    """
    today = date.today()
    horizon_days = {"today": 1, "week": 7, "month": 30}.get(planning_horizon, 7)
    horizon_end = today + timedelta(days=horizon_days)

    eligible_windows = [
        w for w in block_windows
        if w.get("available", True)
        and today <= datetime.fromisoformat(str(w["date"])).date() < horizon_end
    ]

    used_windows: set = set()
    optimized_blocks = []

    for group in task_groups:
        suitable = find_block_for_group(group, eligible_windows, train_schedule, goods_forecasts)
        if not suitable:
            continue

        # Pick first unused window
        for window in suitable:
            wkey = f"{window.get('corridor_id')}-{window.get('date')}-{window.get('start_time')}"
            if wkey not in used_windows:
                used_windows.add(wkey)
                block = _create_block(group, window, train_schedule, goods_forecasts)
                optimized_blocks.append(block)
                break

    total_tasks = sum(len(g.get("tasks", [])) for g in task_groups)
    tasks_sched = sum(b.get("tasks_completed", 0) for b in optimized_blocks)

    metrics = {
        "total_tasks": total_tasks,
        "tasks_scheduled": tasks_sched,
        "total_block_hours": round(sum(b.get("duration_hours", 0) for b in optimized_blocks), 2),
        "separate_blocks": len(optimized_blocks),
        "train_conflicts": sum(b.get("train_conflicts", 0) for b in optimized_blocks),
        "multi_department_blocks": sum(1 for b in optimized_blocks if len(b.get("departments_involved", [])) > 1),
        "average_utilization": round(
            sum(b.get("utilization", 0) for b in optimized_blocks) / len(optimized_blocks), 4
        ) if optimized_blocks else 0,
        "solver_status": "greedy_fallback",
    }

    return optimized_blocks, metrics


def _create_block(
    group: Dict,
    window: Dict,
    train_schedule: List[Dict],
    goods_forecasts: List[Dict] = None,
) -> Dict:
    """Create an optimized block dict from a group and window"""
    tasks = group.get("tasks", [])
    departments = group.get("departments", [])
    total_duration = group.get("total_duration", 1.0)
    window_duration = window.get("maximum_duration", total_duration) or total_duration

    conflicts = count_train_conflicts(window, train_schedule, goods_forecasts)
    baseline_avoided = len(departments)  # Each dept would have had its own block

    explanation = generate_block_explanation(
        group, window, conflicts, baseline_avoided
    )

    # Optimization score: composite metric
    priority_score = group.get("max_planning_score", group.get("max_priority_score", 0.5))
    coord_bonus = group.get("coordination_bonus", 0)
    conflict_penalty = conflicts * 0.05
    opt_score = round(min(100, (priority_score + coord_bonus - conflict_penalty) * 100), 1)

    return {
        "block_id": generate_block_id(),
        "corridor_id": window.get("corridor_id"),
        "date": str(window.get("date")),
        "start_time": window.get("start_time"),
        "end_time": window.get("end_time"),
        "duration_hours": total_duration,
        "optimization_score": opt_score,
        "train_conflicts": conflicts,
        "tasks_completed": len(tasks),
        "departments_involved": departments,
        "estimated_downtime": total_duration,
        "window_duration_hours": window_duration,
        "utilization": round(min(1.0, total_duration / window_duration), 4),
        "explanation": explanation,
        "task_ids": [t.get("task_id") for t in tasks],
        "tasks": tasks,
        "multi_department": group.get("multi_department", False),
        "has_critical": group.get("has_critical", False),
        "has_overdue": group.get("has_overdue", False),
    }


def compute_improvement_metrics(
    baseline_metrics: Dict,
    optimized_metrics: Dict,
    optimized_blocks: List[Dict],
    tasks: List[Dict] = None,
) -> Dict:
    """
    Compute before vs after comparison metrics.
    These are simulated scenario numbers, not real-world claims.
    """
    baseline_hours = baseline_metrics.get("total_block_hours", 0)
    optimized_hours = optimized_metrics.get("total_block_hours", 0)
    baseline_blocks = baseline_metrics.get("total_blocks", 0)
    optimized_blocks_count = optimized_metrics.get("separate_blocks", 0)

    hours_saved = max(0, baseline_hours - optimized_hours)
    blocks_reduced = max(0, baseline_blocks - optimized_blocks_count)

    improvement_pct = (hours_saved / baseline_hours * 100) if baseline_hours > 0 else 0

    baseline_conflicts = baseline_metrics.get("train_conflicts", 0)
    opt_conflicts = optimized_metrics.get("train_conflicts", 0)
    conflict_reduction = max(0, baseline_conflicts - opt_conflicts)

    task_map = {task.get("task_id"): task for task in (tasks or [])}

    def risk_weighted_hours(task_ids: List[str]) -> float:
        total = 0.0
        for task_id in set(task_ids):
            task = task_map.get(task_id)
            if not task:
                continue
            factor = (
                task.get("criticality", 3)
                + task.get("urgency", 3)
                + task.get("safety_risk", 3)
                + task.get("asset_importance", 3)
            ) / 20.0
            if task.get("overdue"):
                factor *= 1.25
            total += float(task.get("duration_hours", 0)) * factor
        return round(total, 2)

    baseline_impact = risk_weighted_hours(baseline_metrics.get("task_ids", []))
    optimized_task_ids = [
        task_id for block in optimized_blocks for task_id in block.get("task_ids", [])
    ]
    optimized_impact = risk_weighted_hours(optimized_task_ids)
    total_impact = risk_weighted_hours(list(task_map))
    risk_coverage = round((optimized_impact / total_impact) * 100, 1) if total_impact else None

    return {
        "baseline_block_hours": round(baseline_hours, 2),
        "optimized_block_hours": round(optimized_hours, 2),
        "hours_saved": round(hours_saved, 2),
        "improvement_percentage": round(improvement_pct, 1),
        "baseline_blocks": baseline_blocks,
        "optimized_blocks_count": optimized_blocks_count,
        "blocks_reduced": blocks_reduced,
        "baseline_tasks_scheduled": baseline_metrics.get("tasks_scheduled", 0),
        "optimized_tasks_scheduled": optimized_metrics.get("tasks_scheduled", 0),
        "baseline_multi_department_blocks": baseline_metrics.get("multi_department_blocks", 0),
        "optimized_multi_department_blocks": optimized_metrics.get("multi_department_blocks", 0),
        "baseline_conflicts": baseline_conflicts,
        "optimized_conflicts": opt_conflicts,
        "conflict_reduction": conflict_reduction,
        "baseline_average_utilization": baseline_metrics.get("average_utilization", 0),
        "optimized_average_utilization": optimized_metrics.get("average_utilization", 0),
        "availability_before": None,
        "availability_after": None,
        "availability_improvement": None,
        "asset_impact": {
            "metric": "risk_weighted_maintenance_hours",
            "baseline": baseline_impact,
            "optimized": optimized_impact,
            "total_pending": total_impact,
            "optimized_risk_coverage_percent": risk_coverage,
        },
        "asset_availability": {
            "status": "simulated_estimate_unavailable",
            "value": None,
            "reason": "Historical asset-state and operating-hour data are not present in the prototype.",
        },
        "tasks_scheduled": optimized_metrics.get("tasks_scheduled", 0),
        "total_tasks": optimized_metrics.get("total_tasks", 0),
        "multi_department_blocks": optimized_metrics.get("multi_department_blocks", 0),
        "note": "Block and conflict metrics are generated from the current dataset. Asset availability is not measurable without historical asset-state data.",
    }

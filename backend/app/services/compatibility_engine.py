"""
=============================================================================
GATIMAAN COMPATIBILITY ENGINE
=============================================================================
Determines which maintenance tasks can be grouped into the same block.

Compatibility rules:
1. Tasks must be on the same corridor
2. Tasks from different departments are preferred (cross-dept coordination)
3. Combined duration must fit within an available block window
4. Departments must be mutually compatible
5. Safety constraints (some tasks cannot run simultaneously)
6. Location overlap (tasks at nearby km ranges can share same block)

This engine identifies candidate groups BEFORE the OR-Tools optimizer
selects the final schedule. The optimizer uses these groups as input.
=============================================================================
"""

from typing import List, Dict, Set, Tuple, Any
from itertools import combinations
import math


# Safety rules: certain task types CANNOT be combined in same block
# (would be unsafe or operationally impossible simultaneously)
INCOMPATIBLE_TASK_PAIRS = {
    ("Rail Fracture Repair", "Welding / Thermit Weld Repair"),  # Same type of rail work
    ("Track Geometry Correction", "Rail Replacement"),  # Conflicting track work
    ("OHE Wire Replacement", "OHE Inspection (Scheduled)"),  # Both need OHE down
    ("Pantograph Damage Repair", "OHE Wire Replacement"),  # Same OHE section
    ("Interlocking Check", "Point Machine Overhaul"),  # Same signalling system
}

# Maximum tasks in a single block (practical limit)
MAX_TASKS_PER_BLOCK = 5

# Maximum combined duration that can be in one block (hours)
MAX_BLOCK_DURATION = 6.0

# Minimum location distance (km) for tasks to be considered co-located
# Tasks within this range can be in the same block
CO_LOCATION_RADIUS_KM = 15.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points"""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def are_tasks_location_compatible(task1: Dict, task2: Dict) -> bool:
    """Check if two tasks are close enough to be in the same block"""
    # Same corridor is required
    if task1.get("corridor_id") != task2.get("corridor_id"):
        return False

    lat1, lon1 = task1.get("latitude"), task1.get("longitude")
    lat2, lon2 = task2.get("latitude"), task2.get("longitude")

    # If no coordinates, assume same corridor = compatible location
    if not all([lat1, lon1, lat2, lon2]):
        return True

    try:
        dist = haversine_distance(float(lat1), float(lon1), float(lat2), float(lon2))
        return dist <= CO_LOCATION_RADIUS_KM
    except (ValueError, TypeError):
        return True


def are_tasks_type_compatible(task1: Dict, task2: Dict) -> bool:
    """Check that task types are not in the incompatible pairs list"""
    type1 = task1.get("task_type", "")
    type2 = task2.get("task_type", "")

    pair = (type1, type2)
    pair_rev = (type2, type1)

    return pair not in INCOMPATIBLE_TASK_PAIRS and pair_rev not in INCOMPATIBLE_TASK_PAIRS


def are_departments_compatible(task1: Dict, task2: Dict) -> bool:
    """Check if departments can work together in the same block"""
    dept1 = task1.get("department")
    dept2 = task2.get("department")

    if dept1 == dept2:
        # Same department tasks can always be in same block
        return True

    # Check compatible_departments field
    compat1 = task1.get("compatible_departments", []) or []
    compat2 = task2.get("compatible_departments", []) or []

    # If either task lists the other's dept as compatible
    if dept2 in compat1 or dept1 in compat2:
        return True

    # By default, cross-department tasks on same corridor are compatible
    # (the optimizer prefers multi-dept blocks for coordination bonus)
    return True


def are_tasks_compatible(task1: Dict, task2: Dict) -> bool:
    """
    Full compatibility check between two tasks.
    Returns True if both tasks CAN be placed in the same block.
    """
    # Must be same corridor
    if task1.get("corridor_id") != task2.get("corridor_id"):
        return False

    # Must not be same task
    if task1.get("task_id") == task2.get("task_id"):
        return False

    # Location check
    if not are_tasks_location_compatible(task1, task2):
        return False

    # Task type safety check
    if not are_tasks_type_compatible(task1, task2):
        return False

    # Department compatibility
    if not are_departments_compatible(task1, task2):
        return False

    return True


def find_compatible_groups(
    tasks: List[Dict],
    block_windows: List[Dict] = None,
) -> List[Dict]:
    """
    Find all groups of tasks that can potentially share a maintenance block.

    Returns a list of compatibility groups, each containing:
    - tasks: list of compatible task dicts
    - corridor_id: corridor
    - total_duration: combined task duration
    - departments: set of departments
    - compatibility_score: preference score for this grouping
    """
    groups = []

    # Group tasks by corridor first
    corridor_tasks: Dict[str, List[Dict]] = {}
    for task in tasks:
        cid = task.get("corridor_id")
        if cid not in corridor_tasks:
            corridor_tasks[cid] = []
        corridor_tasks[cid].append(task)

    for corridor_id, ctasks in corridor_tasks.items():
        if len(ctasks) < 2:
            # Single task: add as its own group
            if ctasks:
                groups.append(_make_single_task_group(ctasks[0]))
            continue

        corridor_max_duration = MAX_BLOCK_DURATION
        if block_windows:
            corridor_durations = [
                float(window.get("maximum_duration", 3.0))
                for window in block_windows
                if window.get("corridor_id") == corridor_id
                and window.get("available", True)
            ]
            if corridor_durations:
                corridor_max_duration = min(MAX_BLOCK_DURATION, max(corridor_durations))

        # Find all compatible pairs and larger groups
        visited_task_ids: Set[str] = set()

        # Build compatibility adjacency list
        adj: Dict[str, Set[str]] = {t["task_id"]: set() for t in ctasks}
        for t1, t2 in combinations(ctasks, 2):
            if are_tasks_compatible(t1, t2):
                adj[t1["task_id"]].add(t2["task_id"])
                adj[t2["task_id"]].add(t1["task_id"])

        # Greedy grouping: start with highest-priority task, add compatible tasks
        task_map = {t["task_id"]: t for t in ctasks}
        sorted_tasks = sorted(
            ctasks,
            key=lambda t: t.get("priority_score", 0),
            reverse=True,
        )

        for seed_task in sorted_tasks:
            tid = seed_task["task_id"]
            if tid in visited_task_ids:
                continue

            group_tasks = [seed_task]
            visited_task_ids.add(tid)
            total_duration = seed_task.get("duration_hours", 1.0)

            # Try to add compatible tasks to this group
            candidates = sorted(
                [task_map[n] for n in adj[tid] if n not in visited_task_ids],
                key=lambda t: t.get("priority_score", 0),
                reverse=True,
            )

            for candidate in candidates:
                cand_id = candidate["task_id"]
                if cand_id in visited_task_ids:
                    continue

                # Check candidate is compatible with ALL tasks in group
                if not all(are_tasks_compatible(candidate, gt) for gt in group_tasks):
                    continue

                # Check combined duration fits
                cand_duration = candidate.get("duration_hours", 1.0)
                if total_duration + cand_duration > corridor_max_duration:
                    continue

                # Check max tasks limit
                if len(group_tasks) >= MAX_TASKS_PER_BLOCK:
                    break

                group_tasks.append(candidate)
                visited_task_ids.add(cand_id)
                total_duration += cand_duration

            if len(group_tasks) == 1:
                groups.append(_make_single_task_group(seed_task))
            else:
                groups.append(_make_group(group_tasks, corridor_id, total_duration))

    # Sort groups by compatibility score (highest priority groups first)
    groups.sort(key=lambda g: g["compatibility_score"], reverse=True)
    return groups


def _make_single_task_group(task: Dict) -> Dict:
    """Create a group containing only one task"""
    return {
        "tasks": [task],
        "task_ids": [task["task_id"]],
        "corridor_id": task.get("corridor_id"),
        "total_duration": task.get("duration_hours", 1.0),
        "departments": list(set([task.get("department")])),
        "multi_department": False,
        "compatibility_score": task.get("priority_score", 0.5),
        "max_priority_score": task.get("priority_score", 0.5),
        "max_planning_score": task.get("final_planning_score", task.get("priority_score", 0.5)),
        "has_critical": task.get("priority_category") == "CRITICAL",
        "has_overdue": task.get("overdue", False),
        "coordination_bonus": 0.0,
    }


def _make_group(tasks: List[Dict], corridor_id: str, total_duration: float) -> Dict:
    """Create a group from multiple compatible tasks"""
    departments = list(set(t.get("department") for t in tasks))
    multi_dept = len(departments) > 1

    max_priority = max(t.get("priority_score", 0) for t in tasks)
    max_planning = max(t.get("final_planning_score", t.get("priority_score", 0)) for t in tasks)
    avg_priority = sum(t.get("priority_score", 0) for t in tasks) / len(tasks)
    has_critical = any(t.get("priority_category") == "CRITICAL" for t in tasks)
    has_overdue = any(t.get("overdue", False) for t in tasks)

    # Multi-department coordination bonus
    coord_bonus = 0.1 * (len(departments) - 1)  # +0.1 per extra department

    # Compatibility score combines priority + coordination bonus
    compatibility_score = min(1.0, avg_priority + coord_bonus)

    return {
        "tasks": tasks,
        "task_ids": [t["task_id"] for t in tasks],
        "corridor_id": corridor_id,
        "total_duration": total_duration,
        "departments": departments,
        "multi_department": multi_dept,
        "compatibility_score": compatibility_score,
        "max_priority_score": max_priority,
        "max_planning_score": max_planning,
        "has_critical": has_critical,
        "has_overdue": has_overdue,
        "coordination_bonus": coord_bonus,
        "num_tasks": len(tasks),
    }


def find_block_for_group(
    group: Dict,
    block_windows: List[Dict],
    train_schedule: List[Dict],
    goods_forecasts: List[Dict] = None,
) -> List[Dict]:
    """
    Find suitable block windows for a task group.
    Returns windows sorted by suitability (fewest conflicts, best fit).
    """
    corridor_id = group["corridor_id"]
    required_duration = group["total_duration"]

    suitable = []
    for window in block_windows:
        if window.get("corridor_id") != corridor_id:
            continue
        if not window.get("available", True):
            continue

        max_dur = window.get("maximum_duration", 3.0)
        if max_dur < required_duration:
            continue

        # Count train conflicts in this window
        conflicts = count_train_conflicts(window, train_schedule, goods_forecasts)

        suitable.append({
            **window,
            "train_conflicts": conflicts,
            "fit_score": max_dur / required_duration,  # 1.0 = perfect fit
        })

    # Sort: fewest conflicts first, then best fit
    suitable.sort(key=lambda w: (w["train_conflicts"], -w["fit_score"]))
    return suitable


def _time_to_minutes(value: str) -> int:
    """Parse HH:MM[:SS] without losing minute-level precision."""
    parts = str(value or "00:00").split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _interval_overlaps(
    window_start: int,
    window_end: int,
    event_start: int,
    event_end: int,
) -> bool:
    """Check overlap for intervals that may cross midnight."""
    if window_end <= window_start:
        window_end += 24 * 60
    if event_end <= event_start:
        event_end += 24 * 60

    for shifted_start, shifted_end in (
        (event_start, event_end),
        (event_start + 24 * 60, event_end + 24 * 60),
        (event_start - 24 * 60, event_end - 24 * 60),
    ):
        if max(window_start, shifted_start) < min(window_end, shifted_end):
            return True
    return False


def count_train_conflicts(
    window: Dict,
    train_schedule: List[Dict],
    goods_forecasts: List[Dict] = None,
) -> int:
    """Count timetable and forecast movements overlapping a maintenance window."""
    corridor_id = window.get("corridor_id")
    window_date = window.get("date")
    start_str = window.get("start_time", "00:00:00")
    end_str = window.get("end_time", "23:59:59")

    window_start = _time_to_minutes(start_str)
    window_end = _time_to_minutes(end_str)

    conflicts = 0
    for train in train_schedule:
        if train.get("corridor_id") != corridor_id:
            continue
        if str(train.get("date")) != str(window_date):
            continue

        event_start = _time_to_minutes(train.get("departure_time", "00:00:00"))
        event_end = _time_to_minutes(train.get("arrival_time") or train.get("departure_time", "00:00:00"))
        if not train.get("arrival_time"):
            event_end = event_start + 1

        if _interval_overlaps(window_start, window_end, event_start, event_end):
            conflicts += 1

    for forecast in goods_forecasts or []:
        if forecast.get("corridor_id") != corridor_id:
            continue
        if str(forecast.get("date")) != str(window_date):
            continue

        event_start = _time_to_minutes(forecast.get("expected_start_time"))
        event_end = _time_to_minutes(forecast.get("expected_end_time"))
        if _interval_overlaps(window_start, window_end, event_start, event_end):
            conflicts += int(forecast.get("train_count", 1) or 1)

    return conflicts

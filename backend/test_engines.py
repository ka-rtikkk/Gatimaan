import sys
sys.path.insert(0, '.')
from app.services.priority_engine import calculate_priority_score, calculate_priorities_bulk
from app.services.compatibility_engine import find_compatible_groups, count_train_conflicts

# Test the demo scenario
tasks = [
    {'task_id': 'T0001', 'department': 'Engineering', 'task_type': 'Track Geometry Correction',
     'criticality': 5, 'urgency': 5, 'safety_risk': 5, 'asset_importance': 5,
     'due_date': None, 'overdue': False, 'corridor_id': 'DEL-AGR',
     'duration_hours': 2.0, 'latitude': 27.856, 'longitude': 77.612,
     'compatible_departments': ['S&T', 'Traction Distribution']},
    {'task_id': 'T0002', 'department': 'S&T', 'task_type': 'Point Machine Overhaul',
     'criticality': 4, 'urgency': 4, 'safety_risk': 5, 'asset_importance': 4,
     'due_date': None, 'overdue': False, 'corridor_id': 'DEL-AGR',
     'duration_hours': 1.0, 'latitude': 27.780, 'longitude': 77.640,
     'compatible_departments': ['Engineering', 'Traction Distribution']},
    {'task_id': 'T0003', 'department': 'Traction Distribution', 'task_type': 'OHE Inspection',
     'criticality': 4, 'urgency': 3, 'safety_risk': 4, 'asset_importance': 4,
     'due_date': None, 'overdue': False, 'corridor_id': 'DEL-AGR',
     'duration_hours': 1.0, 'latitude': 27.800, 'longitude': 77.630,
     'compatible_departments': ['Engineering', 'S&T']},
    {'task_id': 'T0004', 'department': 'Engineering', 'task_type': 'Ballast Tamping',
     'criticality': 2, 'urgency': 2, 'safety_risk': 2, 'asset_importance': 2,
     'due_date': None, 'overdue': False, 'corridor_id': 'MUM-PUN',
     'duration_hours': 1.5, 'latitude': 18.8, 'longitude': 73.6,
     'compatible_departments': []},
]

print("=== PRIORITY ENGINE TEST ===")
scored = calculate_priorities_bulk(tasks)
for t in scored:
    print(f"{t['task_id']}: score={t['priority_score']:.4f} category={t['priority_category']}")
    print(f"  {t['priority_explanation']}")

print("\n=== COMPATIBILITY ENGINE TEST ===")
groups = find_compatible_groups(scored)
print(f"Found {len(groups)} task groups:")
for g in groups:
    print(f"  Corridor {g['corridor_id']}: {[t['task_id'] for t in g['tasks']]} | Depts: {g['departments']} | Duration: {g['total_duration']}h | Multi-dept: {g['multi_department']}")

print("\nAll engines working correctly!")

# Minute-level timetable overlap regression: 10:05–10:15 overlaps 09:45–10:30.
assert count_train_conflicts(
    {'corridor_id': 'TEST', 'date': '2026-09-05', 'start_time': '09:45:00', 'end_time': '10:30:00'},
    [{'corridor_id': 'TEST', 'date': '2026-09-05', 'departure_time': '10:05:00', 'arrival_time': '10:15:00'}],
) == 1
print("Minute-level train conflict regression passed!")

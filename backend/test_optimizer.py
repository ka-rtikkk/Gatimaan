"""Full optimization pipeline test (without Supabase)"""
import sys
sys.path.insert(0, '.')
from datetime import date, timedelta
from app.services.priority_engine import calculate_priorities_bulk
from app.services.compatibility_engine import find_compatible_groups
from app.services.optimizer import run_ortools_optimizer, generate_baseline_plan, compute_improvement_metrics

# Demo scenario tasks
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
]

# Block windows
today = date.today()
block_windows = [
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'start_time': '12:00:00', 'end_time': '14:00:00', 'available': True, 'maximum_duration': 2.0},
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'start_time': '14:00:00', 'end_time': '17:00:00', 'available': True, 'maximum_duration': 3.0},
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'start_time': '18:00:00', 'end_time': '21:00:00', 'available': True, 'maximum_duration': 3.0},
]

# Train schedule
trains = [
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'departure_time': '10:15:00', 'train_number': '12001'},
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'departure_time': '11:00:00', 'train_number': '12003'},
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'departure_time': '13:30:00', 'train_number': '12005'},
    {'corridor_id': 'DEL-AGR', 'date': today.isoformat(), 'departure_time': '16:30:00', 'train_number': '12007'},
]

print("=== FULL OPTIMIZATION PIPELINE TEST ===\n")

# Step 1: Priority scoring
scored = calculate_priorities_bulk(tasks)
print("Step 1 - Priority Scores:")
for t in scored:
    print(f"  {t['task_id']}: {t['priority_category']} ({t['priority_score']:.4f})")

# Step 2: Compatibility detection
groups = find_compatible_groups(scored, block_windows)
print(f"\nStep 2 - Compatible Groups: {len(groups)}")
for g in groups:
    print(f"  Tasks: {g['task_ids']} | Depts: {g['departments']} | Total: {g['total_duration']}h | Multi: {g['multi_department']}")

# Step 3: Optimization
print("\nStep 3 - Running OR-Tools optimizer...")
opt_blocks, opt_metrics = run_ortools_optimizer(groups, block_windows, trains, 'today')
assert opt_metrics['tasks_scheduled'] == 3
assert len(opt_blocks) == 2
assert any(len(block['departments_involved']) > 1 for block in opt_blocks)
print(f"  Solver status: {opt_metrics.get('solver_status', 'unknown')}")
print(f"  Blocks generated: {len(opt_blocks)}")
print(f"  Tasks scheduled: {opt_metrics['tasks_scheduled']}")
print(f"  Total block hours: {opt_metrics['total_block_hours']}h")

for block in opt_blocks:
    print(f"\n  BLOCK: {block['block_id']}")
    print(f"    Corridor: {block['corridor_id']}")
    print(f"    Time: {block['start_time']} - {block['end_time']}")
    print(f"    Duration: {block['duration_hours']}h")
    print(f"    Departments: {block['departments_involved']}")
    print(f"    Tasks: {block['task_ids']}")
    print(f"    Train conflicts: {block['train_conflicts']}")
    print(f"    Optimization score: {block['optimization_score']}")
    print(f"    Explanation preview: {block['explanation'][:200]}...")

# Step 4: Baseline comparison
print("\nStep 4 - Baseline (manual/decentralized) plan:")
base_blocks, base_metrics = generate_baseline_plan(scored, block_windows, trains)
print(f"  Baseline blocks: {base_metrics['total_blocks']}")
print(f"  Baseline hours: {base_metrics['total_block_hours']}h")

# Step 5: Improvement metrics
improvement = compute_improvement_metrics(base_metrics, opt_metrics, opt_blocks)
print(f"\nStep 5 - Improvement:")
print(f"  Block hours: {improvement['baseline_block_hours']}h -> {improvement['optimized_block_hours']}h ({improvement['improvement_percentage']}% improvement)")
print(f"  Blocks: {improvement['baseline_blocks']} -> {improvement['optimized_blocks_count']} ({improvement['blocks_reduced']} reduced)")
print(f"\n  NOTE: {improvement['note']}")
print("\n✓ Full optimization pipeline working end-to-end!")

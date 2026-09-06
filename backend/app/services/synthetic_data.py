"""
=============================================================================
GATIMAAN SYNTHETIC DATA GENERATOR
=============================================================================
Generates realistic synthetic railway maintenance data modeled after:
- TMS (Track Management System)    → Engineering department
- SMMS (Signalling Maintenance & Management System) → S&T department
- TDMS (Traction Distribution Management System)   → Traction Distribution

IMPORTANT: This is SIMULATED PROTOTYPE DATA.
Not connected to real Indian Railways operational systems.
=============================================================================
"""

import random
import uuid
import json
from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any
import numpy as np

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# =============================================================================
# CORRIDOR DEFINITIONS (Synthetic demo corridors)
# =============================================================================
CORRIDORS = [
    {"corridor_id": "DEL-AGR", "corridor_name": "Delhi–Agra Corridor", "from_station": "Delhi", "to_station": "Agra", "distance_km": 195.0, "zone": "NCR", "division": "Agra", "electrified": True},
    {"corridor_id": "LKO-CNB", "corridor_name": "Lucknow–Kanpur Corridor", "from_station": "Lucknow", "to_station": "Kanpur", "distance_km": 75.0, "zone": "NR", "division": "Lucknow", "electrified": True},
    {"corridor_id": "MUM-PUN", "corridor_name": "Mumbai–Pune Corridor", "from_station": "Mumbai CSMT", "to_station": "Pune", "distance_km": 192.0, "zone": "CR", "division": "Pune", "electrified": True},
    {"corridor_id": "CHN-BNG", "corridor_name": "Chennai–Bengaluru Corridor", "from_station": "Chennai Central", "to_station": "Bengaluru City", "distance_km": 362.0, "zone": "SR", "division": "Chennai", "electrified": True},
    {"corridor_id": "KOL-ASN", "corridor_name": "Kolkata–Asansol Corridor", "from_station": "Howrah", "to_station": "Asansol", "distance_km": 200.0, "zone": "ER", "division": "Asansol", "electrified": True},
    {"corridor_id": "DEL-ALD", "corridor_name": "Delhi–Allahabad Corridor", "from_station": "New Delhi", "to_station": "Prayagraj", "distance_km": 642.0, "zone": "NCR", "division": "Prayagraj", "electrified": True},
    {"corridor_id": "HYD-SEC", "corridor_name": "Hyderabad–Secunderabad Corridor", "from_station": "Hyderabad", "to_station": "Secunderabad", "distance_km": 12.0, "zone": "SCR", "division": "Hyderabad", "electrified": True},
    {"corridor_id": "JAI-AJM", "corridor_name": "Jaipur–Ajmer Corridor", "from_station": "Jaipur", "to_station": "Ajmer", "distance_km": 132.0, "zone": "NWR", "division": "Jaipur", "electrified": True},
    {"corridor_id": "AMD-RTM", "corridor_name": "Ahmedabad–Ratlam Corridor", "from_station": "Ahmedabad", "to_station": "Ratlam", "distance_km": 279.0, "zone": "WR", "division": "Ratlam", "electrified": True},
    {"corridor_id": "PAT-DHN", "corridor_name": "Patna–Dhanbad Corridor", "from_station": "Patna", "to_station": "Dhanbad", "distance_km": 295.0, "zone": "ECR", "division": "Dhanbad", "electrified": True},
    {"corridor_id": "NGP-ITR", "corridor_name": "Nagpur–Itarsi Corridor", "from_station": "Nagpur", "to_station": "Itarsi", "distance_km": 270.0, "zone": "CR", "division": "Nagpur", "electrified": True},
    {"corridor_id": "BPL-KTE", "corridor_name": "Bhopal–Katni Corridor", "from_station": "Bhopal", "to_station": "Katni", "distance_km": 295.0, "zone": "WCR", "division": "Bhopal", "electrified": True},
    {"corridor_id": "VZG-VJW", "corridor_name": "Visakhapatnam–Vijayawada Corridor", "from_station": "Visakhapatnam", "to_station": "Vijayawada", "distance_km": 347.0, "zone": "ECoR", "division": "Visakhapatnam", "electrified": True},
    {"corridor_id": "SUR-GNT", "corridor_name": "Solapur–Guntakal Corridor", "from_station": "Solapur", "to_station": "Guntakal", "distance_km": 349.0, "zone": "SCR", "division": "Guntakal", "electrified": True},
    {"corridor_id": "AWB-WRD", "corridor_name": "Aurangabad–Wardha Corridor", "from_station": "Aurangabad", "to_station": "Wardha", "distance_km": 323.0, "zone": "SCR", "division": "Nanded", "electrified": True},
    {"corridor_id": "GHY-LUM", "corridor_name": "Guwahati–Lumding Corridor", "from_station": "Guwahati", "to_station": "Lumding", "distance_km": 208.0, "zone": "NFR", "division": "Lumding", "electrified": False},
    {"corridor_id": "JMU-UDM", "corridor_name": "Jammu–Udhampur Corridor", "from_station": "Jammu Tawi", "to_station": "Udhampur", "distance_km": 65.0, "zone": "NR", "division": "Firozpur", "electrified": False},
    {"corridor_id": "TVC-ERN", "corridor_name": "Thiruvananthapuram–Ernakulam Corridor", "from_station": "Thiruvananthapuram", "to_station": "Ernakulam", "distance_km": 222.0, "zone": "SR", "division": "Thiruvananthapuram", "electrified": True},
    {"corridor_id": "RJT-ADI", "corridor_name": "Rajkot–Ahmedabad Corridor", "from_station": "Rajkot", "to_station": "Ahmedabad", "distance_km": 216.0, "zone": "WR", "division": "Rajkot", "electrified": True},
    {"corridor_id": "BSP-RIG", "corridor_name": "Bilaspur–Raigarh Corridor", "from_station": "Bilaspur", "to_station": "Raigarh", "distance_km": 148.0, "zone": "SECR", "division": "Bilaspur", "electrified": True},
]

# =============================================================================
# TASK TEMPLATES BY DEPARTMENT
# =============================================================================

ENGINEERING_TASKS = [
    {"task_type": "Track Geometry Correction", "asset_type": "Track", "duration_range": (2, 4), "criticality_range": (3, 5), "safety_range": (3, 5)},
    {"task_type": "Rail Replacement", "asset_type": "Rail", "duration_range": (3, 6), "criticality_range": (4, 5), "safety_range": (4, 5)},
    {"task_type": "Sleeper Replacement", "asset_type": "Sleeper", "duration_range": (2, 4), "criticality_range": (3, 4), "safety_range": (3, 4)},
    {"task_type": "Ballast Tamping", "asset_type": "Track", "duration_range": (1, 3), "criticality_range": (2, 4), "safety_range": (2, 4)},
    {"task_type": "Level Crossing Maintenance", "asset_type": "Level Crossing", "duration_range": (1, 2), "criticality_range": (3, 5), "safety_range": (3, 5)},
    {"task_type": "Bridge Inspection", "asset_type": "Bridge", "duration_range": (2, 5), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Culvert Repair", "asset_type": "Culvert", "duration_range": (2, 4), "criticality_range": (2, 4), "safety_range": (2, 4)},
    {"task_type": "Turnout Maintenance", "asset_type": "Turnout/Points", "duration_range": (1, 3), "criticality_range": (3, 5), "safety_range": (3, 5)},
    {"task_type": "Welding / Thermit Weld Repair", "asset_type": "Rail", "duration_range": (1, 2), "criticality_range": (4, 5), "safety_range": (4, 5)},
    {"task_type": "Formation Repair", "asset_type": "Formation", "duration_range": (3, 6), "criticality_range": (3, 5), "safety_range": (3, 4)},
    {"task_type": "Retaining Wall Inspection", "asset_type": "Retaining Wall", "duration_range": (1, 3), "criticality_range": (2, 4), "safety_range": (3, 4)},
    {"task_type": "Rail Fracture Repair", "asset_type": "Rail", "duration_range": (1, 2), "criticality_range": (5, 5), "safety_range": (5, 5)},
    {"task_type": "Deferred Scheduled Maintenance", "asset_type": "Track", "duration_range": (1, 2), "criticality_range": (2, 3), "safety_range": (2, 3)},
    {"task_type": "Track Inspection (SSE patrol)", "asset_type": "Track", "duration_range": (1, 2), "criticality_range": (1, 3), "safety_range": (2, 3)},
]

ST_TASKS = [
    {"task_type": "Signal Lamp Replacement", "asset_type": "Signal", "duration_range": (0.5, 1), "criticality_range": (2, 4), "safety_range": (3, 4)},
    {"task_type": "Point Machine Overhaul", "asset_type": "Point Machine", "duration_range": (2, 4), "criticality_range": (4, 5), "safety_range": (4, 5)},
    {"task_type": "Track Circuit Testing", "asset_type": "Track Circuit", "duration_range": (1, 2), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Relay Room Maintenance", "asset_type": "Relay Room", "duration_range": (2, 4), "criticality_range": (3, 5), "safety_range": (3, 5)},
    {"task_type": "Level Crossing Gate Signal", "asset_type": "LC Gate Signal", "duration_range": (1, 2), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "BPAC/TPWS Testing", "asset_type": "ATP System", "duration_range": (1, 3), "criticality_range": (4, 5), "safety_range": (5, 5)},
    {"task_type": "Axle Counter Testing", "asset_type": "Axle Counter", "duration_range": (1, 2), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Interlocking Check", "asset_type": "Interlocking", "duration_range": (2, 4), "criticality_range": (4, 5), "safety_range": (5, 5)},
    {"task_type": "OFC Cable Repair", "asset_type": "Optical Fibre Cable", "duration_range": (1, 3), "criticality_range": (2, 4), "safety_range": (2, 3)},
    {"task_type": "Station Signalling System Check", "asset_type": "Station Signalling", "duration_range": (1, 3), "criticality_range": (3, 5), "safety_range": (3, 5)},
    {"task_type": "Block Proving Axle Counter Reset", "asset_type": "BPAC", "duration_range": (0.5, 1), "criticality_range": (3, 4), "safety_range": (4, 5)},
    {"task_type": "Telecom Equipment Maintenance", "asset_type": "Telecom", "duration_range": (1, 2), "criticality_range": (1, 3), "safety_range": (1, 2)},
    {"task_type": "Electronic Interlocking Maintenance", "asset_type": "Electronic Interlocking", "duration_range": (2, 4), "criticality_range": (4, 5), "safety_range": (4, 5)},
]

TRACTION_TASKS = [
    {"task_type": "OHE Wire Replacement", "asset_type": "OHE", "duration_range": (3, 6), "criticality_range": (4, 5), "safety_range": (4, 5)},
    {"task_type": "OHE Inspection (Scheduled)", "asset_type": "OHE", "duration_range": (1, 2), "criticality_range": (2, 4), "safety_range": (3, 4)},
    {"task_type": "Pantograph Damage Repair", "asset_type": "OHE/Pantograph", "duration_range": (1, 3), "criticality_range": (4, 5), "safety_range": (5, 5)},
    {"task_type": "Mast Foundation Repair", "asset_type": "OHE Mast", "duration_range": (2, 4), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Section Insulator Replacement", "asset_type": "Section Insulator", "duration_range": (1, 2), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Booster Transformer Maintenance", "asset_type": "Booster Transformer", "duration_range": (2, 3), "criticality_range": (3, 5), "safety_range": (3, 4)},
    {"task_type": "Switching Station Maintenance", "asset_type": "Switching Station", "duration_range": (2, 4), "criticality_range": (3, 5), "safety_range": (4, 5)},
    {"task_type": "Earth Continuity Check", "asset_type": "Earthing", "duration_range": (1, 2), "criticality_range": (2, 4), "safety_range": (4, 5)},
    {"task_type": "Stagger/Sag Adjustment", "asset_type": "OHE", "duration_range": (1, 2), "criticality_range": (2, 4), "safety_range": (3, 4)},
    {"task_type": "Return Current Check", "asset_type": "Return Rail", "duration_range": (1, 2), "criticality_range": (2, 3), "safety_range": (2, 3)},
    {"task_type": "Feed Post Maintenance", "asset_type": "Feed Post", "duration_range": (2, 3), "criticality_range": (3, 4), "safety_range": (3, 4)},
    {"task_type": "Emergency OHE Restoration", "asset_type": "OHE", "duration_range": (1, 3), "criticality_range": (5, 5), "safety_range": (5, 5)},
]

# Asset names for variety
ENGINEERING_ASSETS = [
    "Between Station A-B km {}", "Km {} to km {}", "Station {} Yard",
    "Bridge No.{} over River {}", "Level Crossing No.{}", "Turnout No.{} at {}",
    "Culvert No.{}", "Formation km {} to {}", "Rail Joint at km {}"
]

ST_ASSETS = [
    "Station {} Signal Panel", "Block Section {}–{}", "Level Crossing Gate {}",
    "Station {} Relay Room", "{} Cabin Signal", "Axle Counter between {}–{}",
    "Point No.{} at {} Station", "OFC Section {}–{}", "Telecom Tower at {}"
]

TRACTION_ASSETS = [
    "OHE Section {}–{}", "Mast No.{} at km {}", "Switching Station {}",
    "Feeder Section {}–{}", "Section Insulator at km {}", "Booster Transformer at km {}",
    "Feed Post at Station {}", "Emergency OHE km {}–{}"
]

STATION_NAMES = [
    "Delhi", "Agra", "Mathura", "Gwalior", "Lucknow", "Kanpur", "Prayagraj",
    "Mumbai", "Pune", "Lonavala", "Karjat", "Chennai", "Bengaluru", "Jolarpettai",
    "Katpadi", "Kolkata", "Asansol", "Durgapur", "Dhanbad", "Hyderabad",
    "Secunderabad", "Jaipur", "Ajmer", "Ahmedabad", "Ratlam", "Nagpur",
    "Itarsi", "Bhopal", "Guwahati", "Thiruvananthapuram", "Ernakulam"
]

RIVER_NAMES = ["Yamuna", "Ganga", "Chambal", "Godavari", "Krishna", "Kaveri", "Narmada", "Tapti"]


def random_station():
    return random.choice(STATION_NAMES)


def random_asset_name(department: str) -> str:
    if department == "Engineering":
        template = random.choice(ENGINEERING_ASSETS)
        return template.format(
            random.randint(100, 999),
            random.randint(1, 50),
            random_station(),
            random.randint(1, 999),
            random.choice(RIVER_NAMES),
            random.randint(1, 30),
            random_station(),
            random.randint(1, 50),
            random.randint(50, 500),
            random.randint(550, 600),
        )
    elif department == "S&T":
        template = random.choice(ST_ASSETS)
        return template.format(
            random_station(), random_station(), random_station(),
            random.randint(1, 50), random_station(), random.randint(1, 30),
            random_station(), random_station(), random_station()
        )
    else:
        template = random.choice(TRACTION_ASSETS)
        return template.format(
            random_station(), random_station(),
            random.randint(1, 200), random.randint(100, 500),
            random_station(), random.randint(100, 500),
            random.randint(500, 550),
            random_station(), random.randint(100, 200), random.randint(200, 250)
        )


def generate_lat_lon(corridor: dict) -> tuple:
    """Generate approximate lat/lon near Indian railway corridors"""
    base_coords = {
        "DEL-AGR": (27.5, 77.9), "LKO-CNB": (26.5, 80.5), "MUM-PUN": (18.8, 73.6),
        "CHN-BNG": (12.8, 79.2), "KOL-ASN": (23.2, 87.5), "DEL-ALD": (25.0, 81.0),
        "HYD-SEC": (17.4, 78.5), "JAI-AJM": (26.2, 74.9), "AMD-RTM": (23.2, 73.9),
        "PAT-DHN": (24.5, 86.0), "NGP-ITR": (22.0, 78.5), "BPL-KTE": (23.5, 79.5),
        "VZG-VJW": (16.2, 81.0), "SUR-GNT": (16.0, 77.5), "AWB-WRD": (19.7, 77.5),
        "GHY-LUM": (25.8, 92.0), "JMU-UDM": (32.8, 75.0), "TVC-ERN": (10.0, 76.5),
        "RJT-ADI": (22.5, 71.5), "BSP-RIG": (22.0, 83.0),
    }
    base = base_coords.get(corridor["corridor_id"], (22.0, 78.0))
    lat = base[0] + random.uniform(-0.5, 0.5)
    lon = base[1] + random.uniform(-0.5, 0.5)
    return round(lat, 6), round(lon, 6)


def generate_maintenance_tasks(n: int = 120) -> List[Dict]:
    """Generate n synthetic maintenance tasks from all 3 departments"""
    tasks = []
    today = date.today()

    dept_split = {"Engineering": 45, "S&T": 35, "Traction Distribution": 40}
    task_counter = 1

    for dept, count in dept_split.items():
        if dept == "Engineering":
            templates = ENGINEERING_TASKS
        elif dept == "S&T":
            templates = ST_TASKS
        else:
            templates = TRACTION_TASKS

        for _ in range(count):
            corridor = random.choice(CORRIDORS)
            template = random.choice(templates)
            lat, lon = generate_lat_lon(corridor)

            duration = round(random.uniform(*template["duration_range"]) * 2) / 2  # 0.5 steps

            criticality = random.randint(*template["criticality_range"])
            urgency = random.randint(1, 5)
            safety_risk = random.randint(*template["safety_range"])
            asset_importance = random.randint(2, 5)

            # Due date: mix of overdue, upcoming, future
            overdue_chance = random.random()
            if overdue_chance < 0.2:
                # Overdue
                due_offset = -random.randint(1, 14)
            elif overdue_chance < 0.5:
                # Due soon (1-7 days)
                due_offset = random.randint(1, 7)
            else:
                # Future (7-45 days)
                due_offset = random.randint(7, 45)

            due_date = today + timedelta(days=due_offset)
            overdue = due_offset < 0

            # Compatible departments (tasks that can share a block)
            all_depts = ["Engineering", "S&T", "Traction Distribution"]
            compatible = [d for d in all_depts if d != dept]
            # Not all tasks are compatible with all departments
            compatible_with = random.sample(compatible, k=random.randint(0, 2))

            task_id = f"T{task_counter:04d}"
            task_counter += 1

            tasks.append({
                "task_id": task_id,
                "department": dept,
                "asset_type": template["asset_type"],
                "asset_name": f"{template['asset_type']} at {corridor['from_station']}-{corridor['to_station']} #{random.randint(1,99):02d}",
                "corridor_id": corridor["corridor_id"],
                "location": f"{corridor['from_station']}–{corridor['to_station']} Section",
                "latitude": lat,
                "longitude": lon,
                "task_type": template["task_type"],
                "description": f"{template['task_type']} required at {corridor['corridor_name']}. "
                               f"{'OVERDUE: ' if overdue else ''}Asset condition warrants immediate attention.",
                "duration_hours": duration,
                "criticality": criticality,
                "urgency": urgency,
                "safety_risk": safety_risk,
                "asset_importance": asset_importance,
                "due_date": due_date.isoformat(),
                "overdue": overdue,
                "status": "Overdue" if overdue else random.choice(["Pending", "Pending", "Pending", "Scheduled"]),
                "compatible_departments": compatible_with,
            })

    # Add specific demo scenario tasks for DEL-AGR corridor
    demo_tasks = [
        {
            "task_id": "T0001",
            "department": "Engineering",
            "asset_type": "Track",
            "asset_name": "Track km 45-47 Delhi-Agra Section",
            "corridor_id": "DEL-AGR",
            "location": "Delhi–Agra km 45–47",
            "latitude": 27.856, "longitude": 77.612,
            "task_type": "Track Geometry Correction",
            "description": "Critical track geometry deviation detected. Requires urgent correction to prevent derailment risk.",
            "duration_hours": 2.0,
            "criticality": 5, "urgency": 5, "safety_risk": 5, "asset_importance": 5,
            "due_date": (today + timedelta(days=1)).isoformat(),
            "overdue": False, "status": "Pending",
            "compatible_departments": ["S&T", "Traction Distribution"],
        },
        {
            "task_id": "T0002",
            "department": "S&T",
            "asset_type": "Signal",
            "asset_name": "Station Signal Panel at Mathura",
            "corridor_id": "DEL-AGR",
            "location": "Mathura Station",
            "latitude": 27.502, "longitude": 77.671,
            "task_type": "Point Machine Overhaul",
            "description": "Point machine showing intermittent failure. Overhaul required to ensure signal safety.",
            "duration_hours": 1.0,
            "criticality": 4, "urgency": 4, "safety_risk": 5, "asset_importance": 4,
            "due_date": (today + timedelta(days=2)).isoformat(),
            "overdue": False, "status": "Pending",
            "compatible_departments": ["Engineering", "Traction Distribution"],
        },
        {
            "task_id": "T0003",
            "department": "Traction Distribution",
            "asset_type": "OHE",
            "asset_name": "OHE Section Delhi-Mathura km 45-50",
            "corridor_id": "DEL-AGR",
            "location": "Delhi–Agra km 45–50",
            "latitude": 27.780, "longitude": 77.640,
            "task_type": "OHE Inspection (Scheduled)",
            "description": "Scheduled OHE inspection. Stagger adjustment required at multiple locations.",
            "duration_hours": 1.0,
            "criticality": 4, "urgency": 3, "safety_risk": 4, "asset_importance": 4,
            "due_date": (today + timedelta(days=3)).isoformat(),
            "overdue": False, "status": "Pending",
            "compatible_departments": ["Engineering", "S&T"],
        },
    ]

    # Replace first 3 tasks with demo tasks
    for i, dt in enumerate(demo_tasks):
        # Check if T0001/T0002/T0003 already exist
        existing = [t for t in tasks if t["task_id"] in ["T0001", "T0002", "T0003"]]
        if len(existing) < 3:
            tasks.insert(i, dt)

    return tasks[:n + 3]  # ensure we have demo tasks + n tasks


# =============================================================================
# TRAIN SCHEDULE GENERATOR
# =============================================================================

TRAIN_TEMPLATES = [
    {"type": "Express", "priority": 2, "is_goods": False, "names": ["Shatabdi Express", "Rajdhani Express", "Duronto Express", "Humsafar Express", "Tejas Express"]},
    {"type": "Superfast", "priority": 2, "is_goods": False, "names": ["Superfast Mail", "Jan Shatabdi", "Intercity Express", "Sampark Kranti"]},
    {"type": "Passenger", "priority": 3, "is_goods": False, "names": ["Passenger", "MEMU", "Passenger Express"]},
    {"type": "Goods", "priority": 4, "is_goods": True, "names": ["BOXN Freight", "BCNA Goods", "Container Express", "Coal Rake", "Food Grain Rake"]},
    {"type": "Mail", "priority": 3, "is_goods": False, "names": ["Mail Express", "Night Mail"]},
]


def random_time() -> str:
    hour = random.randint(0, 23)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}:00"


def generate_train_schedule(n: int = 220) -> List[Dict]:
    """Generate n synthetic train movements across corridors"""
    trains = []
    today = date.today()

    train_number = 12001
    for i in range(n):
        corridor = random.choice(CORRIDORS)
        template = random.choice(TRAIN_TEMPLATES)
        train_name = random.choice(template["names"])

        # Date: today to next 7 days
        train_date = today + timedelta(days=random.randint(0, 7))

        dep_hour = random.randint(0, 23)
        dep_min = random.choice([0, 15, 30, 45])
        departure_time = f"{dep_hour:02d}:{dep_min:02d}:00"

        # Arrival is departure + travel time (1-6 hours)
        travel_hours = random.randint(1, 6)
        arr_hour = (dep_hour + travel_hours) % 24
        arrival_time = f"{arr_hour:02d}:{dep_min:02d}:00"

        trains.append({
            "train_number": str(train_number),
            "train_name": f"{train_name} ({corridor['from_station']}-{corridor['to_station']})",
            "train_type": template["type"],
            "corridor_id": corridor["corridor_id"],
            "date": train_date.isoformat(),
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "priority": template["priority"],
            "is_goods_train": template["is_goods"],
        })
        train_number += random.randint(1, 5)

    return trains


# =============================================================================
# GOODS FORECAST GENERATOR
# =============================================================================

def generate_goods_forecast(n: int = 60) -> List[Dict]:
    """Generate goods train forecasts"""
    forecasts = []
    today = date.today()

    for _ in range(n):
        corridor = random.choice(CORRIDORS)
        forecast_date = today + timedelta(days=random.randint(0, 7))

        start_hour = random.randint(0, 22)
        end_hour = start_hour + random.randint(1, 3)
        if end_hour > 23:
            end_hour = 23

        forecasts.append({
            "corridor_id": corridor["corridor_id"],
            "date": forecast_date.isoformat(),
            "expected_start_time": f"{start_hour:02d}:00:00",
            "expected_end_time": f"{end_hour:02d}:00:00",
            "probability": round(random.uniform(0.4, 1.0), 2),
            "train_count": random.randint(1, 4),
        })

    return forecasts


# =============================================================================
# BLOCK WINDOWS GENERATOR
# =============================================================================

BLOCK_WINDOW_SLOTS = [
    ("01:00", "04:00", "Night maintenance window"),
    ("10:00", "12:00", "Morning maintenance window"),
    ("12:00", "14:00", "Midday maintenance window"),
    ("14:00", "17:00", "Afternoon maintenance window"),
    ("18:00", "21:00", "Evening maintenance window"),
    ("22:00", "01:00", "Late night maintenance window"),
]


def generate_block_windows(n: int = 80) -> List[Dict]:
    """Generate available maintenance block windows"""
    windows = []
    today = date.today()

    for corridor in CORRIDORS:
        for day_offset in range(7):
            window_date = today + timedelta(days=day_offset)
            # Each corridor gets 2-4 windows per day
            num_windows = random.randint(2, 4)
            selected_slots = random.sample(BLOCK_WINDOW_SLOTS, min(num_windows, len(BLOCK_WINDOW_SLOTS)))

            for slot in selected_slots:
                available = random.random() > 0.15  # 85% chance available
                start_h, start_m = int(slot[0].split(":")[0]), int(slot[0].split(":")[1])
                end_h, end_m = int(slot[1].split(":")[0]), int(slot[1].split(":")[1])

                if end_h <= start_h:
                    end_h = start_h + 2  # ensure end > start for demo

                max_duration = end_h - start_h + (end_m - start_m) / 60.0

                windows.append({
                    "corridor_id": corridor["corridor_id"],
                    "date": window_date.isoformat(),
                    "start_time": f"{start_h:02d}:{start_m:02d}:00",
                    "end_time": f"{end_h:02d}:{end_m:02d}:00",
                    "available": available,
                    "reason": slot[2] if available else "Reserved for special train",
                    "maximum_duration": round(max_duration, 2),
                })

    # Add specific demo windows for DEL-AGR
    demo_windows = [
        {"corridor_id": "DEL-AGR", "date": today.isoformat(), "start_time": "12:00:00", "end_time": "14:00:00", "available": True, "reason": "Demo morning block", "maximum_duration": 2.0},
        {"corridor_id": "DEL-AGR", "date": today.isoformat(), "start_time": "14:00:00", "end_time": "17:00:00", "available": True, "reason": "Demo afternoon block", "maximum_duration": 3.0},
        {"corridor_id": "DEL-AGR", "date": today.isoformat(), "start_time": "18:00:00", "end_time": "21:00:00", "available": True, "reason": "Demo evening block", "maximum_duration": 3.0},
    ]

    return demo_windows + windows


def get_all_synthetic_data() -> Dict[str, List]:
    """Generate all synthetic data and return as dict"""
    print("Generating synthetic railway data (PROTOTYPE - NOT REAL OPERATIONAL DATA)...")
    tasks = generate_maintenance_tasks(120)
    trains = generate_train_schedule(220)
    forecasts = generate_goods_forecast(60)
    windows = generate_block_windows()

    print(f"  ✓ {len(tasks)} maintenance tasks")
    print(f"  ✓ {len(trains)} train movements")
    print(f"  ✓ {len(forecasts)} goods forecasts")
    print(f"  ✓ {len(windows)} block windows")
    print(f"  ✓ {len(CORRIDORS)} corridors")

    return {
        "corridors": CORRIDORS,
        "tasks": tasks,
        "trains": trains,
        "forecasts": forecasts,
        "windows": windows,
    }


if __name__ == "__main__":
    data = get_all_synthetic_data()
    # Save to JSON for inspection
    import json
    with open("../data/synthetic_data.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    print("\nData saved to backend/data/synthetic_data.json")

# Gatimaan

Gatimaan estimates maintenance delay risk with a Random Forest prototype, then uses constraint optimization to find when and where the work can actually be performed. Machine learning is a prioritization signal; it does not replace corridor, timetable, compatibility, duration, or block-window constraints.

The delay-risk model is trained on 3,000 reproducible synthetic task records using fields available in the maintenance task schema. Training data is synthetic and used only for prototype demonstration. Production deployment would require historical Indian Railways maintenance, asset, failure and operational-impact data.
# GATIMAAN — AI-Powered Railway Block Planning System

> **Smart India Hackathon Prototype**  
> AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways

⚠️ **This is a prototype using SIMULATED data. Not connected to real Indian Railways operational systems.**

---

## 🏗 System Architecture

```
                    SYNTHETIC RAILWAY DATA
                            |
             +--------------+--------------+
             |              |              |
          TMS (Eng)     SMMS (S&T)     TDMS (TRD)
             |              |              |
             +--------------+--------------+
                            |
                            v
                    FASTAPI BACKEND
                    Data Ingestion Layer
                            |
                            v
                    SUPABASE (PostgreSQL)
                            |
             +--------------+--------------+
             |                             |
             v                             v
      PRIORITY ENGINE                 TRAIN DATA
      (Explainable Weighted         COA / Timetable
       Score: 0.30*crit + ...)      Goods Forecast
             |                             |
             +--------------+--------------+
                            |
                            v
               COMPATIBILITY ENGINE
               (Groups tasks by corridor,
                location, safety rules)
                            |
                            v
               OR-TOOLS CP-SAT OPTIMIZER
               (Minimizes block hours,
                conflicts, lateness)
                            |
                            v
                  BLOCK PLAN GENERATOR
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
          WEEKLY         MONTHLY        ANALYTICS
           PLAN            PLAN        (Before/After)
             |              |              |
             +--------------+--------------+
                            |
                            v
                  NEXT.JS DASHBOARD
```

---

## 📋 Database Schema

| Table | Description |
|-------|-------------|
| `maintenance_tasks` | TMS/SMMS/TDMS simulated task data with priority scores |
| `train_schedule` | Simulated COA timetable |
| `goods_forecast` | Goods train forecasts |
| `block_windows` | Available maintenance windows |
| `optimized_blocks` | OR-Tools optimization output |
| `block_tasks` | Task-to-block assignments |
| `optimization_runs` | Run metadata and comparison metrics |
| `corridors` | Reference corridor data |

---

## ⚙️ Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Supabase account** (free tier works)

---

## 🚀 Setup Instructions

### 1. Clone & Setup

```bash
git clone <repo>
cd gatimaan
```

### 2. Supabase Configuration

1. Create a project at [supabase.com](https://supabase.com)
2. Go to SQL Editor → Run the contents of `backend/db/schema.sql`
3. Copy your **Project URL** and **anon key** from Settings → API

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Start the server
python run.py
# OR: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend

# Configure environment
cp .env.local.example .env.local
# Edit NEXT_PUBLIC_API_URL=http://localhost:8000

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## 🎯 How to Run the Demo Scenario

1. Open `http://localhost:3000`
2. Login with demo credentials:
   - Username: `demo`, Password: `demo`
3. Go to **Data Import** → Click **"Load Demo Data"**
4. Go to **Block Planner** → Click **"GENERATE AI BLOCK PLAN"**
5. View the generated timeline — click any block to see optimization explanation
6. Click **"Simulate Train Conflict"** on any block to test rescheduling
7. View **Analytics** for before/after comparison

### Demo Users
| Username | Password | Role |
|----------|----------|------|
| demo | demo | Admin (Full Access) |
| control | control123 | Control Office |
| engineer | eng123 | Engineering |
| signal | signal123 | S&T |
| traction | traction123 | Traction Distribution |

---

## 🧠 How the Priority Engine Works

```python
priority_score =
    0.30 × criticality_normalized    # Safety-critical asset condition
  + 0.25 × urgency_normalized        # How urgently action is needed
  + 0.20 × safety_risk_normalized    # Risk to train operations
  + 0.15 × asset_importance_norm     # Importance to railway network
  + 0.10 × overdue_factor            # Penalty for overdue tasks
```

All inputs normalized to [0, 1]. Overdue tasks get a strong bonus factor.

**Classifications:**
- 0.80–1.00 → CRITICAL
- 0.60–0.79 → HIGH  
- 0.40–0.59 → MEDIUM
- < 0.40 → LOW

The engine is modular — the scoring function can be replaced with a trained ML model (Random Forest, XGBoost) without changing the interface.

---

## ⚡ How OR-Tools Optimization Works

The optimizer uses **Google OR-Tools CP-SAT** solver.

**Decision Variables:** Binary variable `x[group][window]` = 1 if task group `g` is assigned to block window `w`

**Objective (Maximize):**
```
Σ (priority_reward × x[g][w])
  + coordination_bonus × multi_dept_x[g][w]
  + overdue_bonus × overdue_x[g][w]
  - conflict_penalty × conflicts × x[g][w]
```

**Constraints:**
- Each task group assigned to at most one window
- Window duration not exceeded
- Same corridor only
- Train conflict avoidance (soft penalty)

**Fallback:** If OR-Tools is not installed, a greedy priority-based algorithm runs instead.

---

## 📊 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login |
| GET | `/tasks` | Get maintenance tasks |
| POST | `/tasks/calculate-priorities` | Run priority engine |
| GET | `/trains/corridors` | Get corridors |
| GET | `/trains/block-windows` | Get available windows |
| **POST** | **`/blocks/generate-plan`** | **Run full optimization pipeline** |
| GET | `/blocks/optimized` | Get optimized blocks |
| POST | `/blocks/simulate-scenario` | Simulate train conflict |
| GET | `/analytics` | Get analytics + comparison |
| POST | `/import/load-demo-data` | Seed synthetic demo data |
| POST | `/import/csv/tasks` | Upload tasks CSV |

---

## 📁 Project Structure

```
gatimaan/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, auth, database
│   │   └── services/     # Priority engine, compatibility, optimizer
│   ├── db/
│   │   └── schema.sql    # Supabase PostgreSQL schema
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── app/
    │   ├── page.tsx           # Login
    │   └── dashboard/
    │       ├── page.tsx       # Overview
    │       ├── tasks/         # Maintenance tasks
    │       ├── planner/       # Block Planner (HERO)
    │       ├── weekly/        # Weekly calendar
    │       ├── monthly/       # Monthly view
    │       ├── analytics/     # Before/After analytics
    │       ├── corridors/     # Corridor map
    │       └── import/        # Data import
    ├── components/
    │   └── ui/
    └── lib/
        ├── api.ts         # API client
        └── utils.ts       # Utilities
```

---

## ⚠️ Important Notes

1. **This is an SIH prototype.** All data is synthetic and simulated.
2. OR-Tools scheduling is deterministic — results come from actual optimization, not hardcoded values.
3. Priority scores are computed from the weighted formula — not from an LLM.
4. The system architecture is modular. Real TMS/SMMS/TDMS/COA APIs could theoretically be integrated by replacing the synthetic data services.
5. All improvement percentages shown in the analytics are simulated scenario numbers for demonstration purposes.

---

*Gatimaan — Smart India Hackathon 2025-26 | AI-Powered Railway Block Planning*

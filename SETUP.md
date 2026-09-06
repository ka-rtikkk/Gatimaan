# Gatimaan Setup Guide

This guide walks you through setting up the Gatimaan AI-Powered Railway Block Planning System for development and testing.

---

## ⚡ Quick Start (Recommended)

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Supabase account (free tier at [supabase.com](https://supabase.com))
- Git

### 1. Clone the Repository
```bash
git clone <repo-url>
cd gatimaan
```

### 2. Supabase Setup (1 minute)

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** in your Supabase project dashboard
3. Open `backend/db/schema.sql` and copy all SQL
4. Paste into Supabase SQL Editor and execute
5. Go to **Project Settings → API**
6. Copy:
   - **Project URL** (looks like `https://xxx.supabase.co`)
   - **anon public key** (under "Project API keys")
   - **service_role key** (under "Project API keys") — keep this secret!

### 3. Backend Setup

```bash
cd backend

# Windows: create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key
# SUPABASE_SERVICE_KEY=your-service-role-key
```

**Edit `.backend/.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=true

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

JWT_SECRET=gatimaan-prototype-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

PROTOTYPE_MODE=true
DATA_LABEL=SIMULATED_PROTOTYPE_DATA
```

**Start the backend:**
```bash
python run.py
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✓ Backend running at: `http://localhost:8000`  
✓ API docs at: `http://localhost:8000/docs`

### 4. Frontend Setup

In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Development server (auto-reload)
npm run dev

# OR production build
npm run build
npm start
```

✓ Frontend running at: `http://localhost:3000`

---

## 🎯 First Demo Run

1. Open `http://localhost:3000` in your browser
2. Login with:
   - **Username:** `demo`
   - **Password:** `demo`
3. Click **"Load Demo Data"** button in the upper right
4. Wait for synthetic data to load (~5-10 seconds)
5. Go to **Block Planner** from the sidebar
6. Click **"GENERATE AI BLOCK PLAN"**
7. View the generated maintenance blocks
8. Click any block to see details and optimization explanation
9. Try **"Simulate Train Conflict"** on a block

---

## 👥 Demo Users

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `demo` | `demo` | Admin | Full system access |
| `control` | `control123` | Control Office | View all data |
| `engineer` | `eng123` | Engineering | Engineering tasks |
| `signal` | `signal123` | S&T | Signalling & Telecom |
| `traction` | `traction123` | TRD | Traction Distribution |

---

## 📊 Dashboard Navigation

### Overview
- **KPI Cards:** Critical tasks, pending tasks, planned blocks, block hours, asset availability
- **Charts:** Priority distribution, department workload, weekly trend
- **AI Recommendations:** Generated from actual optimization
- **Upcoming Blocks:** Next scheduled maintenance blocks

### Block Planner ⭐ (HERO FEATURE)
- Select planning horizon: Today / This Week / This Month
- Filter by corridor (optional)
- Click **"GENERATE AI BLOCK PLAN"** to run optimization
- View generated maintenance blocks on timeline
- Click any block to see:
  - Tasks included
  - Departments involved
  - Optimization score
  - Why this block was selected (AI explanation)
  - Button to simulate train conflicts

### Weekly Plan
- Calendar view of current week
- Blocks color-coded by department
- Click to see block details
- Navigate weeks with arrows

### Monthly Plan
- Full month calendar view
- Summary cards for KPIs
- Click weeks to drill down
- Month navigation

### Maintenance Tasks
- Table of all maintenance tasks
- Filter by: Department, Corridor, Priority, Status
- Click to view task details
- See priority breakdown with scores
- **Calculate Priorities** button to re-run priority engine

### Analytics & Impact
- **BEFORE vs GATIMAAN** comparison
- Metrics:
  - Block hours saved
  - Number of blocks reduced
  - Train conflicts avoided
  - Asset availability improved
- **Important:** All metrics are from simulated scenarios for prototype demonstration

### Corridors
- Network visualization of railway corridors
- Node color/size indicates maintenance workload
- Critical tasks pulse in red
- Click nodes for detailed corridor information

### Data Import
- **Load Demo Data:** Populate with 120+ synthetic tasks
- **Clear Data:** Reset database
- **Upload CSV:** Import custom maintenance data
- CSV template provided

---

## 🔧 Architecture Overview

```
┌─────────────────────────────────┐
│   Next.js Frontend (port 3000)  │
│   TypeScript + Tailwind CSS     │
│   Recharts + Lucide Icons       │
└────────────┬────────────────────┘
             │ HTTP/JSON
             ↓
┌─────────────────────────────────┐
│    FastAPI Backend (port 8000)  │
│    - Auth (JWT tokens)          │
│    - Data ingestion             │
│    - Priority engine            │
│    - Compatibility engine       │
│    - OR-Tools optimizer         │
│    - Analytics                  │
└────────────┬────────────────────┘
             │ SQL
             ↓
┌─────────────────────────────────┐
│  Supabase PostgreSQL Database   │
│  - maintenance_tasks            │
│  - train_schedule               │
│  - block_windows                │
│  - optimized_blocks             │
│  - optimization_runs            │
│  - corridors                    │
└─────────────────────────────────┘
```

---

## 🚀 Production Deployment

### Backend (Using Gunicorn)
```bash
pip install gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### Frontend (Next.js Build)
```bash
cd frontend
npm run build
npm start
# Or use Vercel, Netlify, AWS Amplify, etc.
```

### Environment Variables for Production

**Backend (.env):**
```env
DEBUG=false
SUPABASE_URL=<production-supabase-url>
SUPABASE_KEY=<production-anon-key>
SUPABASE_SERVICE_KEY=<production-service-key>
JWT_SECRET=<generate-strong-random-secret>
CORS_ORIGINS=https://yourdomain.com
```

**Frontend (.env.production):**
```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_PROTOTYPE_MODE=false
```

---

## 🧪 Testing the System

### Run Tests
```bash
cd backend
python -m pytest
# OR
python test_engines.py   # Test priority & compatibility engines
python test_optimizer.py # Test OR-Tools optimizer
```

### API Health Check
```bash
curl http://localhost:8000/health
```

### Test Generation Pipeline
```bash
# In Python REPL:
from app.services.priority_engine import calculate_priorities_bulk
from app.services.compatibility_engine import find_compatible_groups
from app.services.optimizer import run_ortools_optimizer

# Generate test data
tasks = [...]  # Load from database
scored = calculate_priorities_bulk(tasks)
groups = find_compatible_groups(scored, block_windows)
blocks, metrics = run_ortools_optimizer(groups, block_windows, trains, "week")
```

---

## 🐛 Troubleshooting

### Backend won't start
```
Error: SUPABASE_URL and SUPABASE_KEY must be set
→ Fix: Check .env file in backend/ directory
→ Ensure Supabase credentials are correct
```

### Frontend shows "Connection refused"
```
Error: fetch failed http://localhost:8000
→ Fix: Ensure backend is running (python run.py)
→ Check .env.local has NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database connection fails
```
Error: Supabase connection failed
→ Fix: Verify SUPABASE_URL and SUPABASE_KEY in .env
→ Check that Supabase project is running
→ Run schema.sql to ensure tables exist
```

### "No pending tasks found" when generating plan
```
→ Fix: Go to Data Import → Click "Load Demo Data"
→ Wait for synthetic data to load
→ Then try Block Planner again
```

### Port 8000/3000 already in use
```bash
# Kill the process using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

---

## 📚 Key Features Explained

### Priority Engine
Assigns priority scores to maintenance tasks based on:
- **Criticality (30%):** How critical is the asset condition?
- **Urgency (25%):** How urgent is the action?
- **Safety Risk (20%):** Risk to train operations
- **Asset Importance (15%):** Importance to railway network
- **Overdue Factor (10%):** Penalty for delayed tasks

Formula:
```
score = 0.30*crit + 0.25*urgency + 0.20*safety + 0.15*importance + 0.10*overdue
```

Range: 0.0–1.0 (normalized)  
Categories: CRITICAL (0.80+), HIGH (0.60–0.79), MEDIUM (0.40–0.59), LOW (<0.40)

### Compatibility Engine
Groups tasks that can be done together in one maintenance block:
- Must be on same corridor
- Duration fits within block window
- Safety rules honored (no conflicting task types)
- Location proximity (within 15 km)
- Department compatibility

### OR-Tools Optimizer
Uses Google OR-Tools CP-SAT solver to schedule blocks:
- **Objective:** Minimize total block hours, conflicts, and task lateness
- **Constraints:** Window availability, corridor, duration, train conflicts
- **Output:** Optimized maintenance blocks with scores

If OR-Tools unavailable, falls back to greedy priority-based scheduling.

### Analytics & Comparison
Shows before/after metrics:
- **Before:** Manual/departmental scheduling
- **After:** Gatimaan optimized planning
- **Improvement:** Percentage reduction in hours, blocks, conflicts

**Note:** All demo comparison numbers are from simulated scenarios.

---

## 📞 Support & Contribution

For issues:
1. Check the Troubleshooting section above
2. Review backend logs: `http://localhost:8000/docs`
3. Check browser console for frontend errors (F12 → Console)
4. Verify Supabase connectivity and schema

For improvements:
1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

---

## ⚖️ License & Attribution

**Gatimaan** is an SIH (Smart India Hackathon) 2025-26 prototype.

**Technologies Used:**
- FastAPI (Python backend)
- Next.js 16 (Frontend)
- PostgreSQL + Supabase (Database)
- Google OR-Tools (Optimization)
- Tailwind CSS + Recharts (UI)

**Data Note:** All data is simulated and synthetic for prototype demonstration. Not connected to real Indian Railways operational systems.

---

*Last updated: August 31, 2026*  
*Gatimaan — AI-Powered Railway Block Planning System*

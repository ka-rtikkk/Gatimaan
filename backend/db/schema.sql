-- =============================================================================
-- GATIMAAN DATABASE SCHEMA
-- AI-Powered Railway Block Planning System
-- Supabase / PostgreSQL
-- SYNTHETIC PROTOTYPE DATA - NOT REAL RAILWAY OPERATIONAL DATA
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE: maintenance_tasks
-- Simulated data modeled after TMS, SMMS, TDMS systems
-- =============================================================================
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL CHECK (department IN ('Engineering', 'S&T', 'Traction Distribution')),
    asset_type VARCHAR(100) NOT NULL,
    asset_name VARCHAR(200) NOT NULL,
    corridor_id VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    task_type VARCHAR(100) NOT NULL,
    description TEXT,
    duration_hours DECIMAL(4, 2) NOT NULL CHECK (duration_hours > 0),
    criticality INTEGER NOT NULL CHECK (criticality BETWEEN 1 AND 5),
    urgency INTEGER NOT NULL CHECK (urgency BETWEEN 1 AND 5),
    safety_risk INTEGER NOT NULL CHECK (safety_risk BETWEEN 1 AND 5),
    asset_importance INTEGER NOT NULL CHECK (asset_importance BETWEEN 1 AND 5),
    due_date DATE,
    overdue BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'In Progress', 'Completed', 'Overdue')),
    compatible_departments TEXT[], -- Array of departments this task can share a block with
    priority_score DECIMAL(5, 4),
    priority_category VARCHAR(20),
    score_breakdown JSONB,
    priority_explanation TEXT,
    existing_priority_score DECIMAL(5, 4),
    ml_risk_probability DECIMAL(5, 4),
    ml_risk_category VARCHAR(20),
    ml_risk_explanation TEXT,
    final_planning_score DECIMAL(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE maintenance_tasks ADD COLUMN IF NOT EXISTS existing_priority_score DECIMAL(5, 4);
ALTER TABLE maintenance_tasks ADD COLUMN IF NOT EXISTS ml_risk_probability DECIMAL(5, 4);
ALTER TABLE maintenance_tasks ADD COLUMN IF NOT EXISTS ml_risk_category VARCHAR(20);
ALTER TABLE maintenance_tasks ADD COLUMN IF NOT EXISTS ml_risk_explanation TEXT;
ALTER TABLE maintenance_tasks ADD COLUMN IF NOT EXISTS final_planning_score DECIMAL(5, 4);

-- =============================================================================
-- TABLE: train_schedule
-- Simulated COA (Control Office Application) timetable data
-- =============================================================================
CREATE TABLE IF NOT EXISTS train_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    train_number VARCHAR(20) NOT NULL,
    train_name VARCHAR(200) NOT NULL,
    train_type VARCHAR(50) NOT NULL CHECK (train_type IN ('Express', 'Passenger', 'Goods', 'Superfast', 'Mail', 'EMU', 'Special')),
    corridor_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    arrival_time TIME,
    departure_time TIME NOT NULL,
    priority INTEGER DEFAULT 2 CHECK (priority BETWEEN 1 AND 5),
    is_goods_train BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABLE: goods_forecast
-- Simulated goods train forecasts from COA
-- =============================================================================
CREATE TABLE IF NOT EXISTS goods_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corridor_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    expected_start_time TIME NOT NULL,
    expected_end_time TIME NOT NULL,
    probability DECIMAL(4, 2) NOT NULL CHECK (probability BETWEEN 0 AND 1),
    train_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABLE: block_windows
-- Available maintenance windows when blocks can be taken
-- =============================================================================
CREATE TABLE IF NOT EXISTS block_windows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corridor_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    reason VARCHAR(200),
    maximum_duration DECIMAL(4, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABLE: optimized_blocks
-- Output of the OR-Tools optimization engine
-- =============================================================================
CREATE TABLE IF NOT EXISTS optimized_blocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    block_id VARCHAR(30) UNIQUE NOT NULL,
    corridor_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_hours DECIMAL(4, 2) NOT NULL,
    optimization_score DECIMAL(5, 2),
    train_conflicts INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    departments_involved TEXT[],
    estimated_downtime DECIMAL(4, 2),
    window_duration_hours DECIMAL(4, 2),
    utilization DECIMAL(5, 4),
    explanation TEXT,
    run_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABLE: block_tasks
-- Many-to-many relationship between blocks and tasks
-- =============================================================================
CREATE TABLE IF NOT EXISTS block_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    block_id VARCHAR(30) NOT NULL REFERENCES optimized_blocks(block_id) ON DELETE CASCADE,
    task_id VARCHAR(20) NOT NULL REFERENCES maintenance_tasks(task_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(block_id, task_id)
);

-- =============================================================================
-- TABLE: optimization_runs
-- Metadata for each optimization run
-- =============================================================================
CREATE TABLE IF NOT EXISTS optimization_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    planning_horizon VARCHAR(20) NOT NULL CHECK (planning_horizon IN ('today', 'week', 'month')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    total_tasks INTEGER DEFAULT 0,
    tasks_scheduled INTEGER DEFAULT 0,
    total_block_hours DECIMAL(6, 2) DEFAULT 0,
    separate_blocks INTEGER DEFAULT 0,
    train_conflicts INTEGER DEFAULT 0,
    estimated_asset_availability DECIMAL(5, 2),
    baseline_block_hours DECIMAL(6, 2),
    optimized_block_hours DECIMAL(6, 2),
    improvement_percentage DECIMAL(5, 2),
    average_utilization DECIMAL(5, 4),
    baseline_blocks INTEGER DEFAULT 0,
    baseline_tasks_scheduled INTEGER DEFAULT 0,
    baseline_conflicts INTEGER DEFAULT 0,
    baseline_multi_department_blocks INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'completed',
    scenario_type VARCHAR(50) DEFAULT 'standard'
);

-- =============================================================================
-- TABLE: corridors (reference data)
-- =============================================================================
CREATE TABLE IF NOT EXISTS corridors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corridor_id VARCHAR(50) UNIQUE NOT NULL,
    corridor_name VARCHAR(200) NOT NULL,
    from_station VARCHAR(100) NOT NULL,
    to_station VARCHAR(100) NOT NULL,
    distance_km DECIMAL(7, 2),
    zone VARCHAR(20),
    division VARCHAR(50),
    electrified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES for performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_tasks_corridor ON maintenance_tasks(corridor_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON maintenance_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_department ON maintenance_tasks(department);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON maintenance_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_train_schedule_corridor_date ON train_schedule(corridor_id, date);
CREATE INDEX IF NOT EXISTS idx_block_windows_corridor_date ON block_windows(corridor_id, date);
CREATE INDEX IF NOT EXISTS idx_optimized_blocks_date ON optimized_blocks(date);
CREATE INDEX IF NOT EXISTS idx_optimized_blocks_corridor ON optimized_blocks(corridor_id);

-- =============================================================================
-- ROW LEVEL SECURITY (Supabase)
-- For prototype: allow all authenticated users to read/write
-- In production: implement role-based policies
-- =============================================================================
ALTER TABLE maintenance_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE train_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE goods_forecast ENABLE ROW LEVEL SECURITY;
ALTER TABLE block_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimized_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE block_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimization_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE corridors ENABLE ROW LEVEL SECURITY;

-- Prototype policy: allow all operations for authenticated users
CREATE POLICY "Allow all for authenticated" ON maintenance_tasks FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON train_schedule FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON goods_forecast FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON block_windows FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON optimized_blocks FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON block_tasks FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON optimization_runs FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for authenticated" ON corridors FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Also allow anon for prototype demo purposes
CREATE POLICY "Allow read for anon" ON maintenance_tasks FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON train_schedule FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON goods_forecast FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON block_windows FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON optimized_blocks FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON block_tasks FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON optimization_runs FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for anon" ON corridors FOR SELECT TO anon USING (true);

-- Service role for backend writes
CREATE POLICY "Allow all for service_role" ON maintenance_tasks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON train_schedule FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON goods_forecast FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON block_windows FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON optimized_blocks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON block_tasks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON optimization_runs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service_role" ON corridors FOR ALL TO service_role USING (true) WITH CHECK (true);

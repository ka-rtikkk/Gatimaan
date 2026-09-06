'use client';
import { useEffect, useState } from 'react';
import { tasks as tasksApi, trains as trainsApi, MaintenanceTask, Corridor } from '@/lib/api';
import { DEPT_BADGE, PRIORITY_COLORS, STATUS_COLORS, formatDate, getPriorityScore } from '@/lib/utils';
import { Search, Filter, X, ChevronDown, AlertTriangle, Clock } from 'lucide-react';

const DEPTS = ['Engineering', 'S&T', 'Traction Distribution'];
const PRIORITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const STATUSES = ['Pending', 'Scheduled', 'In Progress', 'Completed', 'Overdue'];

function ScoreBar({ label, value, max = 5 }: { label: string; value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color = pct >= 80 ? 'bg-red-500' : pct >= 60 ? 'bg-orange-400' : pct >= 40 ? 'bg-yellow-400' : 'bg-slate-500';
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-500 w-32">{label}</span>
      <div className="flex-1 bg-[#e4e9f0] rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-900 w-4 text-right">{value}</span>
    </div>
  );
}

export default function TasksPage() {
  const [allTasks, setAllTasks] = useState<MaintenanceTask[]>([]);
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [selected, setSelected] = useState<MaintenanceTask | null>(null);
  const [filters, setFilters] = useState({ dept: '', corridor: '', priority: '', status: '', search: '' });
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [calculationMessage, setCalculationMessage] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function loadTasks() {
    setLoading(true);
    setLoadError(null);
    try {
      const [t, c] = await Promise.all([
      tasksApi.getAll({ limit: 300 }),
      trainsApi.getCorridors(),
      ]);
      setAllTasks(t.tasks);
      setCorridors(c.corridors);
    } catch (error: any) {
      setLoadError(error?.message || 'Unable to load maintenance tasks');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function calcPriorities() {
    setCalculating(true); setCalculationMessage(null);
    try {
      const result = await tasksApi.calculatePriorities();
      const res = await tasksApi.getAll({ limit: 300 });
      setAllTasks(res.tasks);
      setCalculationMessage(`${result.updated} tasks recalculated`);
    } catch (e: any) {
      setCalculationMessage(`Priority recalculation failed: ${e.message}`);
    }
    setCalculating(false);
  }

  const filtered = allTasks.filter(t => {
    if (filters.dept && t.department !== filters.dept) return false;
    if (filters.corridor && t.corridor_id !== filters.corridor) return false;
    if (filters.priority && t.priority_category !== filters.priority) return false;
    if (filters.status && t.status !== filters.status) return false;
    if (filters.search) {
      const q = filters.search.toLowerCase();
      if (!t.task_id.toLowerCase().includes(q) && !t.task_type.toLowerCase().includes(q) && !t.asset_name.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Table Area */}
      <div className={`flex-1 flex flex-col p-6 overflow-hidden ${selected ? 'mr-96' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Maintenance Tasks</h2>
            <p className="text-slate-500 text-xs mt-0.5">Simulated TMS · SMMS · TDMS data — {allTasks.length} tasks loaded</p>
          </div>
          <button onClick={calcPriorities} disabled={calculating} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm text-slate-900 transition disabled:opacity-50">
            {calculating ? 'Calculating...' : '↺ Recalculate Priorities'}
          </button>
        </div>
        {loadError && <div className="mb-3 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center justify-between"><span>{loadError}</span><button onClick={loadTasks} className="underline">Retry</button></div>}
        {calculationMessage && <p className="text-xs text-slate-500 mb-3">{calculationMessage}</p>}

        {/* Filters */}
        <div className="flex gap-2 mb-4 flex-wrap">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              value={filters.search}
              onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
              placeholder="Search tasks..."
              className="bg-white border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-900 w-48 focus:outline-none focus:border-blue-500"
            />
          </div>
          {([
            { key: 'dept', label: 'Department', opts: DEPTS },
            { key: 'corridor', label: 'Corridor', opts: corridors.map(c => c.corridor_id) },
            { key: 'priority', label: 'Priority', opts: PRIORITIES },
            { key: 'status', label: 'Status', opts: STATUSES },
          ] as any[]).map(({ key, label, opts }) => (
            <select
              key={key}
              value={(filters as any)[key]}
              onChange={e => setFilters(f => ({ ...f, [key]: e.target.value }))}
              className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-blue-500"
            >
              <option value="">{label}</option>
              {opts.map((o: string) => <option key={o} value={o}>{o}</option>)}
            </select>
          ))}
          {Object.values(filters).some(Boolean) && (
            <button onClick={() => setFilters({ dept: '', corridor: '', priority: '', status: '', search: '' })} className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1">
              <X className="w-3 h-3" /> Clear
            </button>
          )}
          <span className="text-xs text-slate-500 self-center ml-auto">{filtered.length} results</span>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-white sticky top-0 z-10">
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider">
                <th className="px-4 py-3">Task ID</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Asset</th>
                <th className="px-4 py-3">Corridor</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Due Date</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr><td colSpan={9} className="text-center py-12 text-slate-500">Loading tasks...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-12 text-slate-500">{allTasks.length === 0 ? 'No maintenance data available.' : 'No tasks match the current filters.'}</td></tr>
              ) : filtered.map(task => (
                <tr
                  key={task.task_id}
                  onClick={() => setSelected(task === selected ? null : task)}
                  className={`cursor-pointer transition hover:bg-white ${selected?.task_id === task.task_id ? 'bg-white border-l-2 border-l-blue-500' : ''}`}
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-blue-400 text-xs">{task.task_id}</span>
                    {task.overdue && <span className="ml-1 text-red-400">⚠</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded border ${DEPT_BADGE[task.department] || 'bg-[#e4e9f0] text-slate-700'}`}>
                      {task.department === 'Traction Distribution' ? 'TRD' : task.department}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-slate-900 text-xs">{task.task_type}</p>
                    <p className="text-slate-500 text-xs truncate max-w-[140px]">{task.asset_type}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-700 text-xs font-mono">{task.corridor_id}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded border ${PRIORITY_COLORS[task.priority_category || 'LOW']}`}>
                      {task.priority_category || 'LOW'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-900 font-mono text-xs">{getPriorityScore(task.priority_score)}</td>
                  <td className="px-4 py-3 text-slate-700 text-xs">{task.duration_hours}h</td>
                  <td className="px-4 py-3">
                    {task.due_date ? (
                      <span className={`text-xs ${task.overdue ? 'text-red-400' : 'text-slate-500'}`}>
                        {task.overdue && '⚠ '}{formatDate(task.due_date)}
                      </span>
                    ) : <span className="text-slate-600 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[task.status] || 'bg-[#e4e9f0] text-slate-700'}`}>
                      {task.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="fixed right-0 top-0 h-screen w-96 bg-[#eef2f7] border-l border-slate-200 overflow-y-auto z-30">
          <div className="sticky top-0 bg-[#eef2f7] border-b border-slate-200 p-4 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900">{selected.task_id}</h3>
              <p className="text-xs text-slate-500">{selected.task_type}</p>
            </div>
            <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-slate-900">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 space-y-5">
            {/* Priority */}
            <div>
              <p className="section-tag"><AlertTriangle className="w-3 h-3" /> Priority Analysis</p>
              <div className="flex items-center gap-3 mb-3">
                <span className={`text-sm font-bold px-3 py-1 rounded border ${PRIORITY_COLORS[selected.priority_category || 'LOW']}`}>
                  {selected.priority_category || 'LOW'}
                </span>
                <span className="text-2xl font-black text-slate-900">{getPriorityScore(selected.priority_score)}<span className="text-sm text-slate-500">/100</span></span>
              </div>
              <div className="space-y-2 bg-white/50 rounded-lg p-3">
                <ScoreBar label="Criticality" value={selected.criticality} />
                <ScoreBar label="Urgency" value={selected.urgency} />
                <ScoreBar label="Safety Risk" value={selected.safety_risk} />
                <ScoreBar label="Asset Importance" value={selected.asset_importance} />
                {selected.overdue && (
                  <div className="mt-2 text-xs text-red-400 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Task is OVERDUE — priority boosted
                  </div>
                )}
              </div>
              {selected.score_breakdown && (
                <div className="mt-3 bg-white/50 rounded-lg p-3 space-y-1.5">
                  <p className="text-xs text-slate-500 mb-2">Weighted score contributions</p>
                  {[
                    ['Criticality', selected.score_breakdown.criticality_contribution],
                    ['Urgency', selected.score_breakdown.urgency_contribution],
                    ['Safety', selected.score_breakdown.safety_risk_contribution],
                    ['Asset importance', selected.score_breakdown.asset_importance_contribution],
                    ['Overdue', selected.score_breakdown.overdue_contribution],
                  ].map(([label, value]) => (
                    <div key={label as string} className="flex justify-between text-xs">
                      <span className="text-slate-500">{label}</span>
                      <span className="text-slate-700 font-mono">{((value as number) * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
              {selected.priority_explanation && <p className="text-xs text-slate-500 mt-2">{selected.priority_explanation}</p>}
            </div>

            {selected.ml_model_available && selected.ml_risk_probability != null && (
              <div className="border border-blue-200 bg-blue-50/60 rounded-lg p-3">
                <p className="section-tag">AI Delay Risk</p>
                <div className="flex items-end justify-between mb-3">
                  <span className="text-2xl font-black text-slate-900">{(selected.ml_risk_probability * 100).toFixed(0)}%</span>
                  <span className="text-xs font-bold text-blue-700">{selected.ml_risk_category}</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">Existing Priority</span><span className="font-mono text-slate-800">{(selected.existing_priority_score ?? selected.priority_score ?? 0).toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">ML Risk</span><span className="font-mono text-slate-800">{selected.ml_risk_probability.toFixed(2)}</span></div>
                  <div className="flex justify-between font-semibold"><span className="text-slate-700">Planning Score</span><span className="font-mono text-slate-900">{(selected.final_planning_score ?? selected.priority_score ?? 0).toFixed(2)}</span></div>
                </div>
                {selected.ml_risk_explanation && <p className="text-xs text-slate-500 mt-3">{selected.ml_risk_explanation}</p>}
              </div>
            )}

            {/* Task Info */}
            <div>
              <p className="section-tag">Task Details</p>
              <div className="space-y-2 text-sm">
                {[
                  ['Department', selected.department],
                  ['Asset Type', selected.asset_type],
                  ['Asset Name', selected.asset_name],
                  ['Corridor', selected.corridor_id],
                  ['Location', selected.location],
                  ['Duration', `${selected.duration_hours} hours`],
                  ['Due Date', selected.due_date ? formatDate(selected.due_date) : '—'],
                  ['Status', selected.status],
                ].map(([k, v]) => (
                  <div key={k} className="flex gap-2">
                    <span className="text-slate-500 w-32 flex-shrink-0">{k}</span>
                    <span className="text-slate-700">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Description */}
            {selected.description && (
              <div>
                <p className="section-tag">Description</p>
                <p className="text-sm text-slate-700 bg-white/50 rounded-lg p-3">{selected.description}</p>
              </div>
            )}

            {/* Compatible depts */}
            {selected.compatible_departments && selected.compatible_departments.length > 0 && (
              <div>
                <p className="section-tag">Compatible With</p>
                <div className="flex flex-wrap gap-2">
                  {selected.compatible_departments.map(d => (
                    <span key={d} className={`text-xs px-2 py-0.5 rounded border ${DEPT_BADGE[d] || 'bg-[#e4e9f0] text-slate-700'}`}>
                      {d === 'Traction Distribution' ? 'TRD' : d}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-slate-500 mt-2">This task can be grouped with the above departments in a shared maintenance block.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

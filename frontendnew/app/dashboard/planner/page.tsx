'use client';
import { useState, useEffect } from 'react';
import { blocks, trains as trainsApi, GeneratePlanResponse, OptimizedBlock, Corridor } from '@/lib/api';
import { Zap, X, CheckCircle2, AlertTriangle, Clock, Layers, RotateCcw, ChevronDown } from 'lucide-react';
import { DEPT_BADGE, formatTime, formatDate } from '@/lib/utils';

const HORIZON_OPTS = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
];

const BLOCK_COLORS_BY_DEPT: Record<string, string> = {
  'Engineering': '#3b82f6',
  'S&T': '#22c55e',
  'Traction Distribution': '#f59e0b',
};
const MULTI_DEPT_COLOR = '#8b5cf6';

function getBlockColor(block: OptimizedBlock): string {
  if ((block.departments_involved || []).length > 1) return MULTI_DEPT_COLOR;
  const dept = (block.departments_involved || [])[0];
  return BLOCK_COLORS_BY_DEPT[dept] || '#64748b';
}

function BlockModal({ block, onClose, onSimulate }: { block: OptimizedBlock; onClose: () => void; onSimulate: (id: string) => void }) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#eef2f7] border border-slate-200 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="p-5 border-b border-slate-200 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-slate-500 bg-white px-2 py-0.5 rounded">{block.block_id}</span>
              {block.has_critical && <span className="text-xs bg-red-900/50 text-red-400 border border-red-200/50 px-2 py-0.5 rounded">CRITICAL</span>}
              {block.multi_department && <span className="text-xs bg-purple-900/50 text-purple-400 border border-purple-700/50 px-2 py-0.5 rounded">MULTI-DEPT</span>}
            </div>
            <h3 className="text-lg font-bold text-slate-900">Corridor {block.corridor_id}</h3>
            <p className="text-slate-500 text-sm">{formatDate(block.date)} · {formatTime(block.start_time)} – {formatTime(block.end_time)}</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900 mt-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Tasks */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Tasks in this block</p>
            <div className="space-y-1.5">
              {(block.tasks || []).map((task: any) => (
                <div key={task.task_id} className="flex items-start gap-2.5 bg-white rounded-lg px-3 py-2">
                  <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-slate-900">{task.task_type}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-xs px-1.5 py-0.5 rounded border ${DEPT_BADGE[task.department] || ''}`}>
                        {task.department === 'Traction Distribution' ? 'TRD' : task.department}
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded border ${task.priority_category === 'CRITICAL' ? 'text-red-500 border-red-200' : task.priority_category === 'HIGH' ? 'text-orange-500 border-orange-200' : 'text-slate-500 border-slate-200'}`}>
                        {task.priority_category || 'Priority unavailable'}
                      </span>
                      <span className="text-xs text-slate-500">{task.duration_hours}h</span>
                    </div>
                  </div>
                </div>
              ))}
              {(!block.tasks || block.tasks.length === 0) && (
                <p className="text-xs text-slate-500">{block.tasks_completed} task(s) scheduled</p>
              )}
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Duration', value: `${block.duration_hours}h`, icon: Clock },
              { label: 'Train Conflicts', value: block.train_conflicts ?? 0, icon: AlertTriangle },
              { label: 'Utilization', value: `${((block.utilization ?? 0) * 100).toFixed(1)}%`, icon: Layers },
              { label: 'Opt. Score', value: block.optimization_score == null ? '—' : `${block.optimization_score}/100`, icon: Zap },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="bg-white rounded-lg p-3 text-center">
                <Icon className="w-4 h-4 text-slate-500 mx-auto mb-1" />
                <p className="text-slate-900 font-bold text-sm">{value}</p>
                <p className="text-xs text-slate-500">{label}</p>
              </div>
            ))}
          </div>

          {/* Departments */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Departments</p>
            <div className="flex flex-wrap gap-2">
              {(block.departments_involved || []).map(d => (
                <span key={d} className={`text-xs px-2 py-1 rounded border ${DEPT_BADGE[d] || ''}`}>
                  {d === 'Traction Distribution' ? 'Traction Distribution' : d}
                </span>
              ))}
            </div>
          </div>

          {/* Why this block */}
          {block.explanation && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Zap className="w-3 h-3 text-amber-400" /> Why this block?
              </p>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans">{block.explanation}</pre>
              </div>
            </div>
          )}

          {/* Simulate conflict */}
          <button
            onClick={() => { onSimulate(block.block_id); onClose(); }}
            className="w-full flex items-center justify-center gap-2 bg-white hover:bg-red-50 border border-slate-200 hover:border-red-200 text-slate-700 hover:text-red-400 py-2.5 rounded-lg text-sm transition"
          >
            <AlertTriangle className="w-4 h-4" />
            Simulate Train Conflict on This Block
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PlannerPage() {
  const [horizon, setHorizon] = useState('week');
  const [corridorFilter, setCorridorFilter] = useState('');
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [plan, setPlan] = useState<GeneratePlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState<OptimizedBlock | null>(null);
  const [simResult, setSimResult] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);
  const [existingBlocks, setExistingBlocks] = useState<OptimizedBlock[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([trainsApi.getCorridors(), blocks.getOptimized()])
      .then(([corridorResult, blockResult]) => {
        setCorridors(corridorResult.corridors);
        setExistingBlocks(blockResult.blocks);
      })
      .catch((error: any) => setLoadError(error?.message || 'Unable to load planner data'));
  }, []);

  async function generate() {
    setLoading(true);
    setSimResult(null);
    setGenerateError(null);
    try {
      const res = await blocks.generatePlan({
        planning_horizon: horizon,
        corridor_id: corridorFilter || undefined,
      });
      setPlan(res);
      setExistingBlocks(res.blocks);
    } catch (e: any) {
      setGenerateError(e?.message || 'Unable to generate block plan');
    } finally {
      setLoading(false);
    }
  }

  async function simulate(blockId: string) {
    setSimulating(true);
    try {
      const res = await blocks.simulateScenario(blockId);
      setSimResult(res);
      if (plan) {
        // Refresh blocks
        const fresh = await blocks.getOptimized();
        setExistingBlocks(fresh.blocks);
      }
    } catch (e: any) {
      setGenerateError(e?.message || 'Unable to simulate conflict');
    } finally {
      setSimulating(false);
    }
  }

  // Group blocks by date for timeline view
  const blocksByDate: Record<string, OptimizedBlock[]> = {};
  (existingBlocks || []).forEach(b => {
    if (!blocksByDate[b.date]) blocksByDate[b.date] = [];
    blocksByDate[b.date].push(b);
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Block Planner</h2>
        <p className="text-slate-500 text-sm mt-0.5">Constraint-optimized maintenance block scheduling using OR-Tools CP-SAT solver</p>
      </div>

      {loadError && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center justify-between"><span>{loadError}</span><button onClick={() => window.location.reload()} className="underline">Retry</button></div>}
      {generateError && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{generateError}</div>}

      {/* Controls */}
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <div className="flex items-center gap-4 flex-wrap">
          <div>
            <label className="text-xs text-slate-500 block mb-1.5">Planning Horizon</label>
            <div className="flex gap-2">
              {HORIZON_OPTS.map(o => (
                <button
                  key={o.value}
                  onClick={() => setHorizon(o.value)}
                  className={`px-4 py-2 rounded-lg text-sm transition ${horizon === o.value ? 'bg-red-600 text-slate-900' : 'bg-[#e4e9f0] text-slate-700 hover:bg-[#d8dee7]'}`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-500 block mb-1.5">Filter Corridor</label>
            <select
              value={corridorFilter}
              onChange={e => setCorridorFilter(e.target.value)}
              className="bg-[#e4e9f0] border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none"
            >
              <option value="">All Corridors</option>
              {corridors.map(c => <option key={c.corridor_id} value={c.corridor_id}>{c.corridor_name}</option>)}
            </select>
          </div>

          <div className="ml-auto">
            <button
              onClick={generate}
              disabled={loading}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-2.5 rounded-lg text-slate-900 font-semibold text-sm transition"
            >
              <Zap className="w-4 h-4" />
              {loading ? 'Optimizing...' : 'GENERATE OPTIMIZED BLOCK PLAN'}
            </button>
          </div>
        </div>

        {loading && (
          <div className="mt-4 bg-[#e8edf3] border border-slate-200 rounded-lg p-4">
            <div className="flex items-center gap-3 text-sm text-slate-700">
              <div className="animate-spin w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full" />
              Running optimization pipeline...
            </div>
            <div className="mt-2 space-y-1 text-xs text-slate-500">
              <p>① Fetching maintenance tasks and calculating priority scores...</p>
              <p>② Identifying compatible task groups across departments...</p>
              <p>③ Running OR-Tools CP-SAT optimizer...</p>
              <p>④ Generating baseline vs optimized comparison...</p>
            </div>
          </div>
        )}
      </div>

      {plan?.unscheduled_tasks && plan.unscheduled_tasks.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-3">Unscheduled Tasks ({plan.unscheduled_tasks.length})</h3>
          <div className="space-y-2 max-h-56 overflow-auto">
            {plan.unscheduled_tasks.map(task => (
              <div key={task.task_id} className="flex items-center gap-3 text-xs bg-white/70 rounded-lg px-3 py-2">
                <span className="font-mono text-slate-700">{task.task_id}</span>
                <span className="text-slate-500">{task.corridor_id}</span>
                <span className="text-slate-600 flex-1">{task.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simulation Result */}
      {simResult && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            Conflict Simulation Result
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-red-50 border border-red-200/40 rounded-lg p-4">
              <p className="text-xs text-red-400 font-semibold mb-2">⚠ ORIGINAL PLAN — CONFLICT DETECTED</p>
              <p className="text-slate-900 font-mono">{formatTime(simResult.original_block.start_time)}–{formatTime(simResult.original_block.end_time)}</p>
              <p className="text-slate-500 text-xs mt-1">Corridor {simResult.original_block.corridor_id}</p>
              <p className="text-red-400 text-xs mt-2">Unexpected train scheduled during maintenance window</p>
            </div>
            <div className="bg-green-50 border border-green-200/40 rounded-lg p-4">
              <p className="text-xs text-green-400 font-semibold mb-2">✓ GATIMAAN RESCHEDULED</p>
              <p className="text-slate-900 font-mono">{formatTime(simResult.rescheduled_block.start_time)}–{formatTime(simResult.rescheduled_block.end_time)}</p>
              <p className="text-slate-500 text-xs mt-1">Corridor {simResult.rescheduled_block.corridor_id}</p>
              <p className="text-green-400 text-xs mt-2">Conflict resolved — all tasks rescheduled</p>
            </div>
          </div>
          <button onClick={() => setSimResult(null)} className="mt-3 text-xs text-slate-500 hover:text-slate-700">Dismiss</button>
        </div>
      )}

      {/* Metrics */}
      {plan && (
        <div className="grid grid-cols-4 gap-4">
          {[
              { label: 'Tasks Scheduled', value: plan.metrics.tasks_scheduled ?? 0, sub: `of ${plan.metrics.total_tasks ?? 0} total` },
            { label: 'Optimized Blocks', value: plan.metrics.separate_blocks ?? plan.blocks.length, sub: 'generated' },
            { label: 'Block Hours', value: `${(plan.metrics.total_block_hours ?? 0).toFixed(1)}h`, sub: 'total duration' },
            { label: 'Multi-Dept Blocks', value: plan.metrics.multi_department_blocks ?? 0, sub: 'cross-dept coordination' },
          ].map(m => (
            <div key={m.label} className="bg-white border border-slate-200 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-slate-900">{m.value}</p>
              <p className="text-sm text-slate-500 mt-1">{m.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{m.sub}</p>
            </div>
          ))}
        </div>
      )}

      {/* Block Timeline */}
      {Object.keys(blocksByDate).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Layers className="w-4 h-4" /> Maintenance Block Timeline
          </h3>

          {Object.entries(blocksByDate).sort(([a], [b]) => a.localeCompare(b)).map(([date, dayBlocks]) => (
            <div key={date} className="bg-white border border-slate-200 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">{formatDate(date)}</h4>

              {/* Corridor rows */}
              {Array.from(new Set(dayBlocks.map(b => b.corridor_id))).map(cid => {
                const corridorBlocks = dayBlocks.filter(b => b.corridor_id === cid);
                return (
                  <div key={cid} className="mb-4 last:mb-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs text-slate-500 font-mono w-24">{cid}</span>
                      <div className="flex-1 h-px bg-[#e4e9f0]" />
                    </div>

                    {/* Timeline bar */}
                    <div className="relative ml-24 h-14 bg-[#e8edf3] rounded-lg overflow-hidden">
                      {/* Time markers */}
                      {[0, 6, 12, 18, 23].map(h => (
                        <div key={h} className="absolute top-0 h-full border-l border-slate-200 flex flex-col justify-end pb-1" style={{ left: `${(h / 24) * 100}%` }}>
                          <span className="text-[9px] text-slate-600 pl-0.5">{String(h).padStart(2, '0')}:00</span>
                        </div>
                      ))}

                      {/* Block bars */}
                      {corridorBlocks.map(b => {
                        const startH = parseInt(b.start_time.split(':')[0]) + parseInt(b.start_time.split(':')[1]) / 60;
                        const endH = parseInt(b.end_time.split(':')[0]) + parseInt(b.end_time.split(':')[1]) / 60;
                        const left = (startH / 24) * 100;
                        const width = ((endH - startH) / 24) * 100;
                        const color = getBlockColor(b);

                        return (
                          <div
                            key={b.block_id}
                            onClick={() => setSelectedBlock(b)}
                            className="absolute top-1 h-10 rounded cursor-pointer flex items-center px-2 text-slate-900 text-xs font-semibold hover:brightness-125 transition shadow-lg"
                            style={{ left: `${left}%`, width: `${width}%`, background: color, minWidth: '2px' }}
                            title={`${b.block_id} — Click for details`}
                          >
                            <div className="truncate">
                              <span className="text-[10px]">{formatTime(b.start_time)}–{formatTime(b.end_time)}</span>
                              <br />
                              <span className="text-[10px] opacity-80">{b.tasks_completed ?? 0}t · {b.departments_involved?.length || 0}d · {((b.utilization ?? 0) * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>Legend:</span>
            {Object.entries(BLOCK_COLORS_BY_DEPT).map(([dept, color]) => (
              <span key={dept} className="flex items-center gap-1">
                <span className="w-3 h-3 rounded" style={{ background: color }} />
                {dept === 'Traction Distribution' ? 'TRD' : dept}
              </span>
            ))}
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-purple-500" />
              Multi-Department
            </span>
          </div>
        </div>
      )}

      {/* Before vs After */}
      {plan?.improvement && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-sm font-semibold text-slate-700">Before vs After Comparison</h3>
            <span className="text-xs bg-amber-800/40 text-amber-400 border border-amber-200 px-2 py-0.5 rounded">SIMULATED SCENARIO</span>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Block Hours', before: plan.improvement.baseline_block_hours + 'h', after: plan.improvement.optimized_block_hours + 'h', saved: plan.improvement.hours_saved + 'h saved' },
              { label: 'Separate Blocks', before: plan.improvement.baseline_blocks, after: plan.improvement.optimized_blocks_count, saved: plan.improvement.blocks_reduced + ' reduced' },
              { label: 'Train Conflicts', before: plan.improvement.baseline_conflicts, after: plan.improvement.optimized_conflicts, saved: plan.improvement.conflict_reduction + ' fewer' },
            ].map(m => (
              <div key={m.label} className="bg-[#e8edf3] rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-3">{m.label}</p>
                <div className="flex items-center gap-3">
                  <div className="text-center">
                    <p className="text-xs text-slate-500 mb-1">BEFORE</p>
                    <p className="text-lg font-bold text-red-400 line-through opacity-70">{m.before}</p>
                  </div>
                  <div className="text-slate-500">→</div>
                  <div className="text-center">
                    <p className="text-xs text-slate-500 mb-1">GATIMAAN</p>
                    <p className="text-lg font-bold text-green-400">{m.after}</p>
                  </div>
                </div>
                <p className="text-xs text-amber-400 mt-2 text-center">{m.saved}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3 text-center">{plan.improvement.note}</p>
        </div>
      )}

      {/* Block Detail Modal */}
      {selectedBlock && (
        <BlockModal
          block={selectedBlock}
          onClose={() => setSelectedBlock(null)}
          onSimulate={simulate}
        />
      )}
    </div>
  );
}

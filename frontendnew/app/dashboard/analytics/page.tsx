'use client';
import { useEffect, useState } from 'react';
import { analytics, AnalyticsResponse } from '@/lib/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, CartesianGrid
} from 'recharts';
import { RefreshCw } from 'lucide-react';

const COLORS = ['#dc2626', '#ea580c', '#ca8a04', '#64748b'];
const DEPT_COLORS = ['#3b82f6', '#22c55e', '#f59e0b'];

function MetricCompare({ label, before, after, unit = '', lower_is_better = true }: any) {
  if (before == null || after == null) {
    return <div className="bg-[#e8edf3] border border-slate-200 rounded-xl p-4"><p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{label}</p><p className="text-sm text-slate-500">Not available yet</p></div>;
  }
  const diff = after - before;
  const improved = lower_is_better ? diff < 0 : diff > 0;
  const pct = before !== 0 ? Math.abs((diff / before) * 100).toFixed(1) : '0';
  return (
    <div className="bg-[#e8edf3] border border-slate-200 rounded-xl p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{label}</p>
      <div className="flex items-end gap-4">
        <div>
          <p className="text-xs text-slate-500 mb-1">BEFORE</p>
          <p className="text-2xl font-bold text-slate-500 line-through">{before}{unit}</p>
        </div>
        <div className="text-slate-600 pb-1">→</div>
        <div>
          <p className="text-xs text-slate-500 mb-1">GATIMAAN</p>
          <p className="text-2xl font-bold text-slate-900">{after}{unit}</p>
        </div>
      </div>
      <div className={`mt-2 text-xs font-semibold ${improved ? 'text-green-400' : 'text-slate-500'}`}>
        {improved ? '▲' : '▼'} {pct}% {improved ? 'improvement' : 'change'}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAnalytics() {
    setLoading(true); setError(null);
    try { setData(await analytics.get()); }
    catch (e: any) { setError(e?.message || 'Unable to load analytics'); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadAnalytics(); }, []);

  if (loading) return <div className="flex items-center justify-center h-96 text-slate-500">Loading analytics...</div>;
  if (error) return <div className="p-6"><div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-700"><p>Unable to load analytics</p><p className="mt-1">{error}</p><button onClick={loadAnalytics} className="mt-3 inline-flex items-center gap-2 underline"><RefreshCw className="w-4 h-4" /> Retry</button></div></div>;
  if (!data) return <div className="p-6 text-slate-500">No analytics data available.</div>;

  const { summary: s, comparison: c, priority_distribution: pd, department_distribution: dd, weekly_trend: wt } = data;

  const deptData = dd ? Object.entries(dd).map(([name, value], i) => ({ name: name === 'Traction Distribution' ? 'TRD' : name, value, fill: DEPT_COLORS[i] })) : [];
  const priorityData = pd ? [
    { name: 'Critical', value: pd.CRITICAL, fill: COLORS[0] },
    { name: 'High', value: pd.HIGH, fill: COLORS[1] },
    { name: 'Medium', value: pd.MEDIUM, fill: COLORS[2] },
    { name: 'Low', value: pd.LOW, fill: COLORS[3] },
  ] : [];

  const conflictData = [
    { name: 'Before', conflicts: c?.baseline_conflicts || 0 },
    { name: 'Gatimaan', conflicts: c?.optimized_conflicts || 0 },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Impact & Analytics</h2>
        <p className="text-slate-500 text-sm mt-0.5">Computed planning metrics and independent departmental baseline</p>
        <span className="inline-block mt-1 text-xs bg-amber-800/40 text-amber-400 border border-amber-200 px-2 py-0.5 rounded">
          SIMULATED PROTOTYPE DATA — Not real Indian Railways statistics
        </span>
      </div>

      {/* Before vs After */}
      {c && (
        <div>
          <h3 className="text-sm font-semibold text-slate-500 mb-3">Key Performance Comparison</h3>
          <div className="grid grid-cols-3 gap-4">
            <MetricCompare label="Total Block Hours" before={c?.baseline_block_hours} after={c?.optimized_block_hours} unit="h" lower_is_better />
            <MetricCompare label="Separate Blocks" before={c?.baseline_blocks} after={c?.optimized_blocks} lower_is_better />
            <MetricCompare label="Train Conflicts" before={c?.baseline_conflicts} after={c?.optimized_conflicts} lower_is_better />
          </div>
          <p className="text-xs text-slate-500 mt-2">{c.note}</p>
        </div>
      )}

      {/* Charts row 1 */}
      <div className="grid grid-cols-3 gap-4">
        {/* Priority Pie */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={priorityData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                {priorityData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Dept Workload */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Department Workload</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={deptData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="value" name="Tasks" radius={[4, 4, 0, 0]}>
                {deptData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Conflict Reduction */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Train Conflict Reduction</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={conflictData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="conflicts" name="Conflicts" fill="#dc2626" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weekly Trend */}
      {wt && wt.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Weekly Maintenance Trend</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={wt}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              <Line type="monotone" dataKey="blocks" name="Blocks" stroke="#dc2626" strokeWidth={2.5} dot={{ r: 4, fill: '#dc2626' }} />
              <Line type="monotone" dataKey="tasks" name="Tasks" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: '#3b82f6' }} strokeDasharray="5 5" />
              <Line type="monotone" dataKey="hours" name="Hours" stroke="#22c55e" strokeWidth={2} dot={{ r: 3, fill: '#22c55e' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Summary Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Full Impact Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 uppercase border-b border-slate-200">
                <th className="pb-2 text-left">Metric</th>
                <th className="pb-2 text-right">Before (Simulated)</th>
                <th className="pb-2 text-right">Gatimaan</th>
                <th className="pb-2 text-right">Change</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-700">
              {[
                { metric: 'Total Block Hours', before: c?.baseline_block_hours == null ? '—' : `${c.baseline_block_hours}h`, after: c?.optimized_block_hours == null ? '—' : `${c.optimized_block_hours}h`, change: c?.baseline_block_hours == null ? '—' : `${((c.baseline_block_hours || 0) - (c.optimized_block_hours || 0)).toFixed(1)}h`, good: true },
                { metric: 'Separate Blocks', before: c?.baseline_blocks ?? '—', after: c?.optimized_blocks ?? '—', change: c?.baseline_blocks == null ? '—' : `${(c.baseline_blocks || 0) - (c.optimized_blocks || 0)}`, good: true },
                { metric: 'Train Conflicts', before: c?.baseline_conflicts ?? '—', after: c?.optimized_conflicts ?? '—', change: c?.baseline_conflicts == null ? '—' : `${(c.baseline_conflicts || 0) - (c.optimized_conflicts || 0)}`, good: true },
                { metric: 'Tasks Scheduled', before: c?.baseline_tasks_scheduled ?? '—', after: c?.optimized_tasks_scheduled ?? (s?.scheduled || 0), change: '—', good: true },
                { metric: 'Asset Availability', before: '—', after: 'Not measurable', change: 'Historical state data required', good: false },
              ].map(row => (
                <tr key={row.metric}>
                  <td className="py-3">{row.metric}</td>
                  <td className="py-3 text-right text-slate-500">{row.before}</td>
                  <td className="py-3 text-right text-slate-900 font-semibold">{row.after}</td>
                  <td className={`py-3 text-right font-semibold ${row.good ? 'text-green-400' : 'text-red-400'}`}>{row.change}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500 mt-3">Planning metrics are calculated from the current synthetic/imported dataset. Asset availability remains unavailable without historical asset-state data.</p>
      </div>
    </div>
  );
}

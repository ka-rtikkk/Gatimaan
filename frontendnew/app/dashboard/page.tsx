'use client';
import { useEffect, useState } from 'react';
import { analytics, blocks, importData, AnalyticsResponse, OptimizedBlock } from '@/lib/api';
import {
  AlertTriangle, Clock, Zap, Activity, TrendingUp,
  RefreshCw, Database, ChevronRight, CheckCircle2, AlertCircle
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import Link from 'next/link';
import { PRIORITY_DOT, formatTime, formatDate } from '@/lib/utils';

const COLORS = ['#dc2626', '#ea580c', '#ca8a04', '#64748b'];
const DEPT_COLORS_CHART = ['#3b82f6', '#22c55e', '#f59e0b'];

function KpiCard({ icon: Icon, label, value, sub, color = 'blue' }: any) {
  const colorMap: Record<string, string> = {
    red: 'text-red-400 bg-red-50 border-red-200/30',
    blue: 'text-blue-400 bg-blue-900/20 border-blue-700/30',
    amber: 'text-amber-400 bg-amber-50 border-amber-200',
    green: 'text-green-400 bg-green-50 border-green-200/30',
    purple: 'text-purple-400 bg-purple-900/20 border-purple-700/30',
  };
  return (
    <div className="kpi-card flex items-start gap-4">
      <div className={`p-2.5 rounded-lg border ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [recentBlocks, setRecentBlocks] = useState<OptimizedBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [partialError, setPartialError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    setPartialError(null);
    try {
      const [analyticsResult, blocksResult] = await Promise.allSettled([
        analytics.get(),
        blocks.getOptimized({ date_from: new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0] }),
      ]);
      if (analyticsResult.status === 'fulfilled') setData(analyticsResult.value);
      if (blocksResult.status === 'fulfilled') setRecentBlocks(blocksResult.value.blocks.slice(0, 5));
      const failures = [analyticsResult, blocksResult]
        .filter((result): result is PromiseRejectedResult => result.status === 'rejected')
        .map(result => result.reason?.message || 'A dashboard data source is unavailable');
      if (failures.length === 2) throw new Error(failures.join(' '));
      if (failures.length === 1) setPartialError(failures[0]);
    } catch (e: any) {
      setError(e?.message || 'Unable to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  async function handleSeed() {
    setSeeding(true);
    setSeedMsg('');
    try {
      const res = await importData.loadDemo();
      setSeedMsg(`✓ Loaded: ${res.results.tasks} tasks, ${res.results.trains} trains, ${res.results.windows} windows`);
      await load();
    } catch (e: any) {
      setSeedMsg('Error: ' + e.message);
    }
    setSeeding(false);
  }

  const s = data?.summary;
  const dist = data?.priority_distribution;
  const deptData = data?.department_distribution
    ? Object.entries(data.department_distribution).map(([name, value]) => ({ name, value }))
    : [];
  const weeklyData = data?.weekly_trend || [];
  const pieData = dist
    ? [
        { name: 'Critical', value: dist.CRITICAL },
        { name: 'High', value: dist.HIGH },
        { name: 'Medium', value: dist.MEDIUM },
        { name: 'Low', value: dist.LOW },
      ]
    : [];

  const aiRecommendations = recentBlocks
    .filter(b => (b.departments_involved || []).length > 1)
    .slice(0, 3)
    .map(b => ({
      text: `${(b.departments_involved || []).length} compatible tasks on Corridor ${b.corridor_id} can be combined into a single ${formatTime(b.start_time)}–${formatTime(b.end_time)} block, avoiding separate maintenance windows.`,
      score: b.optimization_score,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-500 animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-2xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <h2 className="font-semibold text-slate-900">Unable to load dashboard data</h2>
              <p className="text-sm text-slate-600 mt-1">{error}</p>
              <button onClick={load} className="mt-4 inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm text-white">
                <RefreshCw className="w-4 h-4" /> Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">System Overview</h2>
          <p className="text-slate-500 text-sm mt-0.5">Railway Maintenance Block Planning Dashboard</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-2 bg-[#e4e9f0] hover:bg-[#d8dee7] px-4 py-2 rounded-lg text-sm text-slate-900 transition disabled:opacity-50"
          >
            <Database className="w-4 h-4" />
            {seeding ? 'Loading...' : 'Load Demo Data'}
          </button>
          <Link
            href="/dashboard/planner"
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm text-slate-900 transition"
          >
            <Zap className="w-4 h-4" />
            Generate Optimized Plan
          </Link>
        </div>
      </div>

      {seedMsg && (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2.5 text-green-300 text-sm">
          {seedMsg}
        </div>
      )}
      {partialError && <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 text-amber-700 text-sm">Some dashboard data is unavailable: {partialError}</div>}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard icon={AlertTriangle} label="Critical Tasks" value={dist?.CRITICAL || 0} color="red" sub="Immediate action needed" />
        <KpiCard icon={Clock} label="Pending Tasks" value={s?.pending || 0} color="amber" sub={`${s?.overdue || 0} overdue`} />
        <KpiCard icon={Activity} label="Planned Blocks" value={s?.total_blocks || 0} color="blue" sub="Optimized blocks" />
        <KpiCard icon={Zap} label="Block Hours" value={s?.total_block_hours?.toFixed(1) || 0} color="purple" sub="Total scheduled" />
        <KpiCard icon={TrendingUp} label="Multi-Dept Blocks" value={s?.multi_dept_blocks || 0} color="green" sub="Actual coordinated blocks" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Priority Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={3}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {['Critical', 'High', 'Medium', 'Low'].map((l, i) => (
              <span key={l} className="flex items-center gap-1 text-xs text-slate-500">
                <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i] }} />{l}
              </span>
            ))}
          </div>
        </div>

        {/* Department Workload */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Department Workload</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={deptData} layout="vertical">
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" width={80} tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => v === 'Traction Distribution' ? 'TRD' : v} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Trend */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Weekly Block Trend</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={weeklyData}>
              <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis hide />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Line type="monotone" dataKey="blocks" stroke="#dc2626" strokeWidth={2} dot={{ r: 3, fill: '#dc2626' }} />
              <Line type="monotone" dataKey="tasks" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: '#3b82f6' }} strokeDasharray="4 4" />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-2 gap-4">
        {/* AI Recommendations */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-700">Gatimaan Optimization Recommendations</h3>
          </div>
          {aiRecommendations.length === 0 ? (
            <div className="text-slate-500 text-sm text-center py-6">
              <p>No optimized blocks yet.</p>
              <Link href="/dashboard/planner" className="text-red-400 hover:underline mt-1 inline-block">Generate Optimized Block Plan →</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {aiRecommendations.map((r, i) => (
                <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-slate-700">{r.text}</p>
                  </div>
                  {r.score && (
                    <div className="mt-2 flex items-center gap-1">
                      <span className="text-xs text-slate-500">Score:</span>
                      <span className="text-xs text-amber-400 font-semibold">{r.score}/100</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Blocks */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-700">Upcoming Maintenance Blocks</h3>
            <Link href="/dashboard/planner" className="text-xs text-red-400 hover:underline flex items-center gap-1">
              View all <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          {recentBlocks.length === 0 ? (
            <div className="text-slate-500 text-sm text-center py-6">No blocks planned yet</div>
          ) : (
            <div className="space-y-2">
              {recentBlocks.map(b => (
                <div key={b.block_id} className="flex items-center justify-between bg-[#e8edf3] rounded-lg px-3 py-2.5">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${b.has_critical ? 'bg-red-500 pulse-red' : 'bg-blue-500'}`} />
                    <div>
                      <p className="text-sm text-slate-900 font-medium">{b.corridor_id}</p>
                      <p className="text-xs text-slate-500">{formatDate(b.date)} · {formatTime(b.start_time)}–{formatTime(b.end_time)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">{b.tasks_completed} tasks</p>
                    <p className="text-xs text-slate-500">{b.duration_hours}h</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Baseline vs Optimized */}
      {data?.comparison && s?.total_blocks! > 0 && (
        <div className="bg-gradient-to-r from-slate-800/60 to-slate-800/40 border border-slate-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <h3 className="text-sm font-semibold text-slate-700">Optimization Impact (Simulated Scenario)</h3>
            <span className="text-xs bg-amber-800/40 text-amber-400 px-2 py-0.5 rounded">PROTOTYPE VALUES</span>
          </div>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Block Hours Saved', before: data.comparison.baseline_block_hours, after: data.comparison.optimized_block_hours, unit: 'h' },
              { label: 'Separate Blocks', before: data.comparison.baseline_blocks, after: data.comparison.optimized_blocks, unit: '' },
              { label: 'Train Conflicts', before: data.comparison.baseline_conflicts, after: data.comparison.optimized_conflicts, unit: '' },
              { label: 'Improvement', before: null, after: `${data.comparison.improvement_percentage}%`, unit: '' },
            ].map((m, i) => (
              <div key={i} className="bg-[#e8edf3] rounded-lg p-3 text-center">
                <p className="text-xs text-slate-500 mb-2">{m.label}</p>
                {m.before !== null && (
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <span className="text-slate-500 text-sm line-through">{m.before}{m.unit}</span>
                    <span className="text-green-400">→</span>
                    <span className="text-slate-900 font-bold">{m.after}{m.unit}</span>
                  </div>
                )}
                {m.before === null && (
                  <p className="text-2xl font-bold text-green-400">{m.after}</p>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3">{data.comparison.note}</p>
        </div>
      )}
    </div>
  );
}

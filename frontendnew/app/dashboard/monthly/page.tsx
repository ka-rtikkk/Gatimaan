'use client';
import { useEffect, useState } from 'react';
import { analytics, blocks, AnalyticsResponse, OptimizedBlock } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

function getMonthDates(year: number, month: number): (Date | null)[] {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startPad = firstDay === 0 ? 6 : firstDay - 1;
  const dates: (Date | null)[] = Array(startPad).fill(null);
  for (let d = 1; d <= daysInMonth; d++) dates.push(new Date(year, month, d));
  return dates;
}

export default function MonthlyPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [analyticsData, setAnalyticsData] = useState<AnalyticsResponse | null>(null);
  const [allBlocks, setAllBlocks] = useState<OptimizedBlock[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<Date[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadMonth() {
    const from = new Date(year, month, 1).toISOString().split('T')[0];
    const to = new Date(year, month + 1, 0).toISOString().split('T')[0];
    setLoading(true); setError(null);
    try {
      const [a, b] = await Promise.all([
        analytics.get(),
        blocks.getOptimized({ date_from: from, date_to: to }),
      ]);
      setAnalyticsData(a);
      setAllBlocks(b.blocks);
    } catch (e: any) { setError(e?.message || 'Unable to load monthly plan'); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadMonth(); }, [year, month]);

  const monthDates = getMonthDates(year, month);
  const monthName = new Date(year, month).toLocaleString('default', { month: 'long', year: 'numeric' });
  const s = analyticsData?.summary;

  function prevMonth() {
    if (month === 0) { setYear(y => y - 1); setMonth(11); } else setMonth(m => m - 1);
  }
  function nextMonth() {
    if (month === 11) { setYear(y => y + 1); setMonth(0); } else setMonth(m => m + 1);
  }

  function getBlocksForDate(date: Date): OptimizedBlock[] {
    const str = date.toISOString().split('T')[0];
    return allBlocks.filter(b => b.date === str);
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Monthly Plan</h2>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="p-2 bg-white hover:bg-[#e4e9f0] rounded-lg transition">
            <ChevronLeft className="w-4 h-4 text-slate-700" />
          </button>
          <span className="text-slate-700 font-semibold w-36 text-center">{monthName}</span>
          <button onClick={nextMonth} className="p-2 bg-white hover:bg-[#e4e9f0] rounded-lg transition">
            <ChevronRight className="w-4 h-4 text-slate-700" />
          </button>
        </div>
      </div>

      {loading && <div className="text-sm text-slate-500">Loading monthly plan...</div>}
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}<button onClick={loadMonth} className="ml-3 inline-flex items-center gap-1 underline"><RefreshCw className="w-3 h-3" /> Retry</button></div>}

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { label: 'Total Tasks', value: s?.total_tasks || 0, color: 'text-slate-900' },
          { label: 'Completed', value: s?.completed || 0, color: 'text-green-400' },
          { label: 'Overdue', value: s?.overdue || 0, color: 'text-red-400' },
          { label: 'Planned Blocks', value: allBlocks.length, color: 'text-blue-400' },
          { label: 'Block Hours', value: allBlocks.reduce((a, b) => a + (b.duration_hours || 0), 0).toFixed(1) + 'h', color: 'text-purple-400' },
        ].map(m => (
          <div key={m.label} className="kpi-card text-center">
            <p className={`text-2xl font-bold ${m.color}`}>{m.value}</p>
            <p className="text-xs text-slate-500 mt-1">{m.label}</p>
          </div>
        ))}
      </div>

      {!loading && !error && allBlocks.length === 0 && <div className="bg-white border border-slate-200 rounded-xl p-5 text-sm text-slate-500">No maintenance blocks are scheduled in this month.</div>}

      {/* Calendar Grid */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        {/* Day headers */}
        <div className="grid grid-cols-7 border-b border-slate-200">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <div key={d} className="py-2 text-center text-xs text-slate-500 font-semibold uppercase tracking-wider border-r last:border-r-0 border-slate-200">{d}</div>
          ))}
        </div>

        {/* Dates */}
        <div className="grid grid-cols-7">
          {monthDates.map((date, i) => {
            if (!date) return <div key={i} className="border-r border-b border-slate-200 min-h-[80px]" />;

            const dayBlocks = getBlocksForDate(date);
            const isToday = date.toDateString() === new Date().toDateString();

            return (
              <div
                key={i}
                className={`border-r border-b border-slate-200 min-h-[80px] p-2 ${isToday ? 'bg-red-900/10' : 'hover:bg-white/40'} transition`}
              >
                <p className={`text-xs font-semibold mb-1.5 ${isToday ? 'text-red-400' : 'text-slate-500'}`}>{date.getDate()}</p>
                {dayBlocks.slice(0, 3).map(b => (
                  <div
                    key={b.block_id}
                    className={`text-[10px] rounded px-1 py-0.5 mb-0.5 truncate cursor-pointer ${
                      b.has_critical ? 'bg-red-900/50 text-red-300' : (b.departments_involved || []).length > 1 ? 'bg-purple-900/50 text-purple-300' : 'bg-blue-900/50 text-blue-300'
                    }`}
                    title={`${b.corridor_id} ${b.start_time?.slice(0,5)}–${b.end_time?.slice(0,5)}`}
                  >
                    {b.corridor_id}
                  </div>
                ))}
                {dayBlocks.length > 3 && (
                  <p className="text-[10px] text-slate-500">+{dayBlocks.length - 3} more</p>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Weekly breakdown */}
      {analyticsData?.weekly_trend && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Weekly Maintenance Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-500 uppercase border-b border-slate-200">
                  <th className="py-2 text-left">Day</th>
                  <th className="py-2 text-right">Blocks</th>
                  <th className="py-2 text-right">Block Hours</th>
                  <th className="py-2 text-right">Tasks</th>
                  <th className="py-2 text-left pl-4">Utilization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {analyticsData.weekly_trend.map(row => (
                  <tr key={row.date} className="hover:bg-white/40">
                    <td className="py-2.5 text-slate-700">{row.day} <span className="text-slate-500 text-xs">{formatDate(row.date)}</span></td>
                    <td className="py-2.5 text-right text-slate-900">{row.blocks}</td>
                    <td className="py-2.5 text-right text-slate-900">{row.hours}h</td>
                    <td className="py-2.5 text-right text-slate-900">{row.tasks}</td>
                    <td className="py-2.5 pl-4">
                        <div className="flex items-center gap-2">
                        <div className="flex-1 bg-[#e4e9f0] rounded-full h-1.5">
                          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, (row.utilization ?? 0) * 100)}%` }} />
                        </div>
                        <span className="text-xs text-slate-500">{row.utilization == null ? '—' : `${(row.utilization * 100).toFixed(0)}%`}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

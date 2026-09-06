'use client';
import { useEffect, useState } from 'react';
import { blocks, OptimizedBlock } from '@/lib/api';
import { formatTime, formatDate, DEPT_BADGE } from '@/lib/utils';
import { ChevronLeft, ChevronRight, AlertTriangle, RefreshCw } from 'lucide-react';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function getPriorityColor(block: OptimizedBlock): string {
  if (block.has_critical) return 'border-l-red-500 bg-red-50';
  if ((block.departments_involved || []).length > 1) return 'border-l-purple-500 bg-purple-900/20';
  if (block.has_overdue) return 'border-l-amber-500 bg-amber-50';
  return 'border-l-blue-500 bg-blue-900/20';
}

function getWeekDates(offset: number): Date[] {
  const now = new Date();
  const day = now.getDay();
  const monday = new Date(now);
  monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1) + offset * 7);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

export default function WeeklyPage() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [allBlocks, setAllBlocks] = useState<OptimizedBlock[]>([]);
  const [selectedBlock, setSelectedBlock] = useState<OptimizedBlock | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const weekDates = getWeekDates(weekOffset);
  const dateFrom = weekDates[0].toISOString().split('T')[0];
  const dateTo = weekDates[6].toISOString().split('T')[0];

  async function loadWeek() {
    setLoading(true);
    setError(null);
    try { setAllBlocks((await blocks.getOptimized({ date_from: dateFrom, date_to: dateTo })).blocks); }
    catch (e: any) { setError(e?.message || 'Unable to load weekly plan'); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadWeek(); }, [weekOffset]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Weekly Plan</h2>
          <p className="text-slate-500 text-sm">{formatDate(dateFrom)} – {formatDate(dateTo)}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setWeekOffset(w => w - 1)} className="p-2 bg-white hover:bg-[#e4e9f0] rounded-lg transition">
            <ChevronLeft className="w-4 h-4 text-slate-700" />
          </button>
          <button onClick={() => setWeekOffset(0)} className="px-4 py-2 bg-white hover:bg-[#e4e9f0] rounded-lg text-sm text-slate-700 transition">
            This Week
          </button>
          <button onClick={() => setWeekOffset(w => w + 1)} className="p-2 bg-white hover:bg-[#e4e9f0] rounded-lg transition">
            <ChevronRight className="w-4 h-4 text-slate-700" />
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center gap-2"><span>{error}</span><button onClick={loadWeek} className="inline-flex items-center gap-1 underline"><RefreshCw className="w-3 h-3" /> Retry</button></div>}

      {/* Legend */}
      <div className="flex items-center gap-4 mb-4 text-xs">
        {[
          { color: 'border-l-red-500 bg-red-50', label: 'Critical' },
          { color: 'border-l-purple-500 bg-purple-900/20', label: 'Multi-Dept' },
          { color: 'border-l-amber-500 bg-amber-50', label: 'Overdue' },
          { color: 'border-l-blue-500 bg-blue-900/20', label: 'Standard' },
        ].map(l => (
          <span key={l.label} className={`flex items-center gap-1.5 px-2 py-1 rounded border-l-4 ${l.color}`}>
            {l.label}
          </span>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2">
        {weekDates.map((date, i) => {
          const dateStr = date.toISOString().split('T')[0];
          const dayBlocks = allBlocks.filter(b => b.date === dateStr);
          const isToday = dateStr === new Date().toISOString().split('T')[0];

          return (
            <div key={i} className={`bg-white border rounded-xl overflow-hidden ${isToday ? 'border-red-600/50' : 'border-slate-200'}`}>
              {/* Day Header */}
              <div className={`px-3 py-2 border-b ${isToday ? 'bg-red-600/20 border-red-200/40' : 'border-slate-200'}`}>
                <p className={`text-xs font-semibold ${isToday ? 'text-red-400' : 'text-slate-500'}`}>{DAYS[i]}</p>
                <p className={`text-lg font-bold ${isToday ? 'text-slate-900' : 'text-slate-700'}`}>{date.getDate()}</p>
                {dayBlocks.length > 0 && (
                  <p className="text-xs text-slate-500">{dayBlocks.length} block{dayBlocks.length !== 1 ? 's' : ''}</p>
                )}
              </div>

              {/* Blocks */}
              <div className="p-2 space-y-1.5 min-h-[120px]">
                {loading ? (
                  <div className="h-8 bg-[#e4e9f0]/50 rounded animate-pulse" />
                ) : dayBlocks.length === 0 ? (
                  <p className="text-xs text-slate-600 text-center mt-4">No blocks</p>
                ) : dayBlocks.map(b => (
                  <div
                    key={b.block_id}
                    onClick={() => setSelectedBlock(b === selectedBlock ? null : b)}
                    className={`border-l-4 rounded-r-lg px-2 py-1.5 cursor-pointer hover:brightness-110 transition ${getPriorityColor(b)}`}
                  >
                    <p className="text-xs font-semibold text-slate-900">{b.corridor_id}</p>
                    <p className="text-[10px] text-slate-500">{formatTime(b.start_time)}–{formatTime(b.end_time)}</p>
                    <p className="text-[10px] text-slate-500">{b.tasks_completed}t · {b.departments_involved?.length || 0}d</p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Block Detail */}
      {selectedBlock && (
        <div className="mt-4 bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900">{selectedBlock.block_id}</h3>
              <p className="text-slate-500 text-sm">Corridor {selectedBlock.corridor_id} · {formatDate(selectedBlock.date)}</p>
            </div>
            <button onClick={() => setSelectedBlock(null)} className="text-slate-500 hover:text-slate-900 text-xs">Close ×</button>
          </div>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><p className="text-xs text-slate-500">Time</p><p className="text-sm text-slate-900">{formatTime(selectedBlock.start_time)}–{formatTime(selectedBlock.end_time)}</p></div>
            <div><p className="text-xs text-slate-500">Duration</p><p className="text-sm text-slate-900">{selectedBlock.duration_hours}h</p></div>
            <div><p className="text-xs text-slate-500">Tasks</p><p className="text-sm text-slate-900">{selectedBlock.tasks_completed}</p></div>
            <div><p className="text-xs text-slate-500">Score</p><p className="text-sm text-slate-900">{selectedBlock.optimization_score}/100</p></div>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            {(selectedBlock.departments_involved || []).map(d => (
              <span key={d} className={`text-xs px-2 py-1 rounded border ${DEPT_BADGE[d] || ''}`}>{d}</span>
            ))}
          </div>
          {selectedBlock.explanation && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-400 font-semibold mb-1">Why this block?</p>
              <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans">{selectedBlock.explanation}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

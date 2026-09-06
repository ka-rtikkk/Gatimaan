'use client';
import { useEffect, useState } from 'react';
import { analytics, trains, CorridorAnalytics, Corridor } from '@/lib/api';
import { MapPin, AlertTriangle, Zap, Train, RefreshCw } from 'lucide-react';

const CORRIDOR_POSITIONS: Record<string, { x: number; y: number }> = {
  'DEL-AGR': { x: 42, y: 28 }, 'LKO-CNB': { x: 55, y: 30 },
  'MUM-PUN': { x: 28, y: 55 }, 'CHN-BNG': { x: 55, y: 72 },
  'KOL-ASN': { x: 78, y: 38 }, 'DEL-ALD': { x: 52, y: 33 },
  'HYD-SEC': { x: 52, y: 62 }, 'JAI-AJM': { x: 36, y: 32 },
  'AMD-RTM': { x: 30, y: 42 }, 'PAT-DHN': { x: 68, y: 38 },
  'NGP-ITR': { x: 48, y: 52 }, 'BPL-KTE': { x: 45, y: 44 },
  'VZG-VJW': { x: 62, y: 62 }, 'SUR-GNT': { x: 48, y: 64 },
  'AWB-WRD': { x: 44, y: 58 }, 'GHY-LUM': { x: 82, y: 26 },
  'JMU-UDM': { x: 38, y: 18 }, 'TVC-ERN': { x: 46, y: 84 },
  'RJT-ADI': { x: 25, y: 42 }, 'BSP-RIG': { x: 64, y: 50 },
};

function getNodeColor(ca: CorridorAnalytics): string {
  if (ca.critical_tasks > 0) return '#dc2626';
  if (ca.overdue_tasks > 0) return '#f59e0b';
  if (ca.task_count > 5) return '#3b82f6';
  return '#22c55e';
}

function getNodeSize(ca: CorridorAnalytics): number {
  const base = 8;
  const bonus = Math.min(ca.task_count * 0.5, 8);
  return base + bonus;
}

export default function CorridorsPage() {
  const [corridorData, setCorridorData] = useState<CorridorAnalytics[]>([]);
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [selected, setSelected] = useState<CorridorAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadCorridors() {
    setLoading(true); setError(null);
    try {
      const [ca, co] = await Promise.all([analytics.getCorridors(), trains.getCorridors()]);
        setCorridorData(ca.corridors);
        setCorridors(co.corridors);
    } catch (e: any) {
      setError(e?.message || 'Unable to load corridor data');
    } finally { setLoading(false); }
  }

  useEffect(() => { loadCorridors(); }, []);

  if (loading) return <div className="p-6 text-slate-500">Loading corridor data...</div>;
  if (error) return <div className="p-6"><div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-700">{error}<button onClick={loadCorridors} className="ml-3 inline-flex items-center gap-1 underline"><RefreshCw className="w-3 h-3" /> Retry</button></div></div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Corridor View</h2>
        <p className="text-slate-500 text-sm mt-0.5">Railway corridor maintenance visualization — simulated network map</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Map */}
        <div className="col-span-2 bg-white border border-slate-200 rounded-xl p-4 relative overflow-hidden" style={{ minHeight: '500px' }}>
          <div className="absolute inset-0 opacity-5" style={{
            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'20\' height=\'20\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M0 0h20v20H0z\' fill=\'%23334155\'/%3E%3C/svg%3E")',
          }} />

          {/* India outline (simplified SVG) */}
          <svg viewBox="0 0 100 100" className="w-full h-full absolute inset-0">
            {/* Simplified India boundary */}
            <path
              d="M25,15 Q35,10 45,12 Q55,10 65,15 Q75,18 80,25 Q85,30 82,38 L85,45 Q88,52 85,58 Q82,65 78,68 Q72,72 65,75 Q60,80 55,85 Q50,90 46,88 Q42,85 38,80 Q30,72 25,65 Q20,58 18,50 Q15,42 18,35 Q20,25 25,15Z"
              fill="none" stroke="#334155" strokeWidth="0.5" opacity="0.6"
            />

            {/* Corridors as lines */}
            {corridorData.map(ca => {
              const pos = CORRIDOR_POSITIONS[ca.corridor_id];
              if (!pos) return null;
              const color = getNodeColor(ca);
              const size = getNodeSize(ca);
              return (
                <g key={ca.corridor_id}>
                  {/* Pulse for critical */}
                  {ca.critical_tasks > 0 && (
                    <circle cx={pos.x} cy={pos.y} r={size + 4} fill={color} opacity="0.2">
                      <animate attributeName="r" from={size} to={size + 6} dur="2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" from="0.3" to="0" dur="2s" repeatCount="indefinite" />
                    </circle>
                  )}
                  <circle
                    cx={pos.x} cy={pos.y} r={size}
                    fill={color} opacity="0.8"
                    className="cursor-pointer hover:opacity-100"
                    onClick={() => setSelected(ca)}
                  />
                  <text x={pos.x} y={pos.y - size - 2} textAnchor="middle" fontSize="2.5" fill="#94a3b8">
                    {ca.corridor_id}
                  </text>
                  {ca.block_count > 0 && (
                    <text x={pos.x} y={pos.y + 1} textAnchor="middle" fontSize="3" fill="white" fontWeight="bold">
                      {ca.task_count}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 flex flex-col gap-1.5">
            {[
              { color: '#dc2626', label: 'Critical tasks' },
              { color: '#f59e0b', label: 'Overdue tasks' },
              { color: '#3b82f6', label: 'High workload' },
              { color: '#22c55e', label: 'Normal' },
            ].map(l => (
              <span key={l.label} className="flex items-center gap-1.5 text-xs text-slate-500">
                <span className="w-3 h-3 rounded-full" style={{ background: l.color }} />
                {l.label}
              </span>
            ))}
          </div>

          <div className="absolute top-4 right-4 text-xs text-slate-500 bg-[#e8edf3] px-2 py-1 rounded">
            Click a node for details
          </div>
        </div>

        {/* Corridor List / Detail */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          {selected ? (
            <div className="p-4">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-slate-900">{selected.corridor_name}</h3>
                  <p className="text-xs text-slate-500 font-mono">{selected.corridor_id}</p>
                </div>
                <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-slate-900 text-xs">✕</button>
              </div>
              <div className="space-y-3">
                {[
                  { icon: Zap, label: 'Total Tasks', value: selected.task_count },
                  { icon: AlertTriangle, label: 'Critical Tasks', value: selected.critical_tasks, color: 'text-red-400' },
                  { icon: AlertTriangle, label: 'Overdue Tasks', value: selected.overdue_tasks, color: 'text-amber-400' },
                  { icon: Train, label: 'Planned Blocks', value: selected.block_count },
                  { icon: MapPin, label: 'Block Hours', value: selected.block_hours + 'h' },
                ].map(({ icon: Icon, label, value, color }) => (
                  <div key={label} className="flex items-center gap-3 bg-[#e8edf3] rounded-lg px-3 py-2">
                    <Icon className={`w-4 h-4 ${color || 'text-slate-500'}`} />
                    <span className="text-sm text-slate-700 flex-1">{label}</span>
                    <span className={`text-sm font-bold ${color || 'text-slate-900'}`}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="overflow-y-auto max-h-[500px]">
              <div className="p-3 border-b border-slate-200 sticky top-0 bg-white">
                <p className="text-xs font-semibold text-slate-500">All Corridors ({corridorData.length})</p>
              </div>
              {corridorData.length === 0 ? <p className="p-4 text-sm text-slate-500">No corridor data available.</p> : corridorData.map(ca => (
                <div
                  key={ca.corridor_id}
                  onClick={() => setSelected(ca)}
                  className="px-4 py-3 border-b border-slate-200 hover:bg-[#e4e9f0]/50 cursor-pointer transition"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-900">{ca.corridor_id}</p>
                      <p className="text-xs text-slate-500 truncate max-w-[160px]">{ca.corridor_name}</p>
                    </div>
                    <div className="text-right">
                      {ca.critical_tasks > 0 && <p className="text-xs text-red-400">⚠ {ca.critical_tasks} critical</p>}
                      <p className="text-xs text-slate-500">{ca.task_count} tasks</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

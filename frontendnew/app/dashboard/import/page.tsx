'use client';
import { useRef, useState } from 'react';
import { importData } from '@/lib/api';
import { Database, Upload, CheckCircle2, AlertTriangle, FileText, Trash2, Wifi, Server, Radio, RefreshCw, Link2 } from 'lucide-react';

const sources = [
  { code: 'TMS', name: 'Track Management System', dept: 'Engineering', icon: Server },
  { code: 'SMMS', name: 'Signalling Maintenance & Management System', dept: 'S&T', icon: Radio },
  { code: 'TDMS', name: 'Traction Distribution Management System', dept: 'Traction Distribution', icon: ZapIcon },
  { code: 'COA', name: 'Control Office Application', dept: 'Train timetable & block windows', icon: Wifi },
  { code: 'GOODS', name: 'Goods Train Forecast', dept: 'Forecasted freight movements', icon: RefreshCw },
];
function ZapIcon(props: any) { return <span {...props} className="text-lg leading-none">⚡</span>; }

const CSV_TEMPLATE = `task_id,department,task_type,asset_type,asset_name,corridor_id,location,duration_hours,criticality,urgency,safety_risk,asset_importance,due_date,status\nT0001,Engineering,Track Geometry Correction,Track,Track km 45-47,DEL-AGR,Delhi-Agra Section,2,5,5,5,5,2026-09-15,Pending\nT0002,S&T,Point Machine Overhaul,Point Machine,Station Signal Panel,DEL-AGR,Mathura Station,1,4,4,5,4,2026-09-16,Pending`;

export default function ImportPage() {
  const [mode, setMode] = useState<'demo' | 'api'>('demo');
  const [demoLoading, setDemoLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [csvResult, setCsvResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function loadDemo() {
    setDemoLoading(true); setMsg(null);
    try {
      const res = await importData.loadDemo();
      setMsg({ type: 'success', text: `Demo data loaded: ${res.results.tasks} tasks, ${res.results.trains} trains, ${res.results.windows} block windows, ${res.results.corridors} corridors` });
    } catch (e: any) { setMsg({ type: 'error', text: e.message }); }
    finally { setDemoLoading(false); }
  }
  async function clearAll() {
    if (!confirm('Clear all data? This cannot be undone.')) return;
    setClearLoading(true);
    try { await importData.clearData(); setMsg({ type: 'success', text: 'All data cleared' }); }
    catch (e: any) { setMsg({ type: 'error', text: e.message }); }
    finally { setClearLoading(false); }
  }
  async function uploadCsv() {
    const file = fileRef.current?.files?.[0]; if (!file) return;
    setUploading(true); setCsvResult(null);
    try { setCsvResult(await importData.uploadTasksCsv(file)); }
    catch (e: any) { setCsvResult({ error: e.message }); }
    finally { setUploading(false); }
  }
  function downloadTemplate() {
    const url = URL.createObjectURL(new Blob([CSV_TEMPLATE], { type: 'text/csv' }));
    const a = document.createElement('a'); a.href = url; a.download = 'gatimaan_tasks_template.csv'; a.click(); URL.revokeObjectURL(url);
  }

  return (
    <div className="p-6 md:p-8 space-y-7 max-w-6xl">
      <div>
        <span className="section-tag"><Database className="w-3.5 h-3.5" /> DATA INTEGRATION TIER</span>
        <h2 className="text-3xl font-black tracking-tight text-slate-900">Data Sources</h2>
        <p className="text-slate-500 text-sm mt-1 max-w-2xl">Prototype-ready CSV ingestion today, with an API adapter architecture for authorized TMS, SMMS, TDMS and COA integrations.</p>
      </div>

      <div className="p-2 rounded-2xl bg-[#e7ecf2] neo-inset flex gap-2 max-w-xl">
        <button onClick={() => setMode('demo')} className={`flex-1 rounded-xl px-5 py-3 text-sm font-bold ${mode === 'demo' ? 'bg-white text-red-600 shadow-md' : 'text-slate-500'}`}>
          DEMO / CSV <span className="ml-1 text-xs font-medium">ACTIVE</span>
        </button>
        <button onClick={() => setMode('api')} className={`flex-1 rounded-xl px-5 py-3 text-sm font-bold ${mode === 'api' ? 'bg-white text-blue-600 shadow-md' : 'text-slate-500'}`}>
          LIVE APIs <span className="ml-1 text-xs font-medium">READY</span>
        </button>
      </div>

      {msg && <div className={`rounded-2xl p-4 flex items-start gap-3 ${msg.type === 'success' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`}><CheckCircle2 className="w-4 h-4 mt-0.5" /><p className="text-sm font-medium">{msg.text}</p></div>}

      <section className="bg-white rounded-2xl p-6">
        <div className="flex items-start justify-between gap-4 mb-5">
          <div><h3 className="font-bold text-slate-900">Integration Status</h3><p className="text-xs text-slate-500 mt-1">All sources normalize into Gatimaan's common planning data model.</p></div>
          <span className="section-tag mb-0">{mode === 'demo' ? '● DEMO ENVIRONMENT' : '○ LIVE API DESIGN'}</span>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((s) => { const Icon = s.icon; const active = mode === 'demo'; return (
            <div key={s.code} className="rounded-2xl bg-[#f1f4f8] p-4 neo-inset border border-slate-200">
              <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm"><Icon className="w-5 h-5 text-slate-500" /></div><div className="min-w-0"><p className="font-black text-sm text-slate-900">{s.code}</p><p className="text-xs text-slate-500 truncate">{s.dept}</p></div><span className={`ml-auto text-[10px] font-bold px-2 py-1 rounded-full ${active ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{active ? 'SIMULATED' : 'API READY'}</span></div>
              <p className="text-xs text-slate-500 mt-3 leading-relaxed">{s.name}</p>
            </div>
          )})}
        </div>
      </section>

      {mode === 'demo' ? <>
        <section className="bg-white rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-3"><div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center"><Database className="w-5 h-5 text-red-600" /></div><div><h3 className="font-bold text-slate-900">Prototype Dataset</h3><p className="text-xs text-slate-500">Synthetic data stands in for the railway source systems during SIH demonstration.</p></div></div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4"><p className="text-xs text-amber-700 font-medium">⚠ SIMULATED PROTOTYPE DATA — not connected to real Indian Railways operational systems.</p></div>
          <div className="flex flex-wrap gap-3"><button onClick={loadDemo} disabled={demoLoading} className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-2.5 rounded-xl text-white font-bold text-sm"><Database className="w-4 h-4" />{demoLoading ? 'Loading...' : 'Load Demo Dataset'}</button><button onClick={clearAll} disabled={clearLoading} className="flex items-center gap-2 bg-[#e4e9f0] px-4 py-2.5 rounded-xl text-slate-600 text-sm font-semibold"><Trash2 className="w-4 h-4" />{clearLoading ? 'Clearing...' : 'Clear Data'}</button></div>
        </section>

        <section className="bg-white rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-1"><Upload className="w-4 h-4 text-blue-600" /><h3 className="font-bold text-slate-900">CSV Maintenance Feed</h3></div>
          <p className="text-sm text-slate-500 mb-4">Use CSV to simulate maintenance records arriving from TMS, SMMS and TDMS.</p>
          <button onClick={downloadTemplate} className="flex items-center gap-2 text-sm text-blue-600 font-semibold mb-4"><FileText className="w-4 h-4" />Download CSV Template</button>
          <div className="bg-[#f1f4f8] rounded-xl p-3 mb-4 neo-inset"><p className="text-xs text-slate-500 mb-2">Required columns</p><div className="flex flex-wrap gap-1.5">{['task_id','department','task_type','corridor_id','duration_hours','criticality'].map(c => <code key={c} className="text-xs bg-white text-blue-700 px-2 py-1 rounded-lg shadow-sm">{c}</code>)}</div></div>
          <div className="border-2 border-dashed border-slate-300 rounded-2xl p-7 text-center bg-[#f7f9fb]"><Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" /><p className="text-sm text-slate-500 mb-3">Drop a CSV file or choose one</p><input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={uploadCsv} /><button onClick={() => fileRef.current?.click()} disabled={uploading} className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-5 py-2.5 rounded-xl text-white text-sm font-semibold">{uploading ? 'Uploading...' : 'Choose CSV File'}</button></div>
          {csvResult && <div className={`mt-4 rounded-xl p-4 ${csvResult.error || csvResult.rejected > 0 ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'}`}>
            {csvResult.error ? <p className="text-red-700 text-sm">{csvResult.error}</p> : <>
              <p className="text-slate-900 text-sm font-semibold">CSV import results</p>
              <p className="text-slate-700 text-xs mt-1">Received: {csvResult.received ?? csvResult.total} · Imported: {csvResult.imported ?? csvResult.inserted} · Rejected: {csvResult.rejected ?? 0}</p>
              {(csvResult.warnings_count > 0 || csvResult.errors?.length > 0) && <p className="text-amber-700 text-xs mt-1">Warnings: {csvResult.warnings_count ?? 0} · Validation errors: {csvResult.errors?.length ?? 0}</p>}
              {csvResult.warnings?.length > 0 && <p className="text-amber-700 text-xs mt-2">{csvResult.warnings.slice(0, 3).join(' · ')}</p>}
            </>}
          </div>}
        </section>
      </> : <section className="bg-white rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5"><div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><Link2 className="w-5 h-5 text-blue-600" /></div><div><h3 className="font-bold text-slate-900">Live API Integration Tier</h3><p className="text-xs text-slate-500">Architecture prepared for authorized railway-system connectors.</p></div></div>
        <div className="grid md:grid-cols-2 gap-4">{sources.map(s => <div key={s.code} className="flex items-center gap-3 rounded-xl bg-[#f1f4f8] p-4"><div className="w-2.5 h-2.5 rounded-full bg-blue-500"/><div className="flex-1"><p className="font-bold text-sm text-slate-900">{s.code} API adapter</p><p className="text-xs text-slate-500">Endpoint and credentials configured by authorized deployment team</p></div><span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">READY</span></div>)}</div>
        <div className="mt-5 bg-blue-50 border border-blue-100 rounded-xl p-4 text-xs text-blue-800 leading-relaxed"><b>Production flow:</b> source API → adapter → validation/normalization → unified data model → planning engine. The optimizer remains independent of the source system.</div>
      </section>}
    </div>
  );
}

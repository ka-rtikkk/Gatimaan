'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { Train, AlertTriangle } from 'lucide-react';

const DEMO_USERS = [
  { username: 'demo', password: 'demo', role: 'Admin (Full Access)' },
  { username: 'control', password: 'control123', role: 'Control Office' },
  { username: 'engineer', password: 'eng123', role: 'Engineering' },
  { username: 'signal', password: 'signal123', role: 'S&T' },
  { username: 'traction', password: 'traction123', role: 'Traction Distribution' },
];

export default function LoginPage() {
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('demo');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.push('/dashboard');
  }, [user]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen rail-bg flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <div className="mb-10 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="bg-red-600 p-2.5 rounded-xl">
            <Train className="w-8 h-8 text-slate-900" />
          </div>
          <div>
            <h1 className="text-4xl font-black tracking-widest text-slate-900">GATIMAAN</h1>
            <p className="text-xs tracking-[0.3em] text-slate-500 uppercase">Block Planning System</p>
          </div>
        </div>
        <p className="text-slate-500 text-sm max-w-xs">
          AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations
        </p>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-sm bg-white border border-slate-200 rounded-2xl p-8 backdrop-blur-sm shadow-2xl">
        <h2 className="text-xl font-bold text-slate-900 mb-6">Sign in</h2>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-300 text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-500 mb-1.5">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full bg-[#eef2f7] border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition"
              placeholder="demo"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-500 mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full bg-[#eef2f7] border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition"
              placeholder="demo"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition"
          >
            {loading ? 'Signing in...' : 'Sign in →'}
          </button>
        </form>

        {/* Demo user quick-select */}
        <div className="mt-6 pt-6 border-t border-slate-200">
          <p className="text-xs text-slate-500 mb-3 text-center uppercase tracking-wider">Demo Accounts</p>
          <div className="space-y-1.5">
            {DEMO_USERS.map(u => (
              <button
                key={u.username}
                onClick={() => { setUsername(u.username); setPassword(u.password); }}
                className="w-full text-left px-3 py-2 bg-[#e8edf3] hover:bg-[#e4e9f0] rounded-lg text-xs flex justify-between transition"
              >
                <span className="text-slate-700 font-mono">{u.username}</span>
                <span className="text-slate-500">{u.role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Prototype warning */}
      <div className="mt-6 max-w-sm text-center">
        <p className="text-xs text-amber-400/80 flex items-center justify-center gap-1.5">
          <AlertTriangle className="w-3 h-3" />
          SIH Prototype · Uses simulated data · Not connected to real IR systems
        </p>
      </div>
    </div>
  );
}

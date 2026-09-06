/**
 * Gatimaan Design Tokens & Utility Functions
 */

export const DEPT_COLORS: Record<string, string> = {
  'Engineering': 'bg-blue-600 text-white',
  'S&T': 'bg-green-600 text-white',
  'Traction Distribution': 'bg-amber-600 text-white',
};

export const DEPT_BADGE: Record<string, string> = {
  'Engineering': 'bg-blue-100 text-blue-800 border-blue-200',
  'S&T': 'bg-green-100 text-green-800 border-green-200',
  'Traction Distribution': 'bg-amber-100 text-amber-800 border-amber-200',
};

export const PRIORITY_COLORS: Record<string, string> = {
  'CRITICAL': 'bg-red-100 text-red-800 border-red-300',
  'HIGH': 'bg-orange-100 text-orange-800 border-orange-300',
  'MEDIUM': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'LOW': 'bg-gray-100 text-gray-700 border-gray-300',
};

export const PRIORITY_DOT: Record<string, string> = {
  'CRITICAL': 'bg-red-500',
  'HIGH': 'bg-orange-400',
  'MEDIUM': 'bg-yellow-400',
  'LOW': 'bg-gray-400',
};

export const STATUS_COLORS: Record<string, string> = {
  'Pending': 'bg-blue-100 text-blue-800',
  'Scheduled': 'bg-purple-100 text-purple-800',
  'In Progress': 'bg-amber-100 text-amber-800',
  'Completed': 'bg-green-100 text-green-800',
  'Overdue': 'bg-red-100 text-red-800',
};

export const BLOCK_COLORS = [
  'bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-amber-500',
  'bg-purple-500', 'bg-teal-500', 'bg-pink-500', 'bg-indigo-500',
];

export function formatTime(timeStr: string): string {
  if (!timeStr) return '';
  return timeStr.slice(0, 5); // "HH:MM"
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
}

export function getDeptShort(dept: string): string {
  const map: Record<string, string> = {
    'Engineering': 'ENG',
    'S&T': 'S&T',
    'Traction Distribution': 'TRD',
  };
  return map[dept] || dept.slice(0, 3);
}

export function getPriorityScore(score?: number): string {
  if (score == null) return '—';
  return (score * 100).toFixed(0);
}

export function clsxLocal(...args: (string | undefined | null | false)[]): string {
  return args.filter(Boolean).join(' ');
}

'use client';

import { useEffect, useState } from 'react';

interface StatusData {
  status: string;
  uptime_percentage: number;
  last_check: string | null;
  total_services: number;
  recently_checked_24h: number;
  success_rate_24h: number;
  scheduler_running: boolean;
  incidents: Array<{
    timestamp: string;
    type: string;
    description: string;
  }>;
  updated_at: string;
}

export default function StatusPage() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/status');
        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }
        const data = await response.json();
        setStatus(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    if (status === 'operational') return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    if (status === 'degraded') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-zinc-600 dark:text-zinc-400">Loading status...</p>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400">{error || 'Failed to load status'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50 mb-8">System Status</h1>

      <div className="mb-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Current Status</h2>
          <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(status.status)}`}>
            {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Uptime</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{status.uptime_percentage}%</p>
          </div>
          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Success Rate (24h)</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{status.success_rate_24h}%</p>
          </div>
          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Total Services</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{status.total_services}</p>
          </div>
          <div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Recently Checked (24h)</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{status.recently_checked_24h}</p>
          </div>
        </div>
        {status.last_check && (
          <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Last check: {formatDate(status.last_check)}
            </p>
          </div>
        )}
      </div>

      {status.incidents.length > 0 && (
        <div className="mb-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 mb-4">Recent Incidents</h2>
          <div className="space-y-3">
            {status.incidents.map((incident, idx) => (
              <div key={idx} className="border-l-4 border-yellow-500 pl-4 py-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">{incident.type}</p>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">{incident.description}</p>
                  </div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 ml-4">
                    {formatDate(incident.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-zinc-500 dark:text-zinc-400 text-center">
        Last updated: {formatDate(status.updated_at)}
      </div>
    </div>
  );
}

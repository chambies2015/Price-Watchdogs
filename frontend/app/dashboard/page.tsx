'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { dashboardApi, ServiceSummary } from '@/lib/api';
import ServiceList from '@/components/ServiceList';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import EmptyState from '@/components/EmptyState';
import OnboardingTour from '@/components/OnboardingTour';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState<{ services: ServiceSummary[]; total_services: number; active_services: number; recent_changes_count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await dashboardApi.getSummary();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <OnboardingTour />
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">Dashboard</h1>
          {user && (
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Welcome back, {user.email}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <Link
            href="/services/new"
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Add Service
          </Link>
          <button
            onClick={handleLogout}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            Sign Out
          </button>
        </div>
      </div>

      {summary && (
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Total Services</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-50">{summary.total_services}</p>
          </div>
          <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Active Services</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-50">{summary.active_services}</p>
          </div>
          <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Recent Changes</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-50">{summary.recent_changes_count}</p>
          </div>
        </div>
      )}
      
      {loading ? (
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading services...</p>
        </div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchDashboard} />
      ) : summary && summary.services.length === 0 ? (
        <EmptyState
          title="No services yet"
          message="Add your first service to start monitoring pricing changes."
          actionLabel="Add Service"
          actionHref="/services/new"
        />
      ) : summary ? (
        <ServiceList services={summary.services} />
      ) : null}
    </div>
  );
}

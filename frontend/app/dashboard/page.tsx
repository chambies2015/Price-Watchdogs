'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { dashboardApi, ServiceSummary, subscriptionsApi, Subscription, SortBy, SortOrder, SavedView, servicesApi } from '@/lib/api';
import ServiceList from '@/components/ServiceList';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import EmptyState from '@/components/EmptyState';
import OnboardingTour from '@/components/OnboardingTour';
import ServiceFilters from '@/components/ServiceFilters';
import SavedViews from '@/components/SavedViews';
import BulkImport from '@/components/BulkImport';
import { useState } from 'react';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState<{ services: ServiceSummary[]; total_services: number; active_services: number; recent_changes_count: number } | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<{ tags: string[]; isActive: boolean | null; sortBy: SortBy; sortOrder: SortOrder }>({
    tags: [],
    isActive: null,
    sortBy: 'name',
    sortOrder: 'asc',
  });
  const [showImport, setShowImport] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const tagsParam = filters.tags.length > 0 ? filters.tags.join(',') : undefined;
      const [dashboardData, subData] = await Promise.all([
        dashboardApi.getSummary(tagsParam, filters.isActive ?? undefined, filters.sortBy, filters.sortOrder),
        subscriptionsApi.getCurrent().catch(() => null)
      ]);
      setSummary(dashboardData);
      setSubscription(subData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await servicesApi.exportToCsv();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `services_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export services');
    }
  };

  const handleViewSelect = (view: SavedView) => {
    setFilters({
      tags: view.filter_tags || [],
      isActive: view.filter_active,
      sortBy: view.sort_by,
      sortOrder: view.sort_order,
    });
  };

  useEffect(() => {
    fetchDashboard();
  }, [filters.tags, filters.isActive, filters.sortBy, filters.sortOrder]);

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

      {subscription && subscription.plan_type === 'free' && subscription.service_limit !== null && (
        <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900/40 dark:bg-yellow-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-yellow-900 dark:text-yellow-200">
                {subscription.current_service_count}/{subscription.service_limit} services used
              </p>
              {subscription.current_service_count >= subscription.service_limit && (
                <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                  You have reached your service limit. Upgrade to Pro for unlimited services.
                </p>
              )}
            </div>
            <Link
              href="/pricing"
              className="rounded-md bg-yellow-600 px-4 py-2 text-sm font-medium text-white hover:bg-yellow-700"
            >
              Upgrade
            </Link>
          </div>
        </div>
      )}

      {showImport && (
        <div className="mb-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Bulk Import Services</h2>
          <BulkImport onImportComplete={() => { setShowImport(false); fetchDashboard(); }} />
        </div>
      )}

      <SavedViews currentFilters={filters} onViewSelect={handleViewSelect} />
      <ServiceFilters onFilterChange={setFilters} />

      {summary && (
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Total Services</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-50">{summary.total_services}</p>
            {subscription && subscription.service_limit !== null && (
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                Limit: {subscription.service_limit}
              </p>
            )}
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
        <ServiceList 
          services={summary.services} 
          showUpgradePrompt={subscription?.plan_type === 'free'}
        />
      ) : null}
    </div>
  );
}

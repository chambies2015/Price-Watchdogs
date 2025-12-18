'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { dashboardApi, ServiceSummary } from '@/lib/api';
import { useState } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function HomePage() {
  const { user, logout, loading: authLoading } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState<{ services: ServiceSummary[]; total_services: number; active_services: number; recent_changes_count: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      const fetchSummary = async () => {
        try {
          const data = await dashboardApi.getSummary();
          setSummary(data);
        } catch (err) {
          console.error('Failed to load summary:', err);
        } finally {
          setLoading(false);
        }
      };
      fetchSummary();
    }
  }, [user, authLoading, router]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const quickActions = [
    {
      title: 'View Dashboard',
      description: 'See all your monitored services and recent changes',
      href: '/dashboard',
      icon: '📊',
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      title: 'Add Service',
      description: 'Start monitoring a new pricing page',
      href: '/services/new',
      icon: '➕',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      title: 'Manage Services',
      description: 'View, edit, or remove your tracked services',
      href: '/dashboard',
      icon: '⚙️',
      color: 'bg-purple-500 hover:bg-purple-600'
    },
    {
      title: 'Billing & Subscription',
      description: 'Manage your plan and payment settings',
      href: '/billing',
      icon: '💳',
      color: 'bg-orange-500 hover:bg-orange-600'
    }
  ];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <nav className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-black dark:text-white">Price Watchdogs</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-zinc-600 dark:text-zinc-400">{user.email}</span>
              <button
                onClick={handleLogout}
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-black dark:text-white mb-2">
            Welcome back, {user.email.split('@')[0]}!
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400">
            Manage your price monitoring and stay informed about changes.
          </p>
        </div>

        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Total Services</p>
                <span className="text-2xl">🔗</span>
              </div>
              <p className="text-3xl font-bold text-black dark:text-white">{summary.total_services}</p>
              <Link
                href="/dashboard"
                className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View all →
              </Link>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Active Services</p>
                <span className="text-2xl">✓</span>
              </div>
              <p className="text-3xl font-bold text-black dark:text-white">{summary.active_services}</p>
              <Link
                href="/dashboard"
                className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                Manage →
              </Link>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Recent Changes</p>
                <span className="text-2xl">📈</span>
              </div>
              <p className="text-3xl font-bold text-black dark:text-white">{summary.recent_changes_count}</p>
              <Link
                href="/dashboard"
                className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View changes →
              </Link>
            </div>
          </div>
        )}

        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-black dark:text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickActions.map((action, index) => (
              <Link
                key={index}
                href={action.href}
                className="group rounded-lg border border-zinc-200 bg-white p-6 hover:shadow-lg transition-shadow dark:border-zinc-700 dark:bg-zinc-900"
              >
                <div className="text-4xl mb-4">{action.icon}</div>
                <h3 className="text-lg font-semibold text-black dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                  {action.title}
                </h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {action.description}
                </p>
              </Link>
            ))}
          </div>
        </div>

        {summary && summary.services.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-black dark:text-white">Your Services</h2>
              <Link
                href="/dashboard"
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View all →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {summary.services.slice(0, 6).map((service) => (
                <Link
                  key={service.id}
                  href={`/services/${service.id}`}
                  className="group rounded-lg border border-zinc-200 bg-white p-6 hover:shadow-lg transition-shadow dark:border-zinc-700 dark:bg-zinc-900"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-black dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {service.name}
                    </h3>
                    <span className={`text-xs px-2 py-1 rounded ${
                      service.is_active 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                        : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200'
                    }`}>
                      {service.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-3 truncate">
                    {service.url}
                  </p>
                  {service.last_change_event && (
                    <div className="mt-3 pt-3 border-t border-zinc-200 dark:border-zinc-700">
                      <p className="text-xs text-zinc-500 dark:text-zinc-400">
                        Last change: {new Date(service.last_change_event.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </Link>
              ))}
            </div>
            {summary.services.length > 6 && (
              <div className="mt-6 text-center">
                <Link
                  href="/dashboard"
                  className="inline-block rounded-md bg-zinc-900 px-6 py-3 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  View All {summary.total_services} Services
                </Link>
              </div>
            )}
          </div>
        )}

        {summary && summary.services.length === 0 && (
          <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-black dark:text-white mb-2">
              No services yet
            </h3>
            <p className="text-zinc-600 dark:text-zinc-400 mb-6">
              Start monitoring your first pricing page to get alerts when prices change.
            </p>
            <Link
              href="/services/new"
              className="inline-block rounded-md bg-zinc-900 px-6 py-3 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Add Your First Service
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { servicesApi, changesApi, snapshotsApi, Service, ServiceUpdate, ChangeEvent, Snapshot } from '@/lib/api';
import ServiceForm from '@/components/ServiceForm';
import ServiceDetail from '@/components/ServiceDetail';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';

type Tab = 'overview' | 'settings' | 'history' | 'snapshots';

export default function ServiceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const serviceId = params.id as string;
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [service, setService] = useState<Service | null>(null);
  const [recentChanges, setRecentChanges] = useState<ChangeEvent[]>([]);
  const [recentSnapshots, setRecentSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [serviceData, changesData, snapshotsData] = await Promise.all([
        servicesApi.get(serviceId),
        changesApi.getServiceChanges(serviceId, 5).catch(() => []),
        snapshotsApi.getServiceSnapshots(serviceId, 5).catch(() => []),
      ]);
      setService(serviceData);
      setRecentChanges(changesData);
      setRecentSnapshots(snapshotsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (serviceId) {
      fetchData();
    }
  }, [serviceId]);

  const handleSubmit = async (data: ServiceUpdate) => {
    try {
      const updated = await servicesApi.update(serviceId, data);
      setService(updated);
      setActiveTab('overview');
      setError('');
    } catch (err: any) {
      if (err.message && err.message.includes('frequency')) {
        setError(err.message + ' Please upgrade to Pro to use faster checks.');
      } else {
        setError(err.message || 'Failed to update service');
      }
      throw err;
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      return;
    }

    setDeleting(true);
    try {
      await servicesApi.delete(serviceId);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete service');
      setDeleting(false);
      setDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading service...</p>
        </div>
      </div>
    );
  }

  if (error && !service) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error} onRetry={fetchData} />
      </div>
    );
  }

  if (!service) {
    return null;
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'settings', label: 'Settings' },
    { id: 'history', label: 'History' },
    { id: 'snapshots', label: 'Snapshots' },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">{service.name}</h1>
        <button
          onClick={() => router.push('/dashboard')}
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Back to Dashboard
        </button>
      </div>

      <div className="mb-6 border-b border-zinc-200 dark:border-zinc-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === tab.id
                  ? 'border-zinc-900 text-zinc-900 dark:border-zinc-50 dark:text-zinc-50'
                  : 'border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-700 dark:text-zinc-400 dark:hover:border-zinc-600 dark:hover:text-zinc-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} />
        </div>
      )}

      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
        {activeTab === 'overview' && (
          <ServiceDetail
            service={service}
            recentChanges={recentChanges}
            recentSnapshots={recentSnapshots}
          />
        )}

        {activeTab === 'settings' && (
          <div>
            <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Service Settings</h2>
            <ServiceForm
              initialData={service}
              onSubmit={handleSubmit}
              onCancel={() => setActiveTab('overview')}
              submitLabel="Update Service"
            />
            <div className="mt-8 border-t border-zinc-200 pt-6 dark:border-zinc-700">
              <h2 className="mb-4 text-lg font-semibold text-red-600 dark:text-red-400">Danger Zone</h2>
              {!deleteConfirm ? (
                <button
                  onClick={handleDelete}
                  className="rounded-md border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-800 dark:bg-zinc-900 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  Delete Service
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">
                    Are you sure you want to delete this service? This action cannot be undone.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleDelete}
                      disabled={deleting}
                      className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      {deleting ? 'Deleting...' : 'Yes, Delete'}
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(false)}
                      disabled={deleting}
                      className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Change History</h2>
              <Link
                href={`/services/${serviceId}/changes`}
                className="text-sm text-blue-600 hover:underline dark:text-blue-400"
              >
                View All
              </Link>
            </div>
            {recentChanges.length === 0 ? (
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-8 text-center dark:border-zinc-700 dark:bg-zinc-800">
                <p className="text-zinc-600 dark:text-zinc-400">No changes detected yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentChanges.map((change) => (
                  <Link
                    key={change.id}
                    href={`/services/${serviceId}/changes/${change.id}`}
                    className="block rounded-md border border-zinc-200 p-4 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-zinc-900 dark:text-zinc-50">{change.summary}</p>
                        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                          {new Date(change.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="text-sm text-zinc-500 dark:text-zinc-400">
                        {(change.confidence_score * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'snapshots' && (
          <div>
            <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Snapshots</h2>
            {recentSnapshots.length === 0 ? (
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-8 text-center dark:border-zinc-700 dark:bg-zinc-800">
                <p className="text-zinc-600 dark:text-zinc-400">No snapshots yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSnapshots.map((snapshot, index) => (
                  <div
                    key={snapshot.id}
                    className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                            Snapshot #{recentSnapshots.length - index}
                          </span>
                          <span className="text-xs text-zinc-500 dark:text-zinc-400">
                            {new Date(snapshot.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="mt-2 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                          {snapshot.normalized_content.substring(0, 100)}
                          {snapshot.normalized_content.length > 100 ? '...' : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

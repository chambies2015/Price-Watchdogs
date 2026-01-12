'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { changesApi, ChangeEvent } from '@/lib/api';
import ChangeHistory from '@/components/ChangeHistory';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import EmptyState from '@/components/EmptyState';

export default function ChangeHistoryPage() {
  const router = useRouter();
  const params = useParams();
  const serviceId = params.id as string;
  const [changes, setChanges] = useState<ChangeEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchChanges = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await changesApi.getServiceChanges(serviceId, 50);
      setChanges(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load change history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (serviceId) {
      fetchChanges();
    }
  }, [serviceId]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">Change History</h1>
        <button
          onClick={() => router.push(`/services/${serviceId}`)}
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Back to Service
        </button>
      </div>

      {loading ? (
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading change history...</p>
        </div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchChanges} />
      ) : changes.length === 0 ? (
        <EmptyState
          title="No changes detected"
          message="This service hasn't had any changes detected yet."
          actionLabel="Back to Service"
          onAction={() => router.push(`/services/${serviceId}`)}
        />
      ) : (
        <ChangeHistory changes={changes} serviceId={serviceId} />
      )}
    </div>
  );
}


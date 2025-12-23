'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { changesApi, ChangeEventDetail, ChangeType } from '@/lib/api';
import DiffView from '@/components/DiffView';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';

export function generateStaticParams() {
  return [];
}

function getChangeTypeLabel(changeType: ChangeType): string {
  const labels: Record<ChangeType, string> = {
    price_increase: 'Price Increase',
    price_decrease: 'Price Decrease',
    new_plan_added: 'New Plan Added',
    plan_removed: 'Plan Removed',
    free_tier_removed: 'Free Tier Removed',
    unknown: 'Change Detected',
  };
  return labels[changeType] || 'Change';
}

function getChangeTypeBadgeColor(changeType: ChangeType): string {
  const colors: Record<ChangeType, string> = {
    price_increase: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    price_decrease: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    new_plan_added: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    plan_removed: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    free_tier_removed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    unknown: 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400',
  };
  return colors[changeType] || colors.unknown;
}

export default function DiffViewPage() {
  const router = useRouter();
  const params = useParams();
  const serviceId = params.id as string;
  const changeId = params.changeId as string;
  const [changeEvent, setChangeEvent] = useState<ChangeEventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchChangeEvent = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await changesApi.getChangeEvent(changeId);
        setChangeEvent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load change details');
      } finally {
        setLoading(false);
      }
    };

    if (changeId) {
      fetchChangeEvent();
    }
  }, [changeId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading diff...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!changeEvent) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">Change Details</h1>
          <div className="mt-2 flex items-center gap-2">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getChangeTypeBadgeColor(changeEvent.change_type)}`}>
              {getChangeTypeLabel(changeEvent.change_type)}
            </span>
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              {(changeEvent.confidence_score * 100).toFixed(0)}% confidence
            </span>
          </div>
        </div>
        <button
          onClick={() => router.push(`/services/${serviceId}/changes`)}
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Back to History
        </button>
      </div>

      <div className="mb-6 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Summary</h2>
        <p className="mt-2 text-zinc-700 dark:text-zinc-300">{changeEvent.summary}</p>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Detected: {new Date(changeEvent.created_at).toLocaleString()}
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Content Comparison</h2>
        <DiffView
          oldContent={changeEvent.old_snapshot?.normalized_content || null}
          newContent={changeEvent.new_snapshot.normalized_content}
        />
      </div>
    </div>
  );
}


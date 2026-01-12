'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChangeEvent, ChangeType } from '@/lib/api';

interface ChangeHistoryProps {
  changes: ChangeEvent[];
  serviceId: string;
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

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

export default function ChangeHistory({ changes, serviceId }: ChangeHistoryProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  if (changes.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
        <p className="text-zinc-600 dark:text-zinc-400">No changes detected yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {changes.map((change) => {
        const isExpanded = expandedIds.has(change.id);
        return (
          <div
            key={change.id}
            className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900"
          >
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getChangeTypeBadgeColor(change.change_type)}`}>
                      {getChangeTypeLabel(change.change_type)}
                    </span>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {(change.confidence_score * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-zinc-900 dark:text-zinc-50">{change.summary}</p>
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    {formatDate(change.created_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => toggleExpand(change.id)}
                    className="rounded-md border border-zinc-300 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
                  >
                    {isExpanded ? 'Hide' : 'Show'} Details
                  </button>
                  <Link
                    href={`/services/change-detail?id=${serviceId}&changeId=${change.id}`}
                    className="rounded-md bg-zinc-900 px-3 py-1 text-xs font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                  >
                    View Diff
                  </Link>
                </div>
              </div>
              {isExpanded && (
                <div className="mt-4 rounded-md border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800">
                  <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">Change Details</p>
                  <div className="mt-2 space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
                    <p>Change ID: {change.id}</p>
                    <p>Service ID: {change.service_id}</p>
                    {change.old_snapshot_id && <p>Old Snapshot: {change.old_snapshot_id}</p>}
                    <p>New Snapshot: {change.new_snapshot_id}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}


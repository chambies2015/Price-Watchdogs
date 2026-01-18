'use client';

import { Service, ChangeEvent, Snapshot } from '@/lib/api';
import Link from 'next/link';
import SnapshotList from './SnapshotList';
import { formatDate, formatDateTime } from '@/lib/datetime';

interface ServiceDetailProps {
  service: Service;
  recentChanges: ChangeEvent[];
  recentSnapshots: Snapshot[];
}

export default function ServiceDetail({ service, recentChanges, recentSnapshots }: ServiceDetailProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Service Information</h2>
        <div className="mt-4 space-y-2">
          <div>
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Name:</span>
            <span className="ml-2 text-sm text-zinc-600 dark:text-zinc-400">{service.name}</span>
          </div>
          <div>
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">URL:</span>
            <a
              href={service.url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-sm text-blue-600 hover:underline dark:text-blue-400"
            >
              {service.url}
            </a>
          </div>
          <div>
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Check Frequency:</span>
            <span className="ml-2 text-sm text-zinc-600 dark:text-zinc-400">
              {service.check_frequency === 'daily' ? 'Daily' : 'Weekly'}
            </span>
          </div>
          <div>
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Status:</span>
            <span className={`ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
              service.is_active
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400'
            }`}>
              {service.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div>
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Alerts:</span>
            <span className={`ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
              service.alerts_enabled
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400'
            }`}>
              {service.alerts_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          {service.last_checked_at && (
            <div>
              <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Last Checked:</span>
              <span className="ml-2 text-sm text-zinc-600 dark:text-zinc-400">
                {formatDateTime(service.last_checked_at)}
              </span>
            </div>
          )}
        </div>
      </div>

      {recentChanges.length > 0 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Recent Changes</h2>
            <Link
              href={`/services/changes?id=${service.id}`}
              className="text-sm text-blue-600 hover:underline dark:text-blue-400"
            >
              View All
            </Link>
          </div>
          <div className="mt-4 space-y-2">
            {recentChanges.slice(0, 5).map((change) => (
              <Link
                key={change.id}
                href={`/services/change-detail?id=${service.id}&changeId=${change.id}`}
                className="block rounded-md border border-zinc-200 p-3 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {change.summary}
                  </span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {formatDate(change.created_at)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {recentSnapshots.length > 0 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Recent Snapshots</h2>
          <div className="mt-4">
            <SnapshotList snapshots={recentSnapshots.slice(0, 5)} serviceId={service.id} />
          </div>
        </div>
      )}
    </div>
  );
}


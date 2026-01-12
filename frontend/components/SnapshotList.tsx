'use client';

import { Snapshot } from '@/lib/api';
import Link from 'next/link';
import { useState } from 'react';

interface SnapshotListProps {
  snapshots: Snapshot[];
  serviceId: string;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

function truncateContent(content: string, maxLength: number = 100): string {
  if (content.length <= maxLength) return content;
  return content.substring(0, maxLength) + '...';
}

export default function SnapshotList({ snapshots, serviceId }: SnapshotListProps) {
  const [viewingSnapshot, setViewingSnapshot] = useState<Snapshot | null>(null);

  if (snapshots.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center dark:border-zinc-700 dark:bg-zinc-900">
        <p className="text-zinc-600 dark:text-zinc-400">No snapshots yet.</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {snapshots.map((snapshot, index) => (
          <div
            key={snapshot.id}
            className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    Snapshot #{snapshots.length - index}
                  </span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {formatDate(snapshot.created_at)}
                  </span>
                </div>
                <p className="mt-2 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                  {truncateContent(snapshot.normalized_content)}
                </p>
                <div className="mt-2 flex gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                  <span>Hash: {snapshot.normalized_content_hash.substring(0, 8)}...</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setViewingSnapshot(snapshot)}
                  className="rounded-md border border-zinc-300 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
                >
                  View
                </button>
                {index > 0 && (
                  <Link
                    href={`/services/changes?id=${serviceId}&compare=${snapshots[index - 1].id}&with=${snapshot.id}`}
                    className="rounded-md border border-zinc-300 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
                  >
                    Compare
                  </Link>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {viewingSnapshot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="relative max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900">
            <div className="sticky top-0 flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4 dark:border-zinc-700 dark:bg-zinc-900">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                  Snapshot Content
                </h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDate(viewingSnapshot.created_at)}
                </p>
              </div>
              <button
                onClick={() => setViewingSnapshot(null)}
                className="rounded-md px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
              >
                Close
              </button>
            </div>
            <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 80px)' }}>
              <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-900 dark:text-zinc-50">
                {viewingSnapshot.normalized_content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


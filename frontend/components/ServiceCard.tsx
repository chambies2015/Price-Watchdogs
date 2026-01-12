'use client';

import { ServiceSummary, ChangeType } from '@/lib/api';
import Link from 'next/link';

interface ServiceCardProps {
  service: ServiceSummary;
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Never';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
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
    price_increase: 'Price ↑',
    price_decrease: 'Price ↓',
    new_plan_added: 'New Plan',
    plan_removed: 'Plan Removed',
    free_tier_removed: 'Free Tier Removed',
    unknown: 'Change',
  };
  return labels[changeType] || 'Change';
}

export default function ServiceCard({ service }: ServiceCardProps) {
  const statusColor = service.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400';
  const isStale = service.last_checked_at ? (Date.now() - new Date(service.last_checked_at).getTime()) > 7 * 24 * 60 * 60 * 1000 : true;
  
  return (
    <Link href={`/services/detail?id=${service.id}`}>
      <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-shadow hover:shadow-md dark:border-zinc-700 dark:bg-zinc-900">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              {service.name}
            </h3>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400 truncate">
              {service.url}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}>
                {service.is_active ? 'Active' : 'Inactive'}
              </span>
              {service.last_change_event && (
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getChangeTypeBadgeColor(service.last_change_event.change_type)}`}>
                  {getChangeTypeLabel(service.last_change_event.change_type)}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="mt-3 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
          <p>
            Last checked: <span className={isStale ? 'font-medium text-orange-600 dark:text-orange-400' : ''}>{formatRelativeTime(service.last_checked_at)}</span>
          </p>
          {service.last_change_event && (
            <p>
              Last change: {formatRelativeTime(service.last_change_event.created_at)}
            </p>
          )}
          {service.change_count > 0 && (
            <p>
              {service.change_count} change{service.change_count !== 1 ? 's' : ''} detected
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}

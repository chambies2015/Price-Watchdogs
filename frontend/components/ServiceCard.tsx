'use client';

import { Service } from '@/lib/api';
import Link from 'next/link';

interface ServiceCardProps {
  service: Service;
}

export default function ServiceCard({ service }: ServiceCardProps) {
  const statusColor = service.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400';
  const frequencyLabel = service.check_frequency === 'daily' ? 'Daily' : 'Weekly';
  
  return (
    <Link href={`/services/${service.id}`}>
      <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-shadow hover:shadow-md dark:border-zinc-700 dark:bg-zinc-900">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              {service.name}
            </h3>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400 truncate">
              {service.url}
            </p>
            <div className="mt-3 flex items-center gap-3">
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}>
                {service.is_active ? 'Active' : 'Inactive'}
              </span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {frequencyLabel} checks
              </span>
            </div>
          </div>
        </div>
        {service.last_checked_at && (
          <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            Last checked: {new Date(service.last_checked_at).toLocaleDateString()}
          </p>
        )}
      </div>
    </Link>
  );
}


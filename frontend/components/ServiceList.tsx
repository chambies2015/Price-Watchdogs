'use client';

import { ServiceSummary } from '@/lib/api';
import ServiceCard from './ServiceCard';
import Link from 'next/link';

interface ServiceListProps {
  services: ServiceSummary[];
  showUpgradePrompt?: boolean;
}

export default function ServiceList({ services, showUpgradePrompt }: ServiceListProps) {
  if (services.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
        <p className="text-zinc-600 dark:text-zinc-400">No services yet. Add your first service to get started.</p>
      </div>
    );
  }

  return (
    <>
      {showUpgradePrompt && (
        <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/40 dark:bg-blue-900/20">
          <div className="flex items-center justify-between">
            <p className="text-sm text-blue-900 dark:text-blue-200">
              You are on the free plan. Upgrade to Pro for unlimited services and advanced features.
            </p>
            <Link
              href="/pricing"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Plans
            </Link>
          </div>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <ServiceCard key={service.id} service={service} />
        ))}
      </div>
    </>
  );
}


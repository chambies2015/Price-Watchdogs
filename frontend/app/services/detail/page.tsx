'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import ServiceDetailClient from '@/components/ServiceDetailClient';
import LoadingSpinner from '@/components/LoadingSpinner';

function ServiceDetailContent() {
  const searchParams = useSearchParams();
  const serviceId = searchParams.get('id');

  if (!serviceId) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <p className="text-zinc-600 dark:text-zinc-400">Service ID is required</p>
        </div>
      </div>
    );
  }

  return <ServiceDetailClient serviceId={serviceId} />;
}

export default function ServiceDetailPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading...</p>
        </div>
      </div>
    }>
      <ServiceDetailContent />
    </Suspense>
  );
}

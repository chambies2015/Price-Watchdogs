'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import DiffViewClient from '@/components/DiffViewClient';
import LoadingSpinner from '@/components/LoadingSpinner';

function DiffViewContent() {
  const searchParams = useSearchParams();
  const serviceId = searchParams.get('id');
  const changeId = searchParams.get('changeId');

  if (!serviceId || !changeId) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <p className="text-zinc-600 dark:text-zinc-400">Service ID and Change ID are required</p>
        </div>
      </div>
    );
  }

  return <DiffViewClient serviceId={serviceId} changeId={changeId} />;
}

export default function DiffViewPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">Loading...</p>
        </div>
      </div>
    }>
      <DiffViewContent />
    </Suspense>
  );
}

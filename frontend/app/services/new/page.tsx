'use client';

import { useRouter } from 'next/navigation';
import { servicesApi, ServiceCreate } from '@/lib/api';
import ServiceForm from '@/components/ServiceForm';

export default function NewServicePage() {
  const router = useRouter();

  const handleSubmit = async (data: ServiceCreate) => {
    try {
      await servicesApi.create(data);
      router.push('/dashboard');
    } catch (error: any) {
      if (error.message && error.message.includes('limit')) {
        throw new Error(error.message + ' Please upgrade to Pro for unlimited services.');
      }
      throw error;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-3xl font-bold text-zinc-900 dark:text-zinc-50">Add New Service</h1>
        <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-900">
          <ServiceForm onSubmit={handleSubmit} onCancel={() => router.push('/dashboard')} />
        </div>
      </div>
    </div>
  );
}


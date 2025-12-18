'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { subscriptionsApi, Subscription, Payment } from '@/lib/api';
import BillingDashboard from '@/components/BillingDashboard';
import PaymentHistory from '@/components/PaymentHistory';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';

export default function BillingPage() {
  const router = useRouter();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sub, pays] = await Promise.all([
        subscriptionsApi.getCurrent(),
        subscriptionsApi.getPayments()
      ]);
      setSubscription(sub);
      setPayments(pays);
    } catch (err: any) {
      console.error('Error loading billing data:', err);
      setError(err.message || 'Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    try {
      const updated = await subscriptionsApi.cancel();
      setSubscription(updated);
    } catch (err: any) {
      throw new Error(err.message || 'Failed to cancel subscription');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  if (error && !subscription) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Billing & Subscription
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your subscription and view payment history
          </p>
        </div>

        <div className="space-y-6">
          <BillingDashboard
            subscription={subscription}
            payments={payments}
            loading={false}
            error={error}
            onCancelSubscription={handleCancelSubscription}
          />
          
          <PaymentHistory payments={payments} />
        </div>
      </div>
    </div>
  );
}


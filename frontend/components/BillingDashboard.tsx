'use client';

import { useState, useEffect } from 'react';
import { subscriptionsApi, Subscription, Payment } from '@/lib/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

interface BillingDashboardProps {
  subscription: Subscription | null;
  payments: Payment[];
  loading: boolean;
  error: string | null;
  onCancelSubscription: () => Promise<void>;
}

export default function BillingDashboard({
  subscription,
  payments,
  loading,
  error,
  onCancelSubscription
}: BillingDashboardProps) {
  const [canceling, setCanceling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const handleCancel = async () => {
    setCanceling(true);
    try {
      await onCancelSubscription();
      setShowCancelConfirm(false);
    } catch (err) {
      console.error('Error canceling subscription:', err);
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (!subscription) {
    return <ErrorMessage message="No subscription found" />;
  }

  const isPro = subscription.plan_type !== 'free';
  const planName = subscription.plan_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Current Plan
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Plan</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">{planName}</p>
          </div>
          
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Status</p>
            <span className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${
              subscription.status === 'active'
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : subscription.status === 'past_due'
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
            }`}>
              {subscription.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Service Limit</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">
              {subscription.service_limit === null ? 'Unlimited' : `${subscription.current_service_count}/${subscription.service_limit}`}
            </p>
          </div>
          
          {subscription.current_period_end && (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                {subscription.cancel_at_period_end ? 'Expires' : 'Next Billing Date'}
              </p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>

        {isPro && !subscription.cancel_at_period_end && (
          <div className="mt-6">
            <button
              onClick={() => setShowCancelConfirm(true)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
            >
              Cancel Subscription
            </button>
          </div>
        )}

        {showCancelConfirm && (
          <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-4">
              Your subscription will remain active until {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'the end of the billing period'}. 
              After that, you'll be downgraded to the free plan.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleCancel}
                disabled={canceling}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {canceling ? 'Canceling...' : 'Confirm Cancel'}
              </button>
              <button
                onClick={() => setShowCancelConfirm(false)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-semibold transition-colors"
              >
                Keep Subscription
              </button>
            </div>
          </div>
        )}

        {!isPro && (
          <div className="mt-6">
            <a
              href="/pricing"
              className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
            >
              Upgrade to Pro
            </a>
          </div>
        )}
      </div>
    </div>
  );
}


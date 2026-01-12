'use client';

import { useState, useEffect } from 'react';
import { subscriptionsApi, PlanType } from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function PricingPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleGetStarted = async (planType: PlanType) => {
    if (planType === 'free') {
      router.push('/dashboard');
      return;
    }

    try {
      setLoading(true);
      const session = await subscriptionsApi.createCheckout(planType);
      window.location.href = session.url;
    } catch (error) {
      console.error('Error creating checkout:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: 'Free',
      planType: 'free' as PlanType,
      price: '$0',
      period: 'Forever',
      features: [
        'Up to 3 services',
        'Daily or weekly checks',
        'Email alerts',
        'Change history',
        'Basic support'
      ],
      cta: 'Get Started',
      popular: false
    },
    {
      name: 'Pro Monthly',
      planType: 'pro_monthly' as PlanType,
      price: '$5',
      period: 'per month',
      features: [
        'Unlimited services',
        'Daily, weekly, or twice-daily checks',
        'Email alerts',
        'Change history',
        'Priority support',
        'Advanced analytics'
      ],
      cta: 'Start Free Trial',
      popular: true
    },
    {
      name: 'Pro Annual',
      planType: 'pro_annual' as PlanType,
      price: '$50',
      period: 'per year',
      originalPrice: '$60',
      savings: 'Save $10',
      features: [
        'Unlimited services',
        'Daily, weekly, or twice-daily checks',
        'Email alerts',
        'Change history',
        'Priority support',
        'Advanced analytics'
      ],
      cta: 'Start Free Trial',
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Choose the plan that works best for you
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.planType}
              className={`relative bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 ${
                plan.popular ? 'ring-2 ring-blue-500 scale-105' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {plan.name}
                </h3>
                <div className="flex items-baseline justify-center gap-2">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className="text-gray-600 dark:text-gray-400">
                      {plan.period}
                    </span>
                  )}
                </div>
                {plan.originalPrice && (
                  <div className="mt-2">
                    <span className="text-gray-500 line-through">{plan.originalPrice}</span>
                    <span className="ml-2 text-green-600 font-semibold">{plan.savings}</span>
                  </div>
                )}
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleGetStarted(plan.planType)}
                disabled={loading}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                  plan.popular
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
                }`}
              >
                {loading ? 'Loading...' : plan.cta}
              </button>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            All plans include a 14-day free trial. No credit card required.
          </p>
        </div>
      </div>
    </div>
  );
}


'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/home');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white dark:bg-black">
        <div className="text-zinc-600 dark:text-zinc-400">Loading...</div>
      </div>
    );
  }

  if (user) {
    return null;
  }

  const features = [
    {
      title: 'Automated Monitoring',
      description: 'We check your tracked services automatically. No manual work required.',
      icon: '🔍'
    },
    {
      title: 'Smart Change Detection',
      description: 'AI-powered detection filters out noise and focuses on meaningful price changes.',
      icon: '🤖'
    },
    {
      title: 'Instant Alerts',
      description: 'Get notified immediately when prices change, plans are removed, or free tiers disappear.',
      icon: '📧'
    },
    {
      title: 'Change History',
      description: 'Track all changes over time with detailed diffs and visual comparisons.',
      icon: '📊'
    },
    {
      title: 'Multiple Services',
      description: 'Monitor unlimited services with Pro plan. Track all your SaaS subscriptions.',
      icon: '🔗'
    },
    {
      title: 'Privacy First',
      description: 'Your data stays private. We only monitor public pricing pages.',
      icon: '🔒'
    }
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "Price Watchdogs",
    "description": "Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change.",
    "url": typeof window !== 'undefined' ? window.location.origin : "https://pricewatchdogs.com",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <nav className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-black dark:text-white">Price Watchdogs</h1>
            </div>
            <div className="flex items-center gap-4">
              {user ? (
                <button
                  onClick={() => router.push('/home')}
                  className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  Go to Home
                </button>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-sm font-medium text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/register"
                    className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main>
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-black dark:text-white mb-6">
              Never Miss a Price Change
            </h1>
            <p className="text-xl md:text-2xl text-zinc-600 dark:text-zinc-400 mb-8 max-w-3xl mx-auto">
              Monitor SaaS pricing pages and subscription changes. Know when prices or plans change before it costs you money.
            </p>
            <div className="flex gap-4 justify-center">
              {user ? (
                <button
                  onClick={() => router.push('/home')}
                  className="rounded-md bg-zinc-900 px-8 py-4 text-lg font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  Go to Home
                </button>
              ) : (
                <>
                  <Link
                    href="/register"
                    className="rounded-md bg-zinc-900 px-8 py-4 text-lg font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                  >
                    Get Started Free
                  </Link>
                  <Link
                    href="/pricing"
                    className="rounded-md border-2 border-zinc-300 px-8 py-4 text-lg font-medium text-zinc-900 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-50 dark:hover:bg-zinc-800"
                  >
                    View Pricing
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-zinc-50 dark:bg-zinc-900">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-center text-black dark:text-white mb-12">
              Everything You Need to Stay Informed
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-zinc-800 p-6 rounded-lg shadow-sm border border-zinc-200 dark:border-zinc-700"
                >
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold text-black dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-black dark:text-white mb-6">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-zinc-600 dark:text-zinc-400 mb-8">
              Start free, upgrade when you need more. No credit card required.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-zinc-50 dark:bg-zinc-900 p-6 rounded-lg border border-zinc-200 dark:border-zinc-700">
                <h3 className="text-xl font-semibold text-black dark:text-white mb-2">Free</h3>
                <div className="text-3xl font-bold text-black dark:text-white mb-4">$0</div>
                <ul className="text-left text-zinc-600 dark:text-zinc-400 space-y-2 mb-6">
                  <li>✓ Up to 3 services</li>
                  <li>✓ Daily or weekly checks</li>
                  <li>✓ Email alerts</li>
                  <li>✓ Change history</li>
                </ul>
                <Link
                  href="/register"
                  className="block w-full rounded-md bg-zinc-900 px-4 py-2 text-center text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  Get Started
                </Link>
              </div>
              <div className="bg-zinc-900 dark:bg-zinc-50 p-6 rounded-lg border-2 border-zinc-900 dark:border-zinc-50 relative">
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                    Most Popular
                  </span>
                </div>
                <h3 className="text-xl font-semibold text-white dark:text-black mb-2">Pro Monthly</h3>
                <div className="text-3xl font-bold text-white dark:text-black mb-4">$5<span className="text-lg">/mo</span></div>
                <ul className="text-left text-zinc-200 dark:text-zinc-800 space-y-2 mb-6">
                  <li>✓ Unlimited services</li>
                  <li>✓ Faster checks (twice daily)</li>
                  <li>✓ Email alerts</li>
                  <li>✓ Change history</li>
                  <li>✓ Priority support</li>
                </ul>
                <Link
                  href="/pricing"
                  className="block w-full rounded-md bg-white dark:bg-zinc-900 px-4 py-2 text-center text-sm font-medium text-zinc-900 dark:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800"
                >
                  Start Free Trial
                </Link>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-900 p-6 rounded-lg border border-zinc-200 dark:border-zinc-700">
                <h3 className="text-xl font-semibold text-black dark:text-white mb-2">Pro Annual</h3>
                <div className="text-3xl font-bold text-black dark:text-white mb-4">$50<span className="text-lg">/yr</span></div>
                <div className="text-sm text-green-600 dark:text-green-400 mb-2">Save $10 (17% off)</div>
                <ul className="text-left text-zinc-600 dark:text-zinc-400 space-y-2 mb-6">
                  <li>✓ Unlimited services</li>
                  <li>✓ Faster checks (twice daily)</li>
                  <li>✓ Email alerts</li>
                  <li>✓ Change history</li>
                  <li>✓ Priority support</li>
                </ul>
                <Link
                  href="/pricing"
                  className="block w-full rounded-md bg-zinc-900 px-4 py-2 text-center text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  Start Free Trial
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-zinc-900 dark:bg-black">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Ready to Never Miss a Price Change?
            </h2>
            <p className="text-xl text-zinc-300 mb-8">
              Start monitoring your SaaS subscriptions today. It's free to get started.
            </p>
            {!user && (
              <>
                <Link
                  href="/register"
                  className="inline-block rounded-md bg-white px-8 py-4 text-lg font-medium text-zinc-900 hover:bg-zinc-100"
                >
                  Get Started Free
                </Link>
              </>
            )}
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center text-zinc-600 dark:text-zinc-400">
          <p>&copy; {new Date().getFullYear()} Price Watchdogs. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

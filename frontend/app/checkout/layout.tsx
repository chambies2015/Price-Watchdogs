'use client';

import { useAuth } from '@/contexts/AuthContext';
import NavBar from '@/components/NavBar';
import Link from 'next/link';

export default function CheckoutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-zinc-600 dark:text-zinc-400">Loading...</div>
      </div>
    );
  }

  if (user) {
    return (
      <>
        <NavBar />
        {children}
      </>
    );
  }

  return (
    <>
      <nav className="border-b border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link
              href="/"
              className="text-xl font-bold text-zinc-900 hover:text-zinc-700 dark:text-zinc-50 dark:hover:text-zinc-300"
            >
              Price Watchdogs
            </Link>
            <Link
              href="/"
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </nav>
      {children}
    </>
  );
}

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { authApi } from '@/lib/api';

export default function ForgotPasswordPageClient() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.forgotPassword({ email });
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request password reset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black">
      <div className="w-full max-w-md space-y-6 rounded-lg bg-white p-8 shadow-lg dark:bg-zinc-900">
        <div>
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">Reset password</h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Enter your email and we’ll send you a reset link.
          </p>
        </div>
        {submitted ? (
          <div className="space-y-4">
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 dark:bg-green-900/20 dark:text-green-400">
              If an account exists for that email, a reset link has been sent.
            </div>
            <Link
              href="/login"
              className="block text-center text-sm font-medium text-zinc-900 hover:text-zinc-700 dark:text-zinc-50 dark:hover:text-zinc-200"
            >
              Back to sign in
            </Link>
          </div>
        ) : (
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
                placeholder="you@example.com"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
            <div className="text-center text-sm">
              <Link
                href="/login"
                className="font-medium text-zinc-900 hover:text-zinc-700 dark:text-zinc-50 dark:hover:text-zinc-200"
              >
                Back to sign in
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}


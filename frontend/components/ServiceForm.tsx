'use client';

import { useState } from 'react';
import { Service, ServiceCreate, ServiceUpdate, CheckFrequency } from '@/lib/api';

interface ServiceFormProps {
  initialData?: Service;
  onSubmit: (data: ServiceCreate | ServiceUpdate) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
}

export default function ServiceForm({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: ServiceFormProps) {
  const [name, setName] = useState(initialData?.name || '');
  const [url, setUrl] = useState(initialData?.url || '');
  const [checkFrequency, setCheckFrequency] = useState<CheckFrequency>(
    initialData?.check_frequency || 'daily'
  );
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validateUrl = (urlValue: string): boolean => {
    try {
      new URL(urlValue);
      return urlValue.startsWith('http://') || urlValue.startsWith('https://');
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!name.trim()) {
      setError('Service name is required');
      return;
    }
    
    if (!url.trim()) {
      setError('URL is required');
      return;
    }
    
    if (!validateUrl(url)) {
      setError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    
    setLoading(true);
    
    try {
      if (initialData) {
        await onSubmit({ name, url, check_frequency: checkFrequency, is_active: isActive });
      } else {
        await onSubmit({ name, url, check_frequency: checkFrequency });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save service');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}
      
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Service Name
        </label>
        <input
          id="name"
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
          placeholder="e.g., Stripe Pricing"
        />
      </div>
      
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Pricing Page URL
        </label>
        <input
          id="url"
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
          placeholder="https://example.com/pricing"
        />
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          The URL of the pricing or plans page to monitor
        </p>
      </div>
      
      <div>
        <label htmlFor="frequency" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Check Frequency
        </label>
        <select
          id="frequency"
          value={checkFrequency}
          onChange={(e) => setCheckFrequency(e.target.value as CheckFrequency)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </select>
      </div>
      
      {initialData && (
        <div className="flex items-center">
          <input
            id="is_active"
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-zinc-300 text-zinc-600 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-zinc-700 dark:text-zinc-300">
            Active (monitoring enabled)
          </label>
        </div>
      )}
      
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {loading ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}


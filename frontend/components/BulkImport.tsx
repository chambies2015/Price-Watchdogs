'use client';

import { useState } from 'react';
import { servicesApi, Service } from '@/lib/api';

interface BulkImportProps {
  onImportComplete: () => void;
}

export default function BulkImport({ onImportComplete }: BulkImportProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ created: number; failed: number; errors: string[]; services: Service[] } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      setFile(selectedFile);
      setError('');
      setResult(null);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    try {
      setLoading(true);
      setError('');
      const importResult = await servicesApi.importFromCsv(file);
      setResult(importResult);
      if (importResult.created > 0) {
        onImportComplete();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import services');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Upload CSV File
        </label>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="block w-full text-sm text-zinc-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900/20 dark:file:text-blue-300"
        />
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          CSV should have columns: name, url, check_frequency (optional), is_active (optional)
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-200">
          <p>Created: {result.created} services</p>
          {result.failed > 0 && (
            <>
              <p>Failed: {result.failed} rows</p>
              {result.errors.length > 0 && (
                <ul className="mt-2 list-disc list-inside">
                  {result.errors.slice(0, 10).map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                  {result.errors.length > 10 && <li>... and {result.errors.length - 10} more</li>}
                </ul>
              )}
            </>
          )}
        </div>
      )}

      <button
        onClick={handleImport}
        disabled={!file || loading}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Importing...' : 'Import Services'}
      </button>
    </div>
  );
}

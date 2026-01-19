'use client';

import { useState, useEffect } from 'react';
import { tagsApi, Tag, SortBy, SortOrder } from '@/lib/api';
import TagManager from './TagManager';

interface ServiceFiltersProps {
  onFilterChange: (filters: {
    tags: string[];
    isActive: boolean | null;
    sortBy: SortBy;
    sortOrder: SortOrder;
  }) => void;
}

export default function ServiceFilters({ onFilterChange }: ServiceFiltersProps) {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isActive, setIsActive] = useState<boolean | null>(null);
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  useEffect(() => {
    onFilterChange({ tags: selectedTags, isActive, sortBy, sortOrder });
  }, [selectedTags, isActive, sortBy, sortOrder, onFilterChange]);

  return (
    <div className="mb-6 space-y-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Filter by Tags
        </label>
        <TagManager
          onTagSelect={setSelectedTags}
          selectedTagIds={selectedTags}
          showCreate={true}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Status
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => setIsActive(isActive === true ? null : true)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              isActive === true
                ? 'bg-green-600 text-white'
                : 'border border-zinc-300 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setIsActive(isActive === false ? null : false)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              isActive === false
                ? 'bg-red-600 text-white'
                : 'border border-zinc-300 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800'
            }`}
          >
            Inactive
          </button>
          {(isActive !== null || selectedTags.length > 0) && (
            <button
              onClick={() => {
                setIsActive(null);
                setSelectedTags([]);
              }}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
            Sort By
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50"
          >
            <option value="name">Name</option>
            <option value="created_at">Created Date</option>
            <option value="last_checked_at">Last Checked</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
            Order
          </label>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as SortOrder)}
            className="block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50"
          >
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </div>
      </div>
    </div>
  );
}

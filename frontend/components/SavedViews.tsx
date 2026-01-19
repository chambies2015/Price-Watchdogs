'use client';

import { useState, useEffect } from 'react';
import { savedViewsApi, SavedView, SortBy, SortOrder } from '@/lib/api';

interface SavedViewsProps {
  currentFilters: {
    tags: string[];
    isActive: boolean | null;
    sortBy: SortBy;
    sortOrder: SortOrder;
  };
  onViewSelect: (view: SavedView) => void;
}

export default function SavedViews({ currentFilters, onViewSelect }: SavedViewsProps) {
  const [views, setViews] = useState<SavedView[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newViewName, setNewViewName] = useState('');

  useEffect(() => {
    loadViews();
  }, []);

  const loadViews = async () => {
    try {
      setLoading(true);
      const data = await savedViewsApi.list();
      setViews(data);
    } catch (err) {
      console.error('Failed to load saved views:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateView = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newViewName.trim()) return;

    try {
      const newView = await savedViewsApi.create({
        name: newViewName.trim(),
        filter_tags: currentFilters.tags.length > 0 ? currentFilters.tags : null,
        filter_active: currentFilters.isActive,
        sort_by: currentFilters.sortBy,
        sort_order: currentFilters.sortOrder,
      });
      setViews([newView, ...views]);
      setNewViewName('');
      setShowCreateForm(false);
    } catch (err) {
      console.error('Failed to create saved view:', err);
    }
  };

  const handleDeleteView = async (viewId: string) => {
    if (!confirm('Delete this saved view?')) return;

    try {
      await savedViewsApi.delete(viewId);
      setViews(views.filter(v => v.id !== viewId));
    } catch (err) {
      console.error('Failed to delete saved view:', err);
    }
  };

  if (loading) {
    return <div className="text-sm text-zinc-500 dark:text-zinc-400">Loading views...</div>;
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Saved Views
        </label>
        {!showCreateForm && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            + Save Current
          </button>
        )}
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreateView} className="mb-3 flex items-center gap-2">
          <input
            type="text"
            value={newViewName}
            onChange={(e) => setNewViewName(e.target.value)}
            placeholder="View name"
            className="flex-1 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
            autoFocus
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              setShowCreateForm(false);
              setNewViewName('');
            }}
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Cancel
          </button>
        </form>
      )}

      <div className="flex flex-wrap gap-2">
        {views.map(view => (
          <div key={view.id} className="flex items-center gap-1">
            <button
              onClick={() => onViewSelect(view)}
              className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
            >
              {view.name}
            </button>
            <button
              onClick={() => handleDeleteView(view.id)}
              className="text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

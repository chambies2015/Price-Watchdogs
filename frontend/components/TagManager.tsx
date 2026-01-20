'use client';

import { useEffect, useState } from 'react';
import { tagsApi, Tag } from '@/lib/api';

interface TagManagerProps {
  onTagSelect?: (tagIds: string[]) => void;
  selectedTagIds?: string[];
  showCreate?: boolean;
}

export default function TagManager({ onTagSelect, selectedTagIds = [], showCreate = true }: TagManagerProps) {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3b82f6');

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    try {
      setLoading(true);
      const data = await tagsApi.list();
      setTags(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tags');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    try {
      const newTag = await tagsApi.create({ name: newTagName.trim(), color: newTagColor });
      setTags([...tags, newTag]);
      setNewTagName('');
      setShowCreateForm(false);
      if (onTagSelect) {
        onTagSelect([...selectedTagIds, newTag.id]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tag');
    }
  };

  const handleDeleteTag = async (tagId: string) => {
    if (!confirm('Delete this tag? It will be removed from all services.')) return;

    try {
      await tagsApi.delete(tagId);
      setTags(tags.filter(t => t.id !== tagId));
      if (onTagSelect) {
        onTagSelect(selectedTagIds.filter(id => id !== tagId));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete tag');
    }
  };

  const toggleTag = (tagId: string) => {
    if (!onTagSelect) return;
    const newSelection = selectedTagIds.includes(tagId)
      ? selectedTagIds.filter(id => id !== tagId)
      : [...selectedTagIds, tagId];
    onTagSelect(newSelection);
  };

  if (loading) {
    return <div className="text-sm text-zinc-500 dark:text-zinc-400">Loading tags...</div>;
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="rounded-md bg-red-50 p-2 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {tags.map(tag => (
          <button
            key={tag.id}
            onClick={() => toggleTag(tag.id)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              selectedTagIds.includes(tag.id)
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
            }`}
            style={tag.color ? { backgroundColor: tag.color + '20', color: tag.color } : undefined}
          >
            <span>{tag.name}</span>
            {showCreate && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteTag(tag.id);
                }}
                className="ml-1 text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
              >
                ×
              </button>
            )}
          </button>
        ))}
      </div>

      {showCreate && (
        <>
          {!showCreateForm ? (
            <button
              onClick={() => setShowCreateForm(true)}
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              + Create tag
            </button>
          ) : (
            <form onSubmit={handleCreateTag} className="flex items-center gap-2">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="Tag name"
                className="flex-1 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
                autoFocus
              />
              <input
                type="color"
                value={newTagColor}
                onChange={(e) => setNewTagColor(e.target.value)}
                className="h-8 w-12 cursor-pointer rounded border border-zinc-300 dark:border-zinc-600"
              />
              <button
                type="submit"
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewTagName('');
                }}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                Cancel
              </button>
            </form>
          )}
        </>
      )}
    </div>
  );
}

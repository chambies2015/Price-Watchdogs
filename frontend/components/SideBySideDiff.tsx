'use client';

import { useState } from 'react';

interface SideBySideDiffProps {
  oldContent: string | null;
  newContent: string;
  className?: string;
}

export default function SideBySideDiff({ oldContent, newContent, className = '' }: SideBySideDiffProps) {
  const [syncedScroll, setSyncedScroll] = useState(true);
  
  const oldLines = oldContent ? oldContent.split('\n') : [];
  const newLines = newContent.split('\n');
  const maxLines = Math.max(oldLines.length, newLines.length);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>, side: 'left' | 'right') => {
    if (!syncedScroll) return;
    
    const scrollTop = e.currentTarget.scrollTop;
    const otherSide = side === 'left' ? 'right' : 'left';
    const otherElement = document.getElementById(`diff-${otherSide}`);
    if (otherElement) {
      otherElement.scrollTop = scrollTop;
    }
  };

  const getLineClass = (oldLine: string | undefined, newLine: string | undefined, index: number): string => {
    if (!oldLine && newLine) return 'bg-green-50 dark:bg-green-900/10';
    if (oldLine && !newLine) return 'bg-red-50 dark:bg-red-900/10';
    if (oldLine !== newLine) return 'bg-yellow-50 dark:bg-yellow-900/10';
    return '';
  };

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex gap-2">
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Before</span>
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">After</span>
        </div>
        <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <input
            type="checkbox"
            checked={syncedScroll}
            onChange={(e) => setSyncedScroll(e.target.checked)}
            className="rounded border-zinc-300"
          />
          Sync scroll
        </label>
      </div>
      <div className="flex gap-2 overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-700">
        <div
          id="diff-left"
          className="flex-1 overflow-auto bg-zinc-50 dark:bg-zinc-900"
          style={{ maxHeight: '600px' }}
          onScroll={(e) => handleScroll(e, 'left')}
        >
          <table className="w-full font-mono text-sm">
            <tbody>
              {Array.from({ length: maxLines }).map((_, index) => {
                const oldLine = oldLines[index];
                const lineClass = getLineClass(oldLine, newLines[index], index);
                return (
                  <tr key={`old-${index}`} className={lineClass}>
                    <td className="w-12 px-2 py-1 text-right text-zinc-500 dark:text-zinc-400">
                      {oldLine !== undefined ? index + 1 : ''}
                    </td>
                    <td className="px-2 py-1">
                      {oldLine !== undefined ? (
                        <span className={oldLine !== newLines[index] ? 'text-red-600 dark:text-red-400' : ''}>
                          {oldLine || '\u00A0'}
                        </span>
                      ) : (
                        <span className="text-zinc-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="w-px bg-zinc-200 dark:bg-zinc-700" />
        <div
          id="diff-right"
          className="flex-1 overflow-auto bg-white dark:bg-zinc-800"
          style={{ maxHeight: '600px' }}
          onScroll={(e) => handleScroll(e, 'right')}
        >
          <table className="w-full font-mono text-sm">
            <tbody>
              {Array.from({ length: maxLines }).map((_, index) => {
                const newLine = newLines[index];
                const lineClass = getLineClass(oldLines[index], newLine, index);
                return (
                  <tr key={`new-${index}`} className={lineClass}>
                    <td className="w-12 px-2 py-1 text-right text-zinc-500 dark:text-zinc-400">
                      {newLine !== undefined ? index + 1 : ''}
                    </td>
                    <td className="px-2 py-1">
                      {newLine !== undefined ? (
                        <span className={newLine !== oldLines[index] ? 'text-green-600 dark:text-green-400' : ''}>
                          {newLine || '\u00A0'}
                        </span>
                      ) : (
                        <span className="text-zinc-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


'use client';

import { useState } from 'react';
import SideBySideDiff from './SideBySideDiff';

interface DiffViewProps {
  oldContent: string | null;
  newContent: string;
  viewMode?: 'side-by-side' | 'unified';
  className?: string;
}

export default function DiffView({ oldContent, newContent, viewMode = 'side-by-side', className = '' }: DiffViewProps) {
  const [currentViewMode, setCurrentViewMode] = useState<'side-by-side' | 'unified'>(viewMode);

  const ViewModeToggle = () => (
    <div className="mb-4 flex items-center justify-end">
      <div className="flex gap-2 rounded-md border border-zinc-200 dark:border-zinc-700 p-1">
        <button
          onClick={() => setCurrentViewMode('side-by-side')}
          className={`rounded px-3 py-1 text-sm font-medium ${
            currentViewMode === 'side-by-side'
              ? 'bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900'
              : 'text-zinc-600 dark:text-zinc-400'
          }`}
        >
          Side-by-Side
        </button>
        <button
          onClick={() => setCurrentViewMode('unified')}
          className={`rounded px-3 py-1 text-sm font-medium ${
            currentViewMode === 'unified'
              ? 'bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900'
              : 'text-zinc-600 dark:text-zinc-400'
          }`}
        >
          Unified
        </button>
      </div>
    </div>
  );

  if (currentViewMode === 'side-by-side') {
    return (
      <div className={className}>
        <ViewModeToggle />
        <SideBySideDiff oldContent={oldContent} newContent={newContent} />
      </div>
    );
  }

  const oldLines = oldContent ? oldContent.split('\n') : [];
  const newLines = newContent.split('\n');
  const maxLines = Math.max(oldLines.length, newLines.length);

  return (
    <div className={className}>
      <ViewModeToggle />
      <div className="overflow-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800" style={{ maxHeight: '600px' }}>
        <table className="w-full font-mono text-sm">
          <tbody>
            {Array.from({ length: maxLines }).map((_, index) => {
              const oldLine = oldLines[index];
              const newLine = newLines[index];
              const isAdded = !oldLine && newLine;
              const isRemoved = oldLine && !newLine;
              const isModified = oldLine && newLine && oldLine !== newLine;

              let lineClass = '';
              let prefix = '';
              if (isAdded) {
                lineClass = 'bg-green-50 dark:bg-green-900/10';
                prefix = '+';
              } else if (isRemoved) {
                lineClass = 'bg-red-50 dark:bg-red-900/10';
                prefix = '-';
              } else if (isModified) {
                lineClass = 'bg-yellow-50 dark:bg-yellow-900/10';
                prefix = '~';
              } else {
                prefix = ' ';
              }

              return (
                <tr key={index} className={lineClass}>
                  <td className="w-8 px-2 py-1 text-right text-zinc-500 dark:text-zinc-400">
                    {prefix}
                  </td>
                  <td className="w-12 px-2 py-1 text-right text-zinc-500 dark:text-zinc-400">
                    {index + 1}
                  </td>
                  <td className="px-2 py-1">
                    {isAdded && <span className="text-green-600 dark:text-green-400">{newLine}</span>}
                    {isRemoved && <span className="text-red-600 dark:text-red-400">{oldLine}</span>}
                    {isModified && (
                      <>
                        <span className="text-red-600 dark:text-red-400 line-through">{oldLine}</span>
                        <br />
                        <span className="text-green-600 dark:text-green-400">{newLine}</span>
                      </>
                    )}
                    {!isAdded && !isRemoved && !isModified && (
                      <span className="text-zinc-700 dark:text-zinc-300">{newLine || oldLine || '\u00A0'}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}


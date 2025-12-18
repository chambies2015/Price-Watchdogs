import Link from 'next/link';

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export default function EmptyState({
  title,
  message,
  actionLabel,
  actionHref,
  onAction,
  icon,
}: EmptyStateProps) {
  const actionButton = actionLabel && (actionHref || onAction) && (
    actionHref ? (
      <Link
        href={actionHref}
        className="mt-4 inline-flex rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {actionLabel}
      </Link>
    ) : (
      <button
        onClick={onAction}
        className="mt-4 inline-flex rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {actionLabel}
      </button>
    )
  );

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
      {icon && <div className="mb-4 flex justify-center">{icon}</div>}
      <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{title}</h3>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">{message}</p>
      {actionButton}
    </div>
  );
}


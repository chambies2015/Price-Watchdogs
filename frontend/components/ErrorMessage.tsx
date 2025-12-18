interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({ message, onRetry, className = '' }: ErrorMessageProps) {
  return (
    <div className={`rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium">Error</p>
          <p className="mt-1 text-sm">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-4 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-800 dark:hover:bg-red-900"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}


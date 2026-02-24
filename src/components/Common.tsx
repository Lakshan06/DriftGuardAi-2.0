export function LoadingSpinner() {
  return (
    <div className="spinner-container">
      <div className="spinner" />
      <p>Loading...</p>
    </div>
  );
}

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-container">
      <p className="error-text">❌ {message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-secondary">
          Retry
        </button>
      )}
    </div>
  );
}
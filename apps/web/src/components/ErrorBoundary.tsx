import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in UI:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ maxWidth: '640px', margin: '40px auto', padding: '24px', background: 'var(--surface)', border: '2px solid var(--danger)' }}>
          <h2 style={{ color: 'var(--danger)', marginBottom: '12px' }}>Something went wrong</h2>
          <p style={{ color: 'var(--ink-2)', marginBottom: '16px', fontSize: 'var(--t-md)' }}>
            An unexpected error occurred while rendering this view.
          </p>
          <pre style={{ padding: '12px', background: 'var(--surface-sunk)', border: '1px solid var(--line)', fontSize: 'var(--t-sm)', overflowX: 'auto', marginBottom: '20px' }} className="mono">
            {this.state.error?.message || 'Unknown error'}
          </pre>
          <button
            type="button"
            className="btn btn--primary btn--md"
            onClick={() => window.location.reload()}
          >
            Reload Chaukas
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

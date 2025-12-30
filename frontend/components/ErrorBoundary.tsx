import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ERROR-BOUNDARY] ❌ Uncaught error caught:', error);
    console.error('[ERROR-BOUNDARY] Error name:', error.name);
    console.error('[ERROR-BOUNDARY] Error message:', error.message);
    console.error('[ERROR-BOUNDARY] Error stack:', error.stack);
    console.error('[ERROR-BOUNDARY] Component stack:', errorInfo.componentStack);
    this.setState({
      error,
      errorInfo,
    });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-white p-8">
          <div className="max-w-2xl w-full border-4 border-black p-8">
            <h1 className="text-4xl font-black uppercase tracking-tighter mb-4 text-black">
              Application Error
            </h1>
            <div className="bg-accent text-white p-4 border-2 border-black mb-4">
              <p className="font-bold uppercase text-sm mb-2">Error Details:</p>
              <pre className="text-xs font-mono overflow-auto">
                {this.state.error && this.state.error.toString()}
                {this.state.errorInfo && (
                  <>
                    {'\n\n'}
                    {this.state.errorInfo.componentStack}
                  </>
                )}
              </pre>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="bg-black text-white border-2 border-black px-6 py-3 font-bold uppercase tracking-wider hover:bg-accent hover:border-accent transition-colors"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;


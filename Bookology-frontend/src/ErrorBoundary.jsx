import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-black text-white flex items-center justify-center" aria-live="assertive">
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-8 max-w-md">
            <h2 className="text-xl font-bold text-red-400 mb-4">🚨 Something went wrong</h2>
            <p className="text-white/80 mb-4">
              The application encountered an error. Check the browser console for more details.
            </p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition"
            >
              Reload Page
            </button>
            <details className="mt-4">
              <summary className="text-red-400 cursor-pointer">Technical Details</summary>
              <pre className="text-xs mt-2 p-2 bg-black/50 rounded overflow-auto">
                {this.state.error?.toString()}
              </pre>
            </details>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
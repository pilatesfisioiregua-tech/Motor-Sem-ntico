import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="max-w-md text-center">
            <h2 className="text-xl font-semibold mb-2 text-[var(--text-primary)]">
              Algo ha ido mal
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mb-4">
              {this.state.error?.message || 'Error inesperado'}
            </p>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="px-4 py-2 rounded-[var(--radius-sm)] bg-[var(--accent-indigo)] text-white text-sm hover:opacity-90 transition"
            >
              Recargar
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

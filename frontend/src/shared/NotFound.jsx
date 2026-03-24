import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-[var(--bg-void)]">
      <div className="max-w-md text-center">
        <div className="text-6xl mb-4">404</div>
        <h2 className="text-xl font-semibold mb-2 text-[var(--text-primary)]">
          Pagina no encontrada
        </h2>
        <Link to="/" className="text-[var(--accent-indigo)] text-sm hover:underline">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

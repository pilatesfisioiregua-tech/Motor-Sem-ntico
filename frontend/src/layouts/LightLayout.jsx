import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';

export default function LightLayout({ children }) {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'light');
    return () => document.documentElement.removeAttribute('data-theme');
  }, []);

  return children || <Outlet />;
}

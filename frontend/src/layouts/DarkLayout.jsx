import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';

export default function DarkLayout() {
  useEffect(() => {
    document.documentElement.removeAttribute('data-theme');
  }, []);

  return <Outlet />;
}

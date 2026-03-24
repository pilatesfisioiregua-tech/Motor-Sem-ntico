import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import ErrorBoundary from './shared/ErrorBoundary';
import './App.css';

// Layouts
import DarkLayout from './layouts/DarkLayout';
import LightLayout from './layouts/LightLayout';

// Pages
import EstudioCockpit from './EstudioCockpit';
import Profundo from './Profundo';
import Onboarding from './Onboarding';
import PortalChat from './PortalChat';
import PortalPublico from './PortalPublico';
import NotFound from './shared/NotFound';

function App() {
  return (
    <AppProvider>
      <ErrorBoundary>
        <Routes>
          {/* Modo Estudio (dark) */}
          <Route element={<DarkLayout />}>
            <Route path="/" element={<EstudioCockpit />} />
            <Route path="/estudio" element={<EstudioCockpit />} />
            <Route path="/profundo" element={<Profundo />} />
          </Route>

          {/* Modo Cliente (light) */}
          <Route element={<LightLayout />}>
            <Route path="/portal/:token" element={<PortalChat />} />
            <Route path="/onboarding/:token" element={<Onboarding />} />
            <Route path="/info" element={<PortalPublico />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </AppProvider>
  );
}

export default App;

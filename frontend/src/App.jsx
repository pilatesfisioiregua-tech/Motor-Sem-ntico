import Onboarding from './Onboarding';
import PortalChat from './PortalChat';
import Profundo from './Profundo';
import PortalPublico from './PortalPublico';
import EstudioCockpit from './EstudioCockpit';
import './App.css';

function App() {
  // Routing simple: si la URL es /onboarding/{token}, mostrar formulario público
  const path = window.location.pathname;
  const portalMatch = path.match(/^\/portal\/(.+)$/);
  if (portalMatch) {
    return <PortalChat token={portalMatch[1]} />;
  }

  const onboardingMatch = path.match(/^\/onboarding\/(.+)$/);
  if (onboardingMatch) {
    return <Onboarding token={onboardingMatch[1]} />;
  }

  if (path === '/profundo') {
    return <Profundo />;
  }

  if (path === '/info') {
    return <PortalPublico />;
  }

  // Por defecto: Cockpit generativo (Modo Estudio)
  return <EstudioCockpit />;
}

export default App;

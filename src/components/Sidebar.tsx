import { Link, useLocation } from 'react-router-dom';

export function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <Link
          to="/dashboard"
          className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
        >
          📊 Dashboard
        </Link>
        <Link
          to="/command-center"
          className={`nav-link ${isActive('/command-center') ? 'active' : ''}`}
        >
          🎮 Command Center
        </Link>
        <Link
          to="/governance"
          className={`nav-link ${isActive('/governance') ? 'active' : ''}`}
        >
          ⚖️ Governance
        </Link>
        <Link
          to="/audit"
          className={`nav-link ${isActive('/audit') ? 'active' : ''}`}
        >
          📋 Audit Trail
        </Link>
      </nav>
    </aside>
  );
}
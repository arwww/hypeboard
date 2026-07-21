import { useEffect, useState, type PropsWithChildren } from 'react';
import { NavLink } from 'react-router-dom';

import { Logo } from './Logo';

export function AppShell({ children }: PropsWithChildren) {
  const [light, setLight] = useState(() => window.localStorage.getItem('hypeboard-theme') === 'light');

  useEffect(() => {
    document.documentElement.dataset.theme = light ? 'light' : 'dark';
    window.localStorage.setItem('hypeboard-theme', light ? 'light' : 'dark');
  }, [light]);

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Logo />
          <nav className="main-nav" aria-label="Primary navigation">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/methodology">Methodology</NavLink>
          </nav>
          <button
            className="icon-button"
            type="button"
            onClick={() => setLight((current) => !current)}
            aria-label={light ? 'Switch to dark mode' : 'Switch to light mode'}
            title={light ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {light ? '☾' : '☀'}
          </button>
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        <div className="container footer-inner">
          <Logo />
          <p>Public signals, transparent methods, no broker-level ownership claims.</p>
        </div>
      </footer>
    </div>
  );
}

import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="container page-space">
      <div className="state-panel">
        <span className="state-icon">404</span>
        <h1>Page not found</h1>
        <p>The requested Hypeboard route does not exist.</p>
        <Link className="primary-button" to="/">Return to dashboard</Link>
      </div>
    </div>
  );
}

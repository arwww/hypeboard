import { Link } from 'react-router-dom';

export function Logo() {
  return (
    <Link className="brand" to="/" aria-label="Hypeboard home">
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span>Hypeboard</span>
    </Link>
  );
}

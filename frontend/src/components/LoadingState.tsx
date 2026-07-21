export function LoadingState({ label = 'Loading market signals…' }: { label?: string }) {
  return (
    <div className="state-panel" role="status">
      <div className="loading-ring" aria-hidden="true" />
      <h2>{label}</h2>
      <p>Reading the latest validated static data files.</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state-panel state-error" role="alert">
      <span className="state-icon">!</span>
      <h2>Dashboard data could not be loaded</h2>
      <p>{message}</p>
      <p>Check that the pipeline generated frontend/public/data and that the deployment uses the Vite base path.</p>
    </div>
  );
}

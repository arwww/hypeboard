export function DisclaimerBanner({ notice }: { notice: string }) {
  return (
    <aside className="disclaimer-banner">
      <span className="disclaimer-icon" aria-hidden="true">i</span>
      <p>{notice}</p>
    </aside>
  );
}

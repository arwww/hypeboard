export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <span aria-hidden="true">⌁</span>
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}

export function DriverList({ drivers }: { drivers: string[] }) {
  if (drivers.length === 0) {
    return <p className="muted-copy">No validated drivers were generated for this observation.</p>;
  }
  return (
    <ul className="driver-list">
      {drivers.map((driver) => (
        <li key={driver}>
          <span aria-hidden="true" className="driver-marker" />
          <span>{driver}</span>
        </li>
      ))}
    </ul>
  );
}

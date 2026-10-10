export function RegainBySecond({ counts }: { counts: number[] }) {
  const max = Math.max(...counts, 1);
  return (
    <ol className="seconds" aria-label="Regains by second after the loss">
      {counts.map((n, bucket) => (
        <li
          key={bucket}
          data-late={bucket >= 5 ? "true" : undefined}
          data-cut={bucket === 5 ? "true" : undefined}
        >
          <span className="seconds-n">{n}</span>
          <span
            className="seconds-bar"
            style={{ height: `${Math.max(4, (n / max) * 100)}%` }}
          />
          <span className="seconds-label">{bucket}</span>
        </li>
      ))}
    </ol>
  );
}

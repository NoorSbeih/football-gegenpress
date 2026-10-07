export function ClockBeam({
  pressure,
  regain,
}: {
  pressure: number | null;
  regain: number | null;
}) {
  const width = 160;
  const mark = (seconds: number) => 8 + (Math.min(8, Math.max(0, seconds)) / 8) * (width - 16);
  return (
    <svg className="beam" viewBox={`0 0 ${width} 28`} aria-hidden="true">
      <line className="beam-rail" x1="8" y1="18" x2={width - 8} y2="18" />
      {[0, 5, 8].map((tick) => (
        <line
          key={tick}
          className={tick === 8 ? "beam-end" : "beam-tick"}
          x1={mark(tick)}
          y1={tick === 8 ? 10 : 14}
          x2={mark(tick)}
          y2="18"
        />
      ))}
      {pressure != null ? (
        <line className="beam-press" x1={mark(pressure)} y1="8" x2={mark(pressure)} y2="18" />
      ) : null}
      {regain != null ? <circle className="beam-regain" cx={mark(regain)} cy="18" r="3.5" /> : null}
    </svg>
  );
}

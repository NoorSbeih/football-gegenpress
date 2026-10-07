export function Scale({ label }: { label?: string }) {
  const ticks = [0, 5, 8];
  return (
    <svg
      className="scale"
      viewBox="0 0 88 16"
      role={label ? "img" : undefined}
      aria-hidden={label ? undefined : true}
      aria-label={label}
    >
      <line x1="4" y1="12" x2="84" y2="12" />
      {ticks.map((tick) => {
        const x = 4 + (tick / 8) * 80;
        const tall = tick === 8;
        return (
          <g key={tick}>
            <line x1={x} y1={tall ? 4 : 7} x2={x} y2="12" />
            <text x={x} y="4" textAnchor="middle">
              {tick}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

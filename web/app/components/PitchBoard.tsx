import type { PitchBin } from "@/lib/types";

const LINES = [
  "M 0 0 H 120 V 80 H 0 Z",
  "M 60 0 V 80",
  "M 18 18 H 0 V 62 H 18",
  "M 6 30 H 0 V 50 H 6",
  "M 102 18 H 120 V 62 H 102",
  "M 114 30 H 120 V 50 H 114",
];

export function PitchBoard({
  bins,
  title,
  empty,
}: {
  bins: PitchBin[];
  title: string;
  empty: string;
}) {
  const max = Math.max(1, ...bins.map((bin) => bin.n));
  return (
    <figure className="pitch">
      <figcaption>{title}</figcaption>
      <svg viewBox="-1 -1 122 82" role="img" aria-label={title}>
        {LINES.map((d) => (
          <path key={d} d={d} className="pitch-line" />
        ))}
        <circle cx="60" cy="40" r="9.15" className="pitch-line" />
        {bins.map((bin) => (
          <rect
            key={`${bin.bx}-${bin.bin_y}`}
            x={bin.bx * 10}
            y={bin.bin_y * 10}
            width="10"
            height="10"
            className={bin.layer === "loss" ? "cell-loss" : "cell-regain"}
            opacity={0.18 + 0.82 * (bin.n / max)}
          >
            <title>{`${bin.n} ${bin.layer === "loss" ? "losses" : "regains"}`}</title>
          </rect>
        ))}
      </svg>
      {bins.length === 0 ? <p className="empty">{empty}</p> : null}
      <p className="pitch-note">Attacking left to right. Darker square, more events.</p>
    </figure>
  );
}

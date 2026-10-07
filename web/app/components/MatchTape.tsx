import Link from "next/link";
import { clock, seconds, zoneLabel } from "@/lib/format";
import type { Turnover } from "@/lib/types";
import { ClockBeam } from "./ClockBeam";

export function MatchTape({ turnovers }: { turnovers: Turnover[] }) {
  if (turnovers.length === 0) {
    return <p className="empty">No live turnovers in this match.</p>;
  }
  return (
    <ol className="tape">
      {turnovers.map((row, index) => {
        const outcome = row.regained
          ? `won back ${seconds(row.time_to_regain_s)}`
          : "not back";
        const press = row.pressed
          ? `pressure ${seconds(row.time_to_pressure_s)}`
          : "no pressure";
        const ended = row.censored ? ", period ended" : "";
        return (
          <li key={`${row.period}-${row.minute}-${row.second}-${index}`}>
            <div className="tape-meta">
              <span className="tape-time">{clock(row.minute, row.second)}</span>
              <Link href={`/team/${row.team_id}`}>{row.team}</Link>
              <span>{zoneLabel(row.zone)}</span>
            </div>
            <ClockBeam
              pressure={row.pressed ? row.time_to_pressure_s : null}
              regain={row.regained ? row.time_to_regain_s : null}
            />
            <p className="tape-read">{`${press}. ${outcome}${ended}.`}</p>
          </li>
        );
      })}
    </ol>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { pct, seconds } from "@/lib/format";
import type { TeamRow } from "@/lib/types";

type SortKey =
  | "team"
  | "high_loss_regain_pct"
  | "regain_pct_8"
  | "median_time_to_pressure_8"
  | "live_turnovers";

const COLUMNS: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: "team", label: "Team", numeric: false },
  { key: "high_loss_regain_pct", label: "High-loss regain ≤8s", numeric: true },
  { key: "regain_pct_8", label: "Regain ≤8s", numeric: true },
  { key: "median_time_to_pressure_8", label: "Median time to pressure", numeric: true },
  { key: "live_turnovers", label: "Live losses", numeric: true },
];

export function TeamTable({ teams }: { teams: TeamRow[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("high_loss_regain_pct");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const ranked = teams.filter((team) => team.sufficient);
  const short = teams.filter((team) => !team.sufficient);
  const rows = [...ranked].sort((a, b) => compare(a, b, sortKey, direction));

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setDirection(key === "team" ? "asc" : "desc");
  }

  return (
    <div className="table-wrap">
      <table>
        <caption>World Cup 2022 teams, ranked by regains after a high loss.</caption>
        <thead>
          <tr>
            {COLUMNS.map((column) => {
              const active = column.key === sortKey;
              return (
                <th
                  key={column.key}
                  aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : "none"}
                  scope="col"
                >
                  <button type="button" onClick={() => onSort(column.key)}>
                    {column.label}
                    {active ? <span className="sort-mark">{direction === "asc" ? "↑" : "↓"}</span> : null}
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((team) => (
            <tr key={team.team_id}>
              <th scope="row">
                <Link href={`/team/${team.team_id}`}>{team.team}</Link>
              </th>
              <td className="num primary-num">
                {pct(team.high_loss_regain_pct)}
                <span className="n"> {team.n_high} high</span>
              </td>
              <td className="num">
                {pct(team.regain_pct_8)}
                <span className="n"> {team.live_turnovers} live</span>
              </td>
              <td className="num">
                {seconds(team.median_time_to_pressure_8)}
                <span className="n"> {pct(team.pressure_pct_8)} pressed</span>
              </td>
              <td className="num">{team.live_turnovers}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {short.length > 0 ? (
        <p className="short-sample">
          Not enough live turnovers: {short.map((team) => team.team).join(", ")}.
        </p>
      ) : null}
    </div>
  );
}

function compare(a: TeamRow, b: TeamRow, key: SortKey, direction: "asc" | "desc"): number {
  const left = a[key];
  const right = b[key];
  const factor = direction === "asc" ? 1 : -1;
  if (typeof left === "string" && typeof right === "string") {
    return left.localeCompare(right) * factor;
  }
  if (left == null && right == null) {
    return 0;
  }
  if (left == null) {
    return 1;
  }
  if (right == null) {
    return -1;
  }
  return ((left as number) - (right as number)) * factor;
}

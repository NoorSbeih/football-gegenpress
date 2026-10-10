"use client";

import { useState } from "react";
import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { pct } from "@/lib/format";
import type { PitchFile, TeamRow } from "@/lib/types";
import { PitchBoard } from "./PitchBoard";

export function TeamView({ team, pitch }: { team: TeamRow; pitch: PitchFile }) {
  const [windowSeconds, setWindowSeconds] = useState<5 | 8>(8);
  const losses = pitch.bins.filter((bin) => bin.layer === "loss");
  const regains = pitch.bins.filter(
    (bin) => bin.layer === "regain" && bin.window_s === windowSeconds,
  );
  const buckets = Array.from({ length: windowSeconds === 8 ? 8 : 5 }, (_, bucket) => ({
    label: `${bucket}`,
    n: pitch.histogram.find((bin) => bin.window_s === windowSeconds && bin.bucket === bucket)?.n ?? 0,
  }));
  const regainCount = buckets.reduce((sum, bin) => sum + bin.n, 0);

  return (
    <>
      <div className="split" aria-label="High losses against low losses">
        <p>
          <span>Opponent&apos;s third</span>
          <strong>{pct(team.high_loss_regain_pct)}</strong>
          <em>{team.n_high} high losses</em>
        </p>
        <p>
          <span>Own third</span>
          <strong>{pct(team.low_loss_regain_pct)}</strong>
          <em>{team.n_low} low losses</em>
        </p>
      </div>
      <div className="window-toggle" role="group" aria-label="Regain window">
        <button
          type="button"
          aria-pressed={windowSeconds === 5}
          onClick={() => setWindowSeconds(5)}
        >
          5 seconds
        </button>
        <button
          type="button"
          aria-pressed={windowSeconds === 8}
          onClick={() => setWindowSeconds(8)}
        >
          8 seconds
        </button>
      </div>
      <div className="pitches">
        <PitchBoard bins={losses} title="Where they lost it" empty="No located losses." />
        <PitchBoard
          bins={regains}
          title={`Where they won it back, within ${windowSeconds}s`}
          empty={`No regains inside ${windowSeconds} seconds.`}
        />
      </div>
      <p className="definition">
        Opponent&apos;s third is the gegenpress: the ball was lost while attacking. Own third is
        defending, and {team.n_low} {team.n_low === 1 ? "loss is" : "losses are"} a small sample.
        The clock starts at the last touch before a live loss. Restarts never start it.
      </p>
      <section className="chart-block" aria-labelledby="hist-title">
        <h2 id="hist-title">Won back, by second</h2>
        {regainCount === 0 ? (
          <p className="empty">No regains inside {windowSeconds} seconds.</p>
        ) : (
          <div className="chart">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={buckets} margin={{ top: 24, right: 8, left: 0, bottom: 8 }}>
                <XAxis dataKey="label" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} width={28} tickLine={false} axisLine={false} />
                <Bar dataKey="n" fill="var(--accent)" isAnimationActive={false}>
                  <LabelList dataKey="n" position="top" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    </>
  );
}

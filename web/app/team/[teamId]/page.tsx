import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { TeamView } from "../../components/TeamView";
import { getPitch, getTeam, getTeams } from "@/lib/data";
import { pct, seconds } from "@/lib/format";

type Params = { teamId: string };

export const dynamicParams = false;

export function generateStaticParams() {
  return getTeams().map((team) => ({ teamId: String(team.team_id) }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { teamId } = await params;
  const team = getTeam(Number(teamId));
  return { title: team ? `${team.team} · Gegenpress` : "Gegenpress" };
}

export default async function TeamPage({ params }: { params: Promise<Params> }) {
  const { teamId } = await params;
  const team = getTeam(Number(teamId));
  if (!team) {
    notFound();
  }
  if (!team.sufficient) {
    return (
      <main>
        <h1>{team.team}</h1>
        <p className="empty">Not enough live turnovers.</p>
      </main>
    );
  }
  const pitch = getPitch(team.team_id);
  return (
    <main>
      <p className="kicker">World Cup 2022</p>
      <h1>{team.team}</h1>
      <p className="lede">
        {`Pressure arrived on ${pct(team.pressure_pct_8)} of ${team.live_turnovers} live losses${
          team.median_time_to_pressure_8 != null
            ? `, median ${seconds(team.median_time_to_pressure_8)}`
            : ""
        }. They won the ball back within 8 seconds ${team.n_regained_8} times.`}
      </p>
      <TeamView team={team} pitch={pitch} />
    </main>
  );
}

import { TeamTable } from "./components/TeamTable";
import { getCompetition, getTeams } from "@/lib/data";
import { pct } from "@/lib/format";

export default function HomePage() {
  const competition = getCompetition();
  const teams = getTeams();
  return (
    <main>
      <p className="kicker">{competition.name}</p>
      <h1>The eight seconds after a team loses the ball.</h1>
      <p className="lede">
        {competition.live_turnovers.toLocaleString("en-US")} live losses.{" "}
        {competition.excluded_restarts.toLocaleString("en-US")} restarts left out.{" "}
        {pct(competition.pressure_pct_8)} drew a pressure. {pct(competition.regain_pct_8)} were won
        back inside eight seconds. The table ranks the high losses — the ball given away in the
        opponent&apos;s third.
      </p>
      <TeamTable teams={teams} />
    </main>
  );
}

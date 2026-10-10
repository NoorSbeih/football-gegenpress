import Link from "next/link";
import { RegainBySecond } from "./components/RegainBySecond";
import { TeamTable } from "./components/TeamTable";
import { getCompetition, getRegainBySecond, getTeams } from "@/lib/data";
import { pct } from "@/lib/format";
import { highLossEnds, listWithAnd } from "@/lib/story";

export default function HomePage() {
  const competition = getCompetition();
  const teams = getTeams();
  const bySecond = getRegainBySecond();
  const { leader, zeros } = highLossEnds(teams);
  const beforeFive = bySecond.slice(0, 5).reduce((sum, n) => sum + n, 0);
  const afterFive = bySecond.slice(5).reduce((sum, n) => sum + n, 0);
  const zeroDetail = listWithAnd(zeros.map((team) => `${team.team} (${team.n_high})`));

  return (
    <main>
      <p className="kicker">{competition.name}</p>
      <h1>The press arrives. The ball usually does not.</h1>
      <p className="lede">
        Eight seconds after a live loss. Of {competition.live_turnovers.toLocaleString("en-US")}{" "}
        losses, {pct(competition.pressure_pct_8)} drew a pressure.{" "}
        {pct(competition.regain_pct_8)} were won back inside the window, and{" "}
        {pct(competition.regain_pct_5)} inside five seconds. Throw-ins, goal kicks, free kicks, and
        the other restarts are left out — {competition.excluded_restarts.toLocaleString("en-US")}{" "}
        of them.
      </p>

      <section className="reading" aria-labelledby="when-title">
        <h2 id="when-title">When the ball came back</h2>
        <p>
          {beforeFive + afterFive} regains inside eight seconds. {beforeFive} landed before five
          seconds, and {afterFive} landed after. The bars from five onward are the ones a
          five-second rule would drop.
        </p>
        <RegainBySecond counts={bySecond} />
        <p className="definition">
          Each bar is a whole second after the loss. StatsBomb&apos;s own counterpress tag fires
          on {pct(competition.counterpress_share)} of the same losses, close to the{" "}
          {pct(competition.pressure_pct_8)} pressure rate.
        </p>
      </section>

      <section className="reading" aria-labelledby="rank-title">
        <h2 id="rank-title">The ranking is the high loss</h2>
        <p>
          A high loss is the ball given away in the opponent&apos;s third. The first column is
          regains divided by those losses only.{" "}
          <Link href={`/team/${leader.team_id}`}>{leader.team}</Link> won back{" "}
          {pct(leader.high_loss_regain_pct)} of {leader.n_high}.
          {zeros.length > 0 ? ` ${zeroDetail} won none back.` : ""}{" "}
          A loss in a team&apos;s own third is on the team page. Winning that back is defending,
          and those counts are often under ten.
        </p>
      </section>

      <TeamTable teams={teams} />
    </main>
  );
}

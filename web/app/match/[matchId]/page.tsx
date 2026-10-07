import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { MatchPicker } from "../../components/MatchPicker";
import { MatchTape } from "../../components/MatchTape";
import { getMatch, getMatchIndex } from "@/lib/data";

type Params = { matchId: string };

export function generateStaticParams() {
  return getMatchIndex().map((match) => ({ matchId: String(match.match_id) }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { matchId } = await params;
  const match = getMatch(Number(matchId));
  return { title: match ? `${match.label} · Gegenpress` : "Gegenpress" };
}

export default async function MatchPage({ params }: { params: Promise<Params> }) {
  const { matchId } = await params;
  const match = getMatch(Number(matchId));
  if (!match) {
    notFound();
  }
  const index = getMatchIndex();
  return (
    <main>
      <p className="kicker">
        {match.date} · {match.stage}
      </p>
      <h1>{match.label}</h1>
      <p className="lede">
        Each row is a live loss. The tick is the first pressure. The dot is the regain, if it
        came inside eight seconds. {match.turnovers.length} live losses in this match.
      </p>
      <MatchPicker matches={index} current={match.match_id} />
      <MatchTape turnovers={match.turnovers} />
    </main>
  );
}

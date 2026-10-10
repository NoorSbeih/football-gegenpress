import fs from "fs";
import path from "path";
import type { Competition, MatchFile, MatchIndex, PitchFile, TeamRow } from "./types";

type CompetitionFile = { competitions: Competition[] };
type TeamFile = { competition: string; teams: TeamRow[] };

function readJson<T>(parts: string[]): T {
  const full = path.join(process.cwd(), "public", "data", ...parts);
  return JSON.parse(fs.readFileSync(full, "utf8")) as T;
}

export function getCompetition(): Competition {
  return readJson<CompetitionFile>(["competitions.json"]).competitions[0];
}

export function getTeams(): TeamRow[] {
  return readJson<TeamFile>(["teams", "wc2022.json"]).teams;
}

/** Tournament regain counts by whole second, summed from the team histograms. */
export function getRegainBySecond(): number[] {
  const counts = Array.from({ length: 8 }, () => 0);
  const dir = path.join(process.cwd(), "public", "data", "pitches");
  for (const file of fs.readdirSync(dir)) {
    if (!file.endsWith(".json")) {
      continue;
    }
    const pitch = JSON.parse(fs.readFileSync(path.join(dir, file), "utf8")) as PitchFile;
    for (const bin of pitch.histogram) {
      if (bin.window_s === 8 && bin.bucket >= 0 && bin.bucket < 8) {
        counts[bin.bucket] += bin.n;
      }
    }
  }
  return counts;
}

export function getTeam(teamId: number): TeamRow | undefined {
  return getTeams().find((team) => team.team_id === teamId);
}

export function getPitch(teamId: number): PitchFile {
  return readJson<PitchFile>(["pitches", `${teamId}.json`]);
}

export function getMatchIndex(): MatchIndex[] {
  return readJson<MatchIndex[]>(["matches", "index.json"]);
}

export function getMatch(matchId: number): MatchFile | undefined {
  const full = path.join(process.cwd(), "public", "data", "matches", `${matchId}.json`);
  if (!fs.existsSync(full)) {
    return undefined;
  }
  return JSON.parse(fs.readFileSync(full, "utf8")) as MatchFile;
}

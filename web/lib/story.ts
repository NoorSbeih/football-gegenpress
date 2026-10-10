import type { TeamRow } from "./types";

export function highLossEnds(teams: TeamRow[]): { leader: TeamRow; zeros: TeamRow[] } {
  const ranked = teams.filter((team) => team.sufficient && team.high_loss_regain_pct != null);
  const leader = [...ranked].sort(
    (a, b) =>
      (b.high_loss_regain_pct ?? 0) - (a.high_loss_regain_pct ?? 0) || b.n_high - a.n_high,
  )[0];
  const zeros = ranked
    .filter((team) => team.high_loss_regain_pct === 0)
    .sort((a, b) => b.n_high - a.n_high);
  return { leader, zeros };
}

export function listWithAnd(parts: string[]): string {
  if (parts.length <= 1) {
    return parts[0] ?? "";
  }
  return `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
}

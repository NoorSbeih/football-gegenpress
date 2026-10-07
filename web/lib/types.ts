export type Competition = {
  key: string;
  name: string;
  competition_id: number;
  season_id: number;
  live_turnovers: number;
  excluded_restarts: number;
  unlocated: number;
  regain_pct_5: number;
  regain_pct_8: number;
  pressure_pct_8: number;
  counterpress_share: number;
  default_match_id: number;
  default_match_label: string;
};

export type TeamRow = {
  team_id: number;
  team: string;
  competition: string;
  live_turnovers: number;
  excluded_restarts: number;
  regain_pct_5: number | null;
  regain_pct_8: number | null;
  median_time_to_regain_8: number | null;
  pressure_pct_8: number | null;
  median_time_to_pressure_8: number | null;
  high_turnover_share: number | null;
  n_high: number;
  n_low: number;
  high_loss_regain_pct: number | null;
  low_loss_regain_pct: number | null;
  mean_regain_x: number | null;
  counterpress_share: number | null;
  n_regained_8: number;
  sufficient: boolean;
};

export type PitchBin = {
  layer: "loss" | "regain";
  window_s: number;
  bx: number;
  bin_y: number;
  n: number;
};

export type HistBin = {
  window_s: number;
  bucket: number;
  n: number;
};

export type PitchFile = {
  team_id: number;
  team: string;
  bins: PitchBin[];
  histogram: HistBin[];
};

export type Turnover = {
  period: number;
  minute: number;
  second: number;
  team: string;
  team_id: number;
  zone: string;
  regained: boolean;
  time_to_regain_s: number | null;
  pressed: boolean;
  time_to_pressure_s: number | null;
  censored: boolean;
  loss_x: number | null;
  loss_y: number | null;
  regain_x: number | null;
  regain_y: number | null;
};

export type MatchFile = {
  match_id: number;
  date: string;
  stage: string;
  home_team: string;
  away_team: string;
  home_team_id: number;
  away_team_id: number;
  home_score: number;
  away_score: number;
  label: string;
  turnovers: Turnover[];
};

export type MatchIndex = {
  match_id: number;
  date: string;
  stage: string;
  label: string;
  home_team_id: number;
  away_team_id: number;
};

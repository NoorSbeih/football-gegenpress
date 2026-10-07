export function pct(value: number | null | undefined): string {
  if (value == null) {
    return "—";
  }
  return `${value.toFixed(1)}%`;
}

export function seconds(value: number | null | undefined): string {
  if (value == null) {
    return "—";
  }
  return `${value.toFixed(1)}s`;
}

export function clock(minute: number, second: number): string {
  return `${minute}:${String(second).padStart(2, "0")}`;
}

export function zoneLabel(zone: string): string {
  if (zone === "own_third") {
    return "own third";
  }
  if (zone === "opp_third") {
    return "opponent third";
  }
  if (zone === "middle") {
    return "middle third";
  }
  return zone;
}

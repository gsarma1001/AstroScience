export type DashaLevel =
  | "mahadasha"
  | "antardasha"
  | "pratyantardasha"
  | "sukshma";

export type DashaParent = {
  period_id: string;
  level: DashaLevel;
  planet: string;
};

export type DashaPeriod = {
  period_id: string;
  level: DashaLevel;
  planet: string;
  starts_at: string;
  ends_at: string;
  duration_seconds: number;
  duration_years: number;
  parent_period: DashaParent | null;
  children: DashaPeriod[];
};

export type DashaSequence = {
  chart_id: string;
  moon_sidereal_longitude: number;
  birth_nakshatra: string;
  nakshatra_lord: string;
  elapsed_nakshatra_fraction: number;
  balance_at_birth_years: number;
  year_length_days: number;
  year_length_convention: string;
  sequence_starts_at: string;
  sequence_ends_at: string;
  mahadashas: DashaPeriod[];
};

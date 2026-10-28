export type ZodiacSign =
  | "Aries"
  | "Taurus"
  | "Gemini"
  | "Cancer"
  | "Leo"
  | "Virgo"
  | "Libra"
  | "Scorpio"
  | "Sagittarius"
  | "Capricorn"
  | "Aquarius"
  | "Pisces";

export type ChartPlacement = {
  name: string;
  sign: ZodiacSign;
  house: number;
  degree_in_sign: number;
};

export type ChartHouse = {
  number: number;
  sign: ZodiacSign;
  occupants: string[];
};

export type DivisionChart = {
  division: string;
  ascendant_sign: ZodiacSign;
  houses: ChartHouse[];
  placements: ChartPlacement[];
};

export type PlanetPosition = {
  name: string;
  sidereal_longitude: number;
  zodiac_sign: ZodiacSign;
  degree_in_sign: number;
  house: number;
  nakshatra: string;
  nakshatra_pada: number;
  retrograde: boolean | null;
};

export type VedicChartData = {
  ascendant: PlanetPosition;
  planets: Record<string, PlanetPosition>;
  moon_rashi: ZodiacSign;
  lagna: ZodiacSign;
  birth_nakshatra: string;
  nakshatra_lord: string;
  d1_rashi_chart: DivisionChart;
  d9_navamsa: DivisionChart;
  d10_dashamsa: DivisionChart;
};

export type ChartDivision = "d1" | "d9" | "d10";
export type ChartStyle = "south-indian" | "north-indian";

export const ZODIAC_SIGNS: ZodiacSign[] = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
];

export const DIVISION_LABELS: Record<ChartDivision, string> = {
  d1: "D1 Rashi",
  d9: "D9 Navamsha",
  d10: "D10 Dashamsha",
};

export function getDivisionChart(
  chart: VedicChartData,
  division: ChartDivision,
): DivisionChart {
  switch (division) {
    case "d1":
      return chart.d1_rashi_chart;
    case "d9":
      return chart.d9_navamsa;
    case "d10":
      return chart.d10_dashamsa;
  }
}

export function formatDegrees(degrees: number): string {
  const totalSeconds = Math.round(degrees * 3600);
  const wholeDegrees = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${wholeDegrees}° ${String(minutes).padStart(2, "0")}′ ${String(seconds).padStart(2, "0")}″`;
}

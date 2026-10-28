import { ChartCell } from "@/components/vedic-chart/chart-cell";
import { DivisionChart, ZODIAC_SIGNS } from "@/components/vedic-chart/types";

type SouthIndianChartProps = {
  chart: DivisionChart;
  selectedName: string | null;
  onSelect: (name: string) => void;
};

const SIGN_GRID: Record<string, number> = {
  Pisces: 0,
  Aries: 1,
  Taurus: 2,
  Gemini: 3,
  Aquarius: 4,
  Cancer: 7,
  Capricorn: 8,
  Leo: 11,
  Sagittarius: 12,
  Scorpio: 13,
  Libra: 14,
  Virgo: 15,
};

export function SouthIndianChart({
  chart,
  selectedName,
  onSelect,
}: SouthIndianChartProps) {
  const housesBySign = new Map(chart.houses.map((house) => [house.sign, house]));
  const placementsBySign = new Map<string, typeof chart.placements>();
  for (const placement of chart.placements) {
    const placements = placementsBySign.get(placement.sign) ?? [];
    placements.push(placement);
    placementsBySign.set(placement.sign, placements);
  }

  return (
    <svg
      aria-label={`South Indian ${chart.division} chart`}
      className="vedic-chart-svg south-chart-svg"
      role="group"
      viewBox="0 0 640 640"
    >
      <title>South Indian chart with fixed zodiac sign compartments</title>
      <rect className="chart-outer-frame" height="600" width="600" x="20" y="20" />
      {ZODIAC_SIGNS.map((sign, index) => {
        const gridIndex = SIGN_GRID[sign];
        const column = gridIndex % 4;
        const row = Math.floor(gridIndex / 4);
        const x = 20 + column * 150;
        const y = 20 + row * 150;
        const house = housesBySign.get(sign);
        return (
          <ChartCell
            house={house?.number ?? 0}
            key={sign}
            onSelect={onSelect}
            placements={placementsBySign.get(sign) ?? []}
            selectedName={selectedName}
            sign={sign}
            signNumber={index + 1}
            x={x}
            y={y}
          />
        );
      })}
      <g aria-hidden="true" className="chart-center-label">
        <text textAnchor="middle" x="320" y="289">NAKSHATRA AI</text>
        <text textAnchor="middle" x="320" y="322">{chart.division.toUpperCase()}</text>
        <text textAnchor="middle" x="320" y="353">VEDIC CHART</text>
      </g>
    </svg>
  );
}

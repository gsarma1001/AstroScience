import { ChartPlacement, DivisionChart, ZODIAC_SIGNS } from "@/components/vedic-chart/types";

type NorthIndianChartProps = {
  chart: DivisionChart;
  selectedName: string | null;
  onSelect: (name: string) => void;
};

type HouseRegion = {
  house: number;
  points: string;
  x: number;
  y: number;
};

const HOUSE_REGIONS: HouseRegion[] = [
  { house: 1, points: "200,0 300,100 200,200 100,100", x: 200, y: 70 },
  { house: 2, points: "0,0 200,0 100,100", x: 100, y: 31 },
  { house: 3, points: "0,0 100,100 0,200", x: 35, y: 100 },
  { house: 4, points: "0,200 100,100 200,200 100,300", x: 70, y: 200 },
  { house: 5, points: "0,200 0,400 100,300", x: 35, y: 300 },
  { house: 6, points: "0,400 200,400 100,300", x: 100, y: 370 },
  { house: 7, points: "200,200 300,300 200,400 100,300", x: 200, y: 330 },
  { house: 8, points: "200,400 400,400 300,300", x: 300, y: 370 },
  { house: 9, points: "400,200 400,400 300,300", x: 365, y: 300 },
  { house: 10, points: "400,200 300,100 200,200 300,300", x: 330, y: 200 },
  { house: 11, points: "400,0 400,200 300,100", x: 365, y: 100 },
  { house: 12, points: "200,0 400,0 300,100", x: 300, y: 31 },
];

const CENTER_X = 220;
const CENTER_Y = 220;

function centeredRegion(region: HouseRegion): HouseRegion {
  return {
    ...region,
    points: region.points
      .split(" ")
      .map((point) => {
        const [x, y] = point.split(",").map(Number);
        return `${x + 20},${y + 20}`;
      })
      .join(" "),
    x: region.x + 20,
    y: region.y + 20,
  };
}

export function NorthIndianChart({
  chart,
  selectedName,
  onSelect,
}: NorthIndianChartProps) {
  const placementsByHouse = new Map<number, ChartPlacement[]>();
  for (const placement of chart.placements) {
    const placements = placementsByHouse.get(placement.house) ?? [];
    placements.push(placement);
    placementsByHouse.set(placement.house, placements);
  }

  return (
    <svg
      aria-label={`North Indian ${chart.division} chart`}
      className="vedic-chart-svg north-chart-svg"
      role="group"
      viewBox="0 0 440 440"
    >
      <title>North Indian chart with fixed houses in a diamond layout</title>
      <rect className="chart-outer-frame" height="400" width="400" x="20" y="20" />
      <path className="chart-diamond-line" d="M220 20 420 220 220 420 20 220Z" />
      <path className="chart-diamond-line" d="M20 20 220 220 420 20M420 420 220 220 20 420" />
      {HOUSE_REGIONS.map((rawRegion) => {
        const region = centeredRegion(rawRegion);
        const placements = placementsByHouse.get(region.house) ?? [];
        const sign = chart.houses.find((house) => house.number === region.house)?.sign;
        const signNumber = sign ? ZODIAC_SIGNS.indexOf(sign) + 1 : null;
        return (
          <g
            aria-label={`House ${region.house}${sign ? `, ${sign}` : ""}`}
            className="north-house"
            key={region.house}
          >
            <polygon className="north-house-region" points={region.points} />
            {signNumber !== null && (
              <text className="north-sign-number" textAnchor="middle" x={region.x} y={region.y - 20}>
                {signNumber}
              </text>
            )}
            <text className="north-house-number" textAnchor="middle" x={region.x} y={region.y - 7}>
              H{region.house}
            </text>
            {placements.map((placement, index) => {
              const isSelected = selectedName === placement.name;
              return (
                <g
                  aria-label={`${placement.name}, ${placement.sign}, house ${placement.house}, ${placement.degree_in_sign.toFixed(2)} degrees`}
                  className={isSelected ? "chart-placement selected" : "chart-placement"}
                  key={placement.name}
                  onClick={() => onSelect(placement.name)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(placement.name);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <title>
                    {placement.name} · {placement.sign} · House {placement.house} ·{" "}
                    {placement.degree_in_sign.toFixed(2)}°
                  </title>
                  <text
                    className="north-planet-label"
                    textAnchor="middle"
                    x={region.x}
                    y={region.y + 12 + index * 16}
                  >
                    {placement.name === "Ascendant" ? "Asc" : placement.name}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}
      <g aria-hidden="true" className="north-chart-center">
        <text textAnchor="middle" x={CENTER_X + 20} y={CENTER_Y + 16}>
          {chart.division.toUpperCase()}
        </text>
      </g>
    </svg>
  );
}

import { ChartPlacement, ZodiacSign } from "@/components/vedic-chart/types";

type ChartCellProps = {
  house: number;
  onSelect: (name: string) => void;
  placements: ChartPlacement[];
  selectedName: string | null;
  sign: ZodiacSign;
  signNumber: number;
  x: number;
  y: number;
};

export function ChartCell({
  house,
  onSelect,
  placements,
  selectedName,
  sign,
  signNumber,
  x,
  y,
}: ChartCellProps) {
  const isAscendantSign = placements.some((placement) => placement.name === "Ascendant");
  return (
    <g className={isAscendantSign ? "south-sign-cell ascendant-sign" : "south-sign-cell"}>
      <rect height="150" width="150" x={x} y={y} />
      <text className="south-sign-number" x={x + 12} y={y + 19}>{signNumber}</text>
      <text className="south-sign-name" textAnchor="middle" x={x + 75} y={y + 25}>{sign}</text>
      {house > 0 && (
        <text className="south-house-number" textAnchor="end" x={x + 137} y={y + 19}>
          H{house}
        </text>
      )}
      {isAscendantSign && (
        <text className="south-ascendant-marker" textAnchor="middle" x={x + 75} y={y + 43}>
          LAGNA
        </text>
      )}
      {placements.map((placement, index) => {
        const isSelected = selectedName === placement.name;
        const degree = `${placement.degree_in_sign.toFixed(2)}°`;
        return (
          <g
            aria-label={`${placement.name}, ${placement.sign}, house ${placement.house}, ${degree}`}
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
              {placement.name} · {placement.sign} · House {placement.house} · {degree}
            </title>
            <text
              className="south-planet-label"
              textAnchor="middle"
              x={x + 75}
              y={y + (isAscendantSign ? 65 : 54) + index * 19}
            >
              {placement.name === "Ascendant" ? "Ascendant" : placement.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

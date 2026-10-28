"use client";

import { useState } from "react";
import { NorthIndianChart } from "@/components/vedic-chart/north-indian-chart";
import { SouthIndianChart } from "@/components/vedic-chart/south-indian-chart";
import { PLANET_MEANINGS } from "@/components/vedic-chart/planet-meanings";
import {
  ChartDivision,
  ChartStyle,
  DIVISION_LABELS,
  formatDegrees,
  getDivisionChart,
  VedicChartData,
} from "@/components/vedic-chart/types";

type VedicChartViewerProps = {
  chart: VedicChartData | null;
};

const GLOSSARY = [
  {
    term: "Lagna",
    definition: "The Ascendant sign; the starting point for counting chart houses.",
  },
  {
    term: "Rashi",
    definition: "One of the twelve zodiac signs. Moon Rashi is the sign occupied by the Moon.",
  },
  {
    term: "Nakshatra",
    definition: "One of 27 lunar mansions along the sidereal zodiac.",
  },
  {
    term: "Houses",
    definition: "Twelve life areas counted from the Ascendant sign in a whole-sign chart.",
  },
];

export function VedicChartViewer({ chart }: VedicChartViewerProps) {
  const [division, setDivision] = useState<ChartDivision>("d1");
  const [style, setStyle] = useState<ChartStyle>("south-indian");
  const [selectedName, setSelectedName] = useState<string | null>(null);

  if (!chart) {
    return (
      <section aria-labelledby="chart-viewer-title" className="vedic-chart-viewer">
        <div className="chart-viewer-heading">
          <span className="section-kicker">Chart explorer</span>
          <h2 id="chart-viewer-title">Explore your Vedic chart</h2>
          <p>
            Chart visualizations will appear here when an astronomical chart
            response is available.
          </p>
        </div>
        <div className="chart-empty-state" role="status">
          <span aria-hidden="true">✳</span>
          <strong>No calculated chart to display</strong>
          <p>
            Nothing is drawn until actual placements are returned by the
            calculation API.
          </p>
        </div>
        <ChartGlossary />
      </section>
    );
  }

  const divisionChart = getDivisionChart(chart, division);
  const selectedPlacement =
    divisionChart.placements.find((placement) => placement.name === selectedName) ??
    null;
  const selectedPlanet =
    selectedName === "Ascendant"
      ? chart.ascendant
      : Object.values(chart.planets).find((planet) => planet.name === selectedName);

  return (
    <section aria-labelledby="chart-viewer-title" className="vedic-chart-viewer">
      <div className="chart-viewer-heading">
        <span className="section-kicker">Chart explorer</span>
        <h2 id="chart-viewer-title">Explore your Vedic chart</h2>
        <p>
          Select a chart and click a placement to explore its traditional
          associations.
        </p>
      </div>
      <div aria-label="Divisional chart" className="chart-control-group" role="group">
        {(Object.keys(DIVISION_LABELS) as ChartDivision[]).map((key) => (
          <button
            aria-pressed={division === key}
            className={division === key ? "chart-control active" : "chart-control"}
            key={key}
            onClick={() => {
              setDivision(key);
              setSelectedName(null);
            }}
            type="button"
          >
            {DIVISION_LABELS[key]}
          </button>
        ))}
      </div>
      <div aria-label="Chart style" className="chart-control-group chart-style-control" role="group">
        <button
          aria-pressed={style === "south-indian"}
          className={style === "south-indian" ? "chart-control active" : "chart-control"}
          onClick={() => setStyle("south-indian")}
          type="button"
        >
          South Indian
        </button>
        <button
          aria-pressed={style === "north-indian"}
          className={style === "north-indian" ? "chart-control active" : "chart-control"}
          onClick={() => setStyle("north-indian")}
          type="button"
        >
          North Indian
        </button>
      </div>
      <div className="chart-detail-layout">
        <div className="chart-canvas">
          {style === "south-indian" ? (
            <SouthIndianChart
              chart={divisionChart}
              selectedName={selectedName}
              onSelect={setSelectedName}
            />
          ) : (
            <NorthIndianChart
              chart={divisionChart}
              selectedName={selectedName}
              onSelect={setSelectedName}
            />
          )}
        </div>
        <aside aria-live="polite" className="planet-detail">
          {selectedPlacement && selectedPlanet ? (
            <>
              <span className="section-kicker">
                {selectedName === "Ascendant" ? "Ascendant" : "Planet detail"}
              </span>
              <h3>{selectedPlacement.name}</h3>
              <dl className="planet-detail-list">
                <div><dt>Sign</dt><dd>{selectedPlacement.sign}</dd></div>
                <div><dt>House</dt><dd>{selectedPlacement.house}</dd></div>
                <div><dt>Degree</dt><dd>{formatDegrees(selectedPlacement.degree_in_sign)}</dd></div>
                <div><dt>Nakshatra</dt><dd>{selectedPlanet.nakshatra}</dd></div>
                <div><dt>Nakshatra pada</dt><dd>{selectedPlanet.nakshatra_pada}</dd></div>
              </dl>
              <p className="planet-significance">
                {PLANET_MEANINGS[selectedPlacement.name] ??
                  "A traditional Jyotisha placement. Interpretations depend on the complete chart and should be considered in context."}
              </p>
              <p className="planet-context">
                Nakshatra is shown from the birth-chart position. Sign, house,
                and degree reflect the selected division.
              </p>
            </>
          ) : (
            <div className="planet-detail-empty">
              <span aria-hidden="true">✧</span>
              <strong>Select a placement</strong>
              <p>Click a planet or the Ascendant in the chart to see its details.</p>
            </div>
          )}
        </aside>
      </div>
      <ChartGlossary />
    </section>
  );
}

function ChartGlossary() {
  return (
    <div aria-label="Jyotisha terms" className="chart-glossary">
      {GLOSSARY.map(({ term, definition }) => (
        <span key={term} title={definition}>
          <strong>{term}</strong>
          <span aria-hidden="true">ⓘ</span>
        </span>
      ))}
    </div>
  );
}

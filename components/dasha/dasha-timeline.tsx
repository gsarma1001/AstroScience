"use client";

import { useEffect, useMemo, useState } from "react";
import { DASHA_INTERPRETATIONS } from "@/components/dasha/interpretations";
import { DashaPeriod, DashaSequence } from "@/components/dasha/types";

type DashaTimelineProps = {
  chartId: string | null;
};

function findActivePath(
  periods: DashaPeriod[],
  activeDate: Date,
): DashaPeriod[] {
  for (const period of periods) {
    const start = new Date(period.starts_at).getTime();
    const end = new Date(period.ends_at).getTime();
    if (activeDate.getTime() >= start && activeDate.getTime() < end) {
      return [period, ...findActivePath(period.children, activeDate)];
    }
  }
  return [];
}

function dateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function formatPeriodDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  }).format(new Date(value));
}

function formatDuration(years: number): string {
  if (years >= 1) return `${years.toFixed(2)} years`;
  const days = years * 365.25;
  return `${days.toFixed(1)} days`;
}

export function DashaTimeline({ chartId }: DashaTimelineProps) {
  const [sequence, setSequence] = useState<DashaSequence | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [expandedPeriods, setExpandedPeriods] = useState<Set<string>>(
    () => new Set(),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartId) return;
    const controller = new AbortController();
    const apiBase =
      process.env.NEXT_PUBLIC_ASTROLOGY_API_URL ?? "http://localhost:8000";
    setLoading(true);
    setError(null);
    setSequence(null);
    setSelectedDate("");
    setExpandedPeriods(new Set());
    fetch(
      `${apiBase.replace(/\/$/, "")}/api/chart/${encodeURIComponent(chartId)}/dashas`,
      { signal: controller.signal },
    )
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          const message =
            body && typeof body.detail === "string"
              ? body.detail
              : `Unable to load Dasha sequence (HTTP ${response.status}).`;
          throw new Error(message);
        }
        return (await response.json()) as DashaSequence;
      })
      .then((data) => {
        setSequence(data);
        const now = new Date();
        setSelectedDate(dateInputValue(now));
        setExpandedPeriods(
          new Set(
            findActivePath(data.mahadashas, now).map(
              (period) => period.period_id,
            ),
          ),
        );
      })
      .catch((cause: unknown) => {
        if (cause instanceof DOMException && cause.name === "AbortError") return;
        setError(
          cause instanceof Error
            ? cause.message
            : "An unexpected error occurred while loading Dasha periods.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [chartId]);

  const selectedInstant = useMemo(
    () => (selectedDate ? new Date(`${selectedDate}T00:00:00.000Z`) : null),
    [selectedDate],
  );
  const selectedPath = useMemo(
    () =>
      sequence && selectedInstant
        ? findActivePath(sequence.mahadashas, selectedInstant)
        : [],
    [sequence, selectedInstant],
  );
  const currentPath = useMemo(
    () => (sequence ? findActivePath(sequence.mahadashas, new Date()) : []),
    [sequence],
  );
  const selectedPeriod = selectedPath.at(-1) ?? null;

  function togglePeriod(periodId: string) {
    setExpandedPeriods((current) => {
      const next = new Set(current);
      if (next.has(periodId)) next.delete(periodId);
      else next.add(periodId);
      return next;
    });
  }

  if (!chartId) {
    return (
      <section aria-labelledby="dasha-title" className="dasha-timeline">
        <div className="dasha-heading">
          <span className="section-kicker">Planetary periods</span>
          <h2 id="dasha-title">Vimshottari Dasha</h2>
          <p>
            Add a chart ID returned by the calculation API to explore its
            Dasha sequence. Periods are never generated from placeholder data.
          </p>
        </div>
        <div className="dasha-empty-state" role="status">
          No calculated birth chart is connected.
        </div>
      </section>
    );
  }

  return (
    <section aria-labelledby="dasha-title" className="dasha-timeline">
      <div className="dasha-heading">
        <span className="section-kicker">Planetary periods</span>
        <h2 id="dasha-title">Vimshottari Dasha</h2>
        <p>
          A traditional timing sequence calculated from the Moon&apos;s exact
          sidereal Nakshatra position.
        </p>
      </div>
      {loading && <p className="dasha-status" role="status">Loading Dasha periods…</p>}
      {error && <p className="dasha-error" role="alert">{error}</p>}
      {sequence && (
        <>
          <div className="dasha-summary">
            <span>Birth Nakshatra <strong>{sequence.birth_nakshatra}</strong></span>
            <span>Nakshatra lord <strong>{sequence.nakshatra_lord}</strong></span>
            <span>Birth balance <strong>{sequence.balance_at_birth_years.toFixed(3)} years</strong></span>
          </div>
          <div className="dasha-date-picker">
            <label htmlFor="active-dasha-date">Find the Dasha active on a date</label>
            <input
              id="active-dasha-date"
              max={sequence.sequence_ends_at.slice(0, 10)}
              min={sequence.sequence_starts_at.slice(0, 10)}
              onChange={(event) => setSelectedDate(event.target.value)}
              type="date"
              value={selectedDate}
            />
            <small>Date selection is interpreted as 00:00 UTC; displayed period dates use your browser&apos;s timezone.</small>
          </div>
          {selectedPeriod ? (
            <div className="active-dasha-card" aria-live="polite">
              <span className="section-kicker">Active on {selectedDate || "selected date"}</span>
              <strong>{selectedPath.map((period) => period.planet).join(" → ")}</strong>
              <span>{selectedPeriod.level} · {formatPeriodDate(selectedPeriod.starts_at)} – {formatPeriodDate(selectedPeriod.ends_at)}</span>
              <p>{DASHA_INTERPRETATIONS[selectedPeriod.planet]}</p>
            </div>
          ) : (
            <div className="dasha-empty-state" role="status">
              Select a date inside this 120-year sequence to see its active period.
            </div>
          )}
          <div className="dasha-legend">
            <span><i className="dasha-current-key" /> Current period</span>
            <span><i className="dasha-selected-key" /> Selected date</span>
          </div>
          <div className="dasha-tree" aria-label="Expandable Vimshottari Dasha timeline">
            {sequence.mahadashas.map((period) => (
              <DashaPeriodRow
                currentIds={new Set(currentPath.map((item) => item.period_id))}
                depth={0}
                expandedPeriods={expandedPeriods}
                key={period.period_id}
                onToggle={togglePeriod}
                period={period}
                selectedIds={new Set(selectedPath.map((item) => item.period_id))}
              />
            ))}
          </div>
          <p className="dasha-convention">{sequence.year_length_convention}</p>
        </>
      )}
    </section>
  );
}

type DashaPeriodRowProps = {
  currentIds: Set<string>;
  depth: number;
  expandedPeriods: Set<string>;
  onToggle: (periodId: string) => void;
  period: DashaPeriod;
  selectedIds: Set<string>;
};

function DashaPeriodRow({
  currentIds,
  depth,
  expandedPeriods,
  onToggle,
  period,
  selectedIds,
}: DashaPeriodRowProps) {
  const hasChildren = period.children.length > 0;
  const expanded = expandedPeriods.has(period.period_id);
  const isCurrent = currentIds.has(period.period_id);
  const isSelected = selectedIds.has(period.period_id);
  const periodLabel = period.level === "sukshma" ? "Sukshma" : period.level;
  return (
    <div className="dasha-tree-item">
      <div
        className={[
          "dasha-period-row",
          `dasha-depth-${depth}`,
          isCurrent ? "is-current" : "",
          isSelected ? "is-selected" : "",
        ].filter(Boolean).join(" ")}
      >
        {hasChildren ? (
          <button
            aria-expanded={expanded}
            aria-label={`${expanded ? "Collapse" : "Expand"} ${period.planet} ${periodLabel}`}
            className="dasha-expand"
            onClick={() => onToggle(period.period_id)}
            type="button"
          >
            {expanded ? "−" : "+"}
          </button>
        ) : (
          <span className="dasha-expand-placeholder" />
        )}
        <span
          aria-label={`${period.planet}. ${DASHA_INTERPRETATIONS[period.planet]}`}
          className="dasha-planet"
          title={DASHA_INTERPRETATIONS[period.planet]}
        >
          {period.planet}
        </span>
        <span className="dasha-level">{periodLabel}</span>
        <span className="dasha-dates">
          {formatPeriodDate(period.starts_at)} – {formatPeriodDate(period.ends_at)}
        </span>
        <span className="dasha-duration">{formatDuration(period.duration_years)}</span>
        {isCurrent && <span className="dasha-current-badge">NOW</span>}
      </div>
      {expanded && hasChildren && (
        <div className="dasha-children">
          {period.children.map((child) => (
            <DashaPeriodRow
              currentIds={currentIds}
              depth={depth + 1}
              expandedPeriods={expandedPeriods}
              key={child.period_id}
              onToggle={onToggle}
              period={child}
              selectedIds={selectedIds}
            />
          ))}
        </div>
      )}
    </div>
  );
}

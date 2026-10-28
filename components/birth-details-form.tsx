"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Place = {
  label: string;
  latitude: number;
  longitude: number;
};

export function BirthDetailsForm() {
  const [birthplace, setBirthplace] = useState("");
  const [isPlaceListOpen, setIsPlaceListOpen] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [suggestions, setSuggestions] = useState<Place[]>([]);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
  const [placeSearchStatus, setPlaceSearchStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [placeSearchMessage, setPlaceSearchMessage] = useState("");
  const [placeSelectionError, setPlaceSelectionError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const birthplaceInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const query = birthplace.trim();
    if (!isPlaceListOpen || selectedPlace || query.length < 3) {
      setSuggestions([]);
      setPlaceSearchStatus("idle");
      setPlaceSearchMessage("");
      return;
    }

    const controller = new AbortController();
    setPlaceSearchStatus("loading");
    setPlaceSearchMessage("");
    const timeout = window.setTimeout(async () => {
      try {
        const response = await fetch(
          `/api/places?q=${encodeURIComponent(query)}`,
          { signal: controller.signal },
        );
        const result: unknown = await response.json();
        if (!response.ok) {
          const message =
            typeof result === "object" &&
            result !== null &&
            "error" in result &&
            typeof result.error === "string"
              ? result.error
              : "Place search is temporarily unavailable. Please try again.";
          throw new Error(message);
        }
        if (
          typeof result !== "object" ||
          result === null ||
          !("places" in result) ||
          !Array.isArray(result.places)
        ) {
          throw new Error("Place search returned an invalid response. Please try again.");
        }

        const places = result.places.filter(
          (place): place is Place =>
            typeof place === "object" &&
            place !== null &&
            "label" in place &&
            typeof place.label === "string" &&
            "latitude" in place &&
            typeof place.latitude === "number" &&
            "longitude" in place &&
            typeof place.longitude === "number",
        );
        setSuggestions(places);
        setActiveSuggestionIndex(-1);
        setPlaceSearchStatus("ready");
      } catch (error) {
        if (controller.signal.aborted) return;
        setSuggestions([]);
        setActiveSuggestionIndex(-1);
        setPlaceSearchStatus("error");
        setPlaceSearchMessage(
          error instanceof Error
            ? error.message
            : "Place search is temporarily unavailable. Please try again.",
        );
      }
    }, 350);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [birthplace, isPlaceListOpen, selectedPlace]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlace) {
      setPlaceSelectionError("Select a birthplace from the search results.");
      setIsPlaceListOpen(true);
      birthplaceInput.current?.focus();
      return;
    }
    setPlaceSelectionError("");
    setSubmitted(true);
  }

  function selectPlace(place: Place) {
    setBirthplace(place.label);
    setSelectedPlace(place);
    setIsPlaceListOpen(false);
    setActiveSuggestionIndex(-1);
    setPlaceSelectionError("");
    setSubmitted(false);
  }

  return (
    <form className="birth-form" onSubmit={handleSubmit}>
      <div className="form-card-heading">
        <span className="section-kicker">Step 01 <i /> About you</span>
        <h2>Your birth details</h2>
        <p>Fields marked <span aria-hidden="true">*</span> are required.</p>
      </div>
      <div className="form-fields">
        <label className="field">
          <span>Full name <b>*</b></span>
          <input autoComplete="name" name="name" placeholder="How should we address you?" required />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Birth date <b>*</b></span>
            <input autoComplete="bday" name="birthDate" type="date" required />
          </label>
          <label className="field">
            <span>Birth time <b>*</b></span>
            <input name="birthTime" type="time" required />
          </label>
        </div>
        <div className="field place-field">
          <label className="field-label" htmlFor="birthplace">Birthplace <b>*</b></label>
          <div className="place-input-wrap">
            <span className="place-pin" aria-hidden="true">⌖</span>
            <input
              autoComplete="off"
              aria-describedby="birthplace-help birthplace-status"
              aria-invalid={Boolean(placeSelectionError)}
              aria-autocomplete="list"
              aria-controls="birthplace-suggestions"
              aria-expanded={isPlaceListOpen && suggestions.length > 0}
              aria-activedescendant={
                isPlaceListOpen && activeSuggestionIndex >= 0
                  ? `birthplace-option-${activeSuggestionIndex}`
                  : undefined
              }
              role="combobox"
              ref={birthplaceInput}
              id="birthplace"
              name="birthplace"
              onBlur={() => window.setTimeout(() => setIsPlaceListOpen(false), 180)}
              onChange={(event) => {
                setBirthplace(event.target.value);
                setSelectedPlace(null);
                setActiveSuggestionIndex(-1);
                setIsPlaceListOpen(true);
                setPlaceSelectionError("");
                setSubmitted(false);
              }}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  setIsPlaceListOpen(false);
                  setActiveSuggestionIndex(-1);
                } else if (event.key === "ArrowDown" && suggestions.length > 0) {
                  event.preventDefault();
                  setIsPlaceListOpen(true);
                  setActiveSuggestionIndex((index) =>
                    index < suggestions.length - 1 ? index + 1 : 0,
                  );
                } else if (event.key === "ArrowUp" && suggestions.length > 0) {
                  event.preventDefault();
                  setActiveSuggestionIndex((index) =>
                    index > 0 ? index - 1 : suggestions.length - 1,
                  );
                } else if (
                  event.key === "Enter" &&
                  isPlaceListOpen &&
                  activeSuggestionIndex >= 0
                ) {
                  event.preventDefault();
                  selectPlace(suggestions[activeSuggestionIndex]);
                }
              }}
              onFocus={() => setIsPlaceListOpen(true)}
              placeholder="Search for a city or town"
              required
              value={birthplace}
            />
            <input
              name="latitude"
              type="hidden"
              value={selectedPlace?.latitude ?? ""}
            />
            <input
              name="longitude"
              type="hidden"
              value={selectedPlace?.longitude ?? ""}
            />
            {isPlaceListOpen && suggestions.length > 0 && (
              <ul className="place-suggestions" id="birthplace-suggestions" role="listbox">
                {suggestions.map((place, index) => (
                  <li
                    key={`${place.label}:${place.latitude}:${place.longitude}`}
                    id={`birthplace-option-${index}`}
                    role="option"
                    aria-selected={index === activeSuggestionIndex}
                    onClick={() => selectPlace(place)}
                    onMouseDown={(event) => event.preventDefault()}
                    onMouseEnter={() => setActiveSuggestionIndex(index)}
                  >
                    <span aria-hidden="true">⌖</span>{place.label}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="place-search-status" id="birthplace-status" aria-live="polite">
            {isPlaceListOpen && birthplace.trim().length > 0 && birthplace.trim().length < 3
              ? "Enter at least 3 characters to search."
              : null}
            {placeSearchStatus === "loading" ? "Searching locations…" : null}
            {placeSearchStatus === "ready" && suggestions.length === 0
              ? "No matching places found. Try a nearby city or a different spelling."
              : null}
            {placeSearchStatus === "error" ? placeSearchMessage : null}
            {selectedPlace
              ? `Selected coordinates: ${selectedPlace.latitude.toFixed(5)}, ${selectedPlace.longitude.toFixed(5)}`
              : null}
            {placeSelectionError ? (
              <span className="place-selection-error" role="alert">{placeSelectionError}</span>
            ) : null}
          </div>
          <small id="birthplace-help">
            Search powered by{" "}
            <a href="https://github.com/komoot/photon" target="_blank" rel="noreferrer">
              Photon
            </a>{" "}
            and{" "}
            <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
              OpenStreetMap
            </a>
            . Place-search text is sent to Photon to find locations. Select a result to confirm its coordinates.
          </small>
        </div>
      </div>
      <fieldset className="form-options">
        <legend>How certain is your birth time? <span>Helps set expectations for a future chart</span></legend>
        <div className="radio-options">
          <label><input defaultChecked name="timeAccuracy" type="radio" value="exact" /><span>Exact</span></label>
          <label><input name="timeAccuracy" type="radio" value="approximate" /><span>Approximate</span></label>
          <label><input name="timeAccuracy" type="radio" value="unknown" /><span>Not sure</span></label>
        </div>
      </fieldset>
      <div className="field">
        <label className="field-label" htmlFor="chartStyle">Preferred chart style</label>
        <select defaultValue="north-indian" id="chartStyle" name="chartStyle">
          <option value="north-indian">North Indian</option>
          <option value="south-indian">South Indian</option>
          <option value="east-indian">East Indian</option>
        </select>
      </div>
      <div className="field ayanamsa-field">
        <label className="field-label" htmlFor="ayanamsa">Ayanamsa</label>
        <select defaultValue="lahiri" id="ayanamsa" name="ayanamsa">
          <option value="lahiri">Lahiri (Chitrapaksha) — Recommended</option>
          <option value="raman">Raman</option>
          <option value="krishnamurti">Krishnamurti</option>
        </select>
        <small>Lahiri is the most widely used ayanamsa in modern Vedic astrology.</small>
      </div>
      <button className="button button-form" type="submit">Continue <span aria-hidden="true">→</span></button>
      {submitted && (
        <p className="form-feedback" role="status">
          Your details are entered for this preview only. Birth-chart calculations and saving are not implemented yet.
        </p>
      )}
      <p className="form-disclaimer">No chart will be generated or saved at this stage. Place-search text is sent to Photon; your other details remain in this browser preview.</p>
    </form>
  );
}

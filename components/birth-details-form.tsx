"use client";

import { FormEvent, useMemo, useState } from "react";

const places = [
  "Ahmedabad, Gujarat, India",
  "Bengaluru, Karnataka, India",
  "Chennai, Tamil Nadu, India",
  "Delhi, India",
  "Hyderabad, Telangana, India",
  "Kolkata, West Bengal, India",
  "Mumbai, Maharashtra, India",
  "Pune, Maharashtra, India",
  "London, United Kingdom",
  "New York, NY, United States",
  "San Francisco, CA, United States",
  "Toronto, Ontario, Canada",
];

export function BirthDetailsForm() {
  const [birthplace, setBirthplace] = useState("");
  const [isPlaceListOpen, setIsPlaceListOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const suggestions = useMemo(() => {
    const query = birthplace.trim().toLocaleLowerCase();
    if (!query) return [];
    return places.filter((place) => place.toLocaleLowerCase().includes(query)).slice(0, 5);
  }, [birthplace]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
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
              id="birthplace"
              name="birthplace"
              onBlur={() => window.setTimeout(() => setIsPlaceListOpen(false), 120)}
              onChange={(event) => {
                setBirthplace(event.target.value);
                setIsPlaceListOpen(true);
                setSubmitted(false);
              }}
              onFocus={() => setIsPlaceListOpen(true)}
              placeholder="Search for a city or town"
              required
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={isPlaceListOpen && suggestions.length > 0}
              aria-controls="birthplace-suggestions"
              value={birthplace}
            />
            {isPlaceListOpen && suggestions.length > 0 && (
              <ul className="place-suggestions" id="birthplace-suggestions" role="listbox">
                {suggestions.map((place) => (
                  <li key={place} role="option" aria-selected={birthplace === place}>
                    <button
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => {
                        setBirthplace(place);
                        setIsPlaceListOpen(false);
                        setSubmitted(false);
                      }}
                      type="button"
                    >
                      <span aria-hidden="true">⌖</span>{place}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <small>Start typing to see local suggestions, or enter any place. Suggestions are for demonstration only; location lookup is not connected.</small>
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
      <p className="form-disclaimer">No chart will be generated at this stage. Your information is not sent or stored.</p>
    </form>
  );
}

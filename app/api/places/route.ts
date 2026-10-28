import { NextResponse } from "next/server";

type PhotonProperties = {
  name?: unknown;
  city?: unknown;
  district?: unknown;
  county?: unknown;
  state?: unknown;
  country?: unknown;
};

type PhotonFeature = {
  properties?: PhotonProperties;
  geometry?: { coordinates?: unknown };
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function toPlace(feature: PhotonFeature) {
  const properties = feature.properties;
  const coordinates = feature.geometry?.coordinates;
  if (!properties || !Array.isArray(coordinates) || coordinates.length < 2) {
    return null;
  }

  const longitude = coordinates[0];
  const latitude = coordinates[1];
  if (
    typeof longitude !== "number" ||
    typeof latitude !== "number" ||
    !Number.isFinite(longitude) ||
    !Number.isFinite(latitude) ||
    longitude < -180 ||
    longitude > 180 ||
    latitude < -90 ||
    latitude > 90
  ) {
    return null;
  }

  const name = nonEmptyString(properties.name);
  if (!name) return null;

  const locality =
    nonEmptyString(properties.city) ?? nonEmptyString(properties.district);
  const labelParts = [
    name,
    locality && locality.toLocaleLowerCase() !== name.toLocaleLowerCase()
      ? locality
      : null,
    nonEmptyString(properties.state),
    nonEmptyString(properties.country),
  ].filter((part): part is string => part !== null);
  const label = labelParts.filter(
    (part, index) =>
      labelParts.findIndex(
        (candidate) => candidate.toLocaleLowerCase() === part.toLocaleLowerCase(),
      ) === index,
  ).join(", ");

  return { label, latitude, longitude };
}

export async function GET(request: Request) {
  const query = new URL(request.url).searchParams.get("q")?.trim() ?? "";
  if (query.length < 3) {
    return NextResponse.json(
      { error: "Enter at least 3 characters to search for a place." },
      { status: 400 },
    );
  }
  if (query.length > 120) {
    return NextResponse.json(
      { error: "Place searches must be 120 characters or fewer." },
      { status: 400 },
    );
  }

  const url = new URL("https://photon.komoot.io/api/");
  url.searchParams.set("q", query);
  url.searchParams.set("limit", "5");
  url.searchParams.set("lang", "en");

  let response: Response;
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
    });
  } catch (error) {
    console.error("Place search request to Photon failed", error);
    return NextResponse.json(
      { error: "Place search is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }

  if (!response.ok) {
    console.error("Photon place search returned HTTP", response.status);
    return NextResponse.json(
      { error: "Place search is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch (error) {
    console.error("Photon returned invalid place search JSON", error);
    return NextResponse.json(
      { error: "Place search returned an invalid response. Please try again." },
      { status: 502 },
    );
  }

  if (!isRecord(payload) || !Array.isArray(payload.features)) {
    console.error("Photon returned an unexpected place search response");
    return NextResponse.json(
      { error: "Place search returned an invalid response. Please try again." },
      { status: 502 },
    );
  }

  const seenLabels = new Set<string>();
  const places = payload.features
    .map((feature) => (isRecord(feature) ? toPlace(feature as PhotonFeature) : null))
    .filter((place): place is NonNullable<typeof place> => {
      if (!place) return false;
      const key = place.label.toLocaleLowerCase();
      if (seenLabels.has(key)) return false;
      seenLabels.add(key);
      return true;
    });

  return NextResponse.json({ places });
}

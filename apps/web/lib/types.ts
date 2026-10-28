// Shapes returned by the FastAPI service (see /api/docs for the full schema).

export type PlanetId = "sun" | "moon" | "mars" | "mercury" | "jupiter" | "venus" | "saturn" | "rahu" | "ketu";
export const PLANETS: PlanetId[] = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"];
export const SIGN_KEYS = [
  "aries", "taurus", "gemini", "cancer", "leo", "virgo",
  "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
] as const;
export const VARGA_CODES = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"] as const;
export type VargaCode = (typeof VARGA_CODES)[number];

export type ChartSettings = {
  ayanamsa: "lahiri" | "raman" | "krishnamurti" | "yukteshwar" | "true_chitrapaksha";
  node_type: "mean" | "true";
  chart_style: "north" | "south";
  dasha_year_days: 365.25 | 365.2422;
};

export type Me = {
  id: string;
  email: string;
  display_name: string | null;
  role: "user" | "astrologer" | "admin";
  locale: "en" | "hi" | "mr";
  default_settings: ChartSettings;
  consent: { given: boolean; version: string };
  brand_name: string | null;
  has_brand_logo: boolean;
  max_profiles: number;
};

export type Profile = {
  id: string;
  name: string;
  birth_date: string;
  birth_time: string;
  time_accuracy: "exact" | "approximate" | "unknown";
  latitude: number;
  longitude: number;
  place_name: string | null;
  tz_name: string | null;
  utc_offset_minutes: number | null;
  gender: "male" | "female" | "other" | null;
  folder: string | null;
  settings: ChartSettings;
  is_main: boolean;
  created_at: string;
  updated_at: string;
};

export type ProfileInput = Omit<Profile, "id" | "created_at" | "updated_at">;

export type ChartPlanet = {
  id: PlanetId;
  longitude: number;
  latitude: number;
  speed: number;
  retrograde: boolean;
  sign: string;
  sign_index: number;
  degree_in_sign: number;
  dms: string;
  house: number;
  nakshatra: string;
  nakshatra_index: number;
  pada: number;
  nakshatra_lord: PlanetId;
  sign_lord: PlanetId;
  dignity: string;
  combust: boolean;
  combustion_orb: number | null;
};

export type DashaPeriod = {
  lord: PlanetId;
  start: string;
  end: string;
  start_jd: number;
  end_jd: number;
  periods?: DashaPeriod[];
};

export type Varga = {
  name: string;
  lagna_sign_index: number;
  lagna_sign: string;
  planets: Record<PlanetId, { sign_index: number; sign: string; house: number }>;
};

export type Reading = { id: string; topic: string; kind: string; source: string; text_key: string; title: string; text: string };

export type Chart = {
  meta: {
    engine_version: string;
    ephemeris: string;
    ephemeris_version: string;
    ephemeris_source: string[];
    ayanamsa: string;
    ayanamsa_value: number;
    settings: ChartSettings & { house_system: string };
    zodiac: string;
  };
  input: {
    local_datetime: string;
    utc_datetime: string;
    tz_name: string | null;
    utc_offset_minutes: number;
    julian_day_ut: number;
    latitude: number;
    longitude: number;
    time_accuracy: string;
  };
  lagna: { longitude: number; sign: string; sign_index: number; degree_in_sign: number; dms: string; nakshatra: string; pada: number; lord: PlanetId };
  planets: ChartPlanet[];
  houses: { house: number; sign: string; sign_index: number; lord: PlanetId; occupants: PlanetId[] }[];
  vargas: Partial<Record<VargaCode, Varga>>;
  dasha: { system: string; moon_nakshatra: string; first_lord: PlanetId; balance_years: number; year_days: number; mahadashas: DashaPeriod[] };
  time_sensitive: string[];
  bhava_chalit?: { system: string; cusps: number[]; planets: Record<PlanetId, number> };
  interpretations: { ruleset_version: string; count: number; results: Omit<Reading, "title" | "text">[] };
};

export type Names = {
  lang: string;
  planets: Record<string, string>;
  planet_abbr: Record<string, string>;
  signs: Record<string, string>;
  sign_short: Record<string, string>;
  nakshatras: Record<string, string>;
  tithis: Record<string, string>;
  paksha: Record<string, string>;
  yogas: Record<string, string>;
  karanas: Record<string, string>;
  varas: Record<string, string>;
  dignities: Record<string, string>;
  ayanamsas: Record<string, string>;
  vargas: Record<string, string>;
  kootas: Record<string, string>;
  topics: Record<string, string>;
  sade_sati_phases: Record<string, string>;
};

export type Place = {
  id: number;
  name: string;
  name_deva: string | null;
  admin1: string | null;
  country: string;
  country_code: string;
  label: string;
  latitude: number;
  longitude: number;
  tz_name: string;
  population: number;
};

export type Transits = {
  date: string;
  natal_lagna: string;
  natal_moon_sign: string;
  planets: { id: PlanetId; longitude: number; sign: string; sign_index: number; dms: string; retrograde: boolean; nakshatra: string; pada: number; house_from_lagna: number; house_from_moon: number }[];
  sade_sati: {
    cycles: { start: string; end: string; starts_before_birth: boolean; ends_after_range: boolean; phases: { phase: string; start: string; end: string }[] }[];
    current: { phase: string | null; cycle: { start: string; end: string } } | null;
  };
};

export type PanchangSpan = { index: number; name: string | { paksha: string; name: string }; ends: string | null };
export type Panchang = {
  date: string;
  tz_name: string;
  sunrise: string;
  sunset: string;
  next_sunrise: string;
  moonrise: string | null;
  moonset: string | null;
  vara: { index: number; name: string };
  tithi: PanchangSpan[];
  nakshatra: PanchangSpan[];
  yoga: PanchangSpan[];
  karana: PanchangSpan[];
};

export type Koota = { koota: string; max: number; points: number; boy?: string; girl?: string };
export type MatchResult = {
  boy: { profile: { id: string; name: string; birth_date: string }; chart: Chart; manglik: { is_manglik: boolean; from: Record<string, number>; rule: string; mitigations: string[] } };
  girl: MatchResult["boy"];
  ashtakoota: { kootas: Koota[]; total: number; max: number; verdict: "excellent" | "good" | "not_recommended"; doshas: { nadi: boolean; bhakoot: boolean } };
};

export type Report = { id: string; kind: "natal" | "match"; lang: string; status: "queued" | "running" | "ready" | "failed"; profile_id: string | null; partner_profile_id: string | null; created_at: string; expires_at: string | null; error: string | null };

export type Strength = {
  ashtakavarga: { signs: string[]; bhinna: Record<string, number[]>; sarva: number[]; sarva_total: number; sarva_by_house: number[] };
  shadbala: {
    planets: Record<string, { sthana_total: number; dig: number; kala_total: number; chesta: number; naisargika: number; drik: number; total_rupas: number; required_rupas: number; ratio: number; motion: string }>;
    ranking: string[];
    method_notes: string;
  };
};

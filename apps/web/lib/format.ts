// Date and number formatting in the user's language.

const LOCALE_TAG: Record<string, string> = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

export function fmtDate(iso: string, locale: string, timeZone?: string | null): string {
  return new Intl.DateTimeFormat(LOCALE_TAG[locale] ?? locale, { dateStyle: "medium", timeZone: timeZone ?? undefined }).format(new Date(iso));
}

export function fmtDateTime(iso: string, locale: string, timeZone?: string | null): string {
  return new Intl.DateTimeFormat(LOCALE_TAG[locale] ?? locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: timeZone ?? undefined,
  }).format(new Date(iso));
}

export function fmtTime(iso: string, locale: string, timeZone?: string | null): string {
  return new Intl.DateTimeFormat(LOCALE_TAG[locale] ?? locale, { timeStyle: "short", timeZone: timeZone ?? undefined }).format(new Date(iso));
}

export function fmtBirthDate(ymd: string, locale: string): string {
  const [y, m, d] = ymd.split("-").map(Number);
  return new Intl.DateTimeFormat(LOCALE_TAG[locale] ?? locale, { dateStyle: "long", timeZone: "UTC" }).format(Date.UTC(y, m - 1, d));
}

export function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function julianDay(date: Date): number {
  return date.getTime() / 86400000 + 2440587.5;
}

export function offsetLabel(minutes: number): string {
  const sign = minutes >= 0 ? "+" : "-";
  const m = Math.abs(minutes);
  return `UTC${sign}${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

export const locales = ["en", "hi", "mr"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";
export const localeNames: Record<Locale, string> = { en: "English", hi: "हिन्दी", mr: "मराठी" };
export const LOCALE_COOKIE = "NEXT_LOCALE";

export function isLocale(x: unknown): x is Locale {
  return typeof x === "string" && (locales as readonly string[]).includes(x);
}

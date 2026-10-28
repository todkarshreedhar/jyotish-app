"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { api } from "@/lib/api";
import { LOCALE_COOKIE, localeNames, locales, type Locale } from "@/i18n/config";
import { useMe } from "@/lib/hooks";

export function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations("nav");
  const router = useRouter();
  const qc = useQueryClient();
  const { data: me } = useMe();
  const [pending, start] = useTransition();

  async function change(next: Locale) {
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    if (me) {
      try {
        await api("/v1/me", { method: "PATCH", json: { locale: next } });
      } catch {
        /* the cookie is enough to switch the screen */
      }
    }
    start(() => {
      qc.invalidateQueries({ queryKey: ["names"] });
      qc.invalidateQueries({ queryKey: ["readings"] });
      router.refresh();
    });
  }

  return (
    <label className="flex items-center gap-1 text-sm">
      <span className="sr-only">{t("language")}</span>
      <select
        value={locale}
        disabled={pending}
        onChange={(e) => change(e.target.value as Locale)}
        className="min-h-10 rounded-md border border-border bg-surface px-2"
        aria-label={t("language")}
      >
        {locales.map((l) => (
          <option key={l} value={l} lang={l}>
            {localeNames[l]}
          </option>
        ))}
      </select>
    </label>
  );
}

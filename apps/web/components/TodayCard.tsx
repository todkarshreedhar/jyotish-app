"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { fmtDate, fmtTime, julianDay, todayISO } from "@/lib/format";
import { useChart, useNames, usePanchang, useTransits } from "@/lib/hooks";
import type { Profile } from "@/lib/types";
import { Card } from "./ui";

/** "Today for you" (US-70): current Dasha, Moon transit and today's Panchang. */
export function TodayCard({ profile }: { profile: Profile }) {
  const t = useTranslations("today");
  const locale = useLocale();
  const { data: names } = useNames();
  const { data: chart } = useChart(profile.id, ["D1", "D9"]);
  const today = todayISO();
  const { data: tr } = useTransits(profile.id, today);
  const { data: pan } = usePanchang(today, profile.latitude, profile.longitude, profile.tz_name);
  if (!names) return null;

  const jd = julianDay(new Date());
  const maha = chart?.dasha.mahadashas.find((m) => m.start_jd <= jd && jd < m.end_jd);
  const antar = maha?.periods?.find((a) => a.start_jd <= jd && jd < a.end_jd);
  const moon = tr?.planets.find((p) => p.id === "moon");
  const tithi = pan?.tithi[0];
  const tithiName = tithi && typeof tithi.name === "object" ? `${names.paksha[tithi.name.paksha]} ${names.tithis[tithi.name.name]}` : "";

  return (
    <Card title={t("title", { name: profile.name })} actions={<Link href={`/profiles/${profile.id}`} className="text-sm underline">{t("open")}</Link>}>
      <dl className="grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted">{t("dasha")}</dt>
          <dd className="font-semibold">
            {maha ? `${names.planets[maha.lord]}${antar ? ` / ${names.planets[antar.lord]}` : ""}` : "…"}
          </dd>
          {antar && <dd className="text-xs text-muted">{t("until", { date: fmtDate(antar.end, locale) })}</dd>}
        </div>
        <div>
          <dt className="text-muted">{t("moon")}</dt>
          <dd className="font-semibold">{moon ? `${names.signs[moon.sign]} · ${names.nakshatras[moon.nakshatra]}` : "…"}</dd>
          {moon && <dd className="text-xs text-muted">{t("houseFromMoon", { house: moon.house_from_moon })}</dd>}
        </div>
        <div>
          <dt className="text-muted">{t("panchang")}</dt>
          <dd className="font-semibold">{pan ? `${names.varas[pan.vara.name]} · ${tithiName}` : "…"}</dd>
          {pan && <dd className="text-xs text-muted">{t("sunrise", { time: fmtTime(pan.sunrise, locale, pan.tz_name) })}</dd>}
        </div>
      </dl>
      {tr?.sade_sati.current?.phase && (
        <p className="mt-3 text-sm">{t("sadeSati", { phase: names.sade_sati_phases[tr.sade_sati.current.phase] })}</p>
      )}
    </Card>
  );
}

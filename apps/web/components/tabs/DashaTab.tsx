"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Badge, Term } from "@/components/ui";
import { fmtDate, julianDay } from "@/lib/format";
import type { Chart, DashaPeriod, Names } from "@/lib/types";

/** US-35: Dasha timeline with today's periods highlighted. */
export function DashaTab({ chart, names, tz }: { chart: Chart; names: Names; tz: string | null }) {
  const t = useTranslations("dasha");
  const g = useTranslations("glossary");
  const locale = useLocale();
  const jd = julianDay(new Date());
  const current = chart.dasha.mahadashas.find((m) => m.start_jd <= jd && jd < m.end_jd);
  const [open, setOpen] = useState<string | null>(current ? current.start : null);
  const fmt = (iso: string) => fmtDate(iso, locale, tz);

  const years = Math.floor(chart.dasha.balance_years);
  const months = Math.round((chart.dasha.balance_years - years) * 12);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm">
        {t.rich("intro", {
          term: (c) => <Term meaning={g("vimshottari")}>{c}</Term>,
          lord: names.planets[chart.dasha.first_lord],
          nak: names.nakshatras[chart.dasha.moon_nakshatra],
          years,
          months,
        })}
      </p>
      <p className="text-xs text-muted">{t("yearLength", { days: chart.dasha.year_days })}</p>
      <ol className="flex flex-col gap-2">
        {chart.dasha.mahadashas.map((m) => {
          const isNow = m === current;
          const expanded = open === m.start;
          return (
            <li key={m.start} className={`rounded-xl border ${isNow ? "border-primary bg-surface-2" : "border-border bg-surface"}`}>
              <button
                className="flex min-h-12 w-full flex-wrap items-center justify-between gap-2 px-4 py-2 text-left"
                aria-expanded={expanded}
                onClick={() => setOpen(expanded ? null : m.start)}
              >
                <span className="font-semibold">
                  {names.planets[m.lord]} {t("maha")} {isNow && <Badge tone="accent">{t("now")}</Badge>}
                </span>
                <span className="text-sm text-muted">{fmt(m.start)} – {fmt(m.end)}</span>
              </button>
              {expanded && m.periods && <Antars maha={m} names={names} jd={jd} fmt={fmt} />}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function Antars({ maha, names, jd, fmt }: { maha: DashaPeriod; names: Names; jd: number; fmt: (s: string) => string }) {
  const t = useTranslations("dasha");
  const [open, setOpen] = useState<string | null>(maha.periods?.find((a) => a.start_jd <= jd && jd < a.end_jd)?.start ?? null);
  return (
    <ol className="border-t border-border px-2 pb-2">
      {maha.periods!.map((a) => {
        const isNow = a.start_jd <= jd && jd < a.end_jd;
        const expanded = open === a.start;
        return (
          <li key={a.start} className={isNow ? "rounded-lg bg-accent/15" : ""}>
            <button className="flex min-h-11 w-full flex-wrap items-center justify-between gap-2 px-3 py-1 text-left text-sm" aria-expanded={expanded} onClick={() => setOpen(expanded ? null : a.start)}>
              <span>
                {names.planets[maha.lord]} / <strong>{names.planets[a.lord]}</strong> {isNow && <Badge tone="accent">{t("now")}</Badge>}
              </span>
              <span className="text-muted">{fmt(a.start)} – {fmt(a.end)}</span>
            </button>
            {expanded && a.periods && (
              <ol className="mb-2 ml-6 border-l border-border pl-3 text-xs">
                <li className="py-1 font-medium text-muted">{t("pratyantar")}</li>
                {a.periods.map((p) => {
                  const now = p.start_jd <= jd && jd < p.end_jd;
                  return (
                    <li key={p.start} className={`flex flex-wrap justify-between gap-2 py-1 ${now ? "font-semibold" : ""}`}>
                      <span>{names.planets[p.lord]} {now && <Badge tone="accent">{t("now")}</Badge>}</span>
                      <span className="text-muted">{fmt(p.start)} – {fmt(p.end)}</span>
                    </li>
                  );
                })}
              </ol>
            )}
          </li>
        );
      })}
    </ol>
  );
}

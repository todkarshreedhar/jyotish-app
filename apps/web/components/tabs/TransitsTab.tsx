"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Alert, Badge, Input, Spinner, Table, Term } from "@/components/ui";
import { fmtDate, todayISO } from "@/lib/format";
import { useTransits } from "@/lib/hooks";
import type { Names } from "@/lib/types";

/** US-37, US-38: today's planets over the birth chart, and Sade Sati. */
export function TransitsTab({ profileId, names }: { profileId: string; names: Names }) {
  const t = useTranslations("transits");
  const g = useTranslations("glossary");
  const locale = useLocale();
  const [on, setOn] = useState(todayISO());
  const { data, isLoading } = useTransits(profileId, on);

  return (
    <div className="flex flex-col gap-4">
      <label className="flex max-w-xs flex-col gap-1 text-sm">
        {t("date")}
        <Input type="date" value={on} onChange={(e) => e.target.value && setOn(e.target.value)} />
      </label>
      {isLoading || !data ? (
        <Spinner />
      ) : (
        <>
          <Table caption={t("caption")}>
            <thead>
              <tr>
                <th scope="col">{t("planet")}</th>
                <th scope="col">{t("sign")}</th>
                <th scope="col">{t("degree")}</th>
                <th scope="col">{t("nakshatra")}</th>
                <th scope="col">{t("fromLagna")}</th>
                <th scope="col">{t("fromMoon")}</th>
              </tr>
            </thead>
            <tbody>
              {data.planets.map((p) => (
                <tr key={p.id}>
                  <th scope="row">{names.planets[p.id]} {p.retrograde && p.id !== "rahu" && p.id !== "ketu" && <Badge tone="danger">R</Badge>}</th>
                  <td>{names.signs[p.sign]}</td>
                  <td className="font-mono">{p.dms}</td>
                  <td>{names.nakshatras[p.nakshatra]} {p.pada}</td>
                  <td>{p.house_from_lagna}</td>
                  <td>{p.house_from_moon}</td>
                </tr>
              ))}
            </tbody>
          </Table>

          <section aria-labelledby="ss" className="flex flex-col gap-2">
            <h2 id="ss" className="text-lg font-semibold"><Term meaning={g("sadeSati")}>{t("sadeSati")}</Term></h2>
            {data.sade_sati.current?.phase ? (
              <Alert kind="warn">{t("inSadeSati", { phase: names.sade_sati_phases[data.sade_sati.current.phase], end: fmtDate(data.sade_sati.current.cycle.end, locale) })}</Alert>
            ) : (
              <p className="text-sm">{t("notInSadeSati")}</p>
            )}
            <ul className="flex flex-col gap-2">
              {data.sade_sati.cycles.map((c) => (
                <li key={c.start} className="rounded-lg border border-border p-3 text-sm">
                  <p className="font-medium">{fmtDate(c.start, locale)} – {fmtDate(c.end, locale)}{c.starts_before_birth && ` (${t("beforeBirth")})`}</p>
                  <ul className="mt-1 text-muted">
                    {c.phases.map((ph) => (
                      <li key={ph.phase}>{names.sade_sati_phases[ph.phase]}: {fmtDate(ph.start, locale)} – {fmtDate(ph.end, locale)}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

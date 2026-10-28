"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { PlaceSearch } from "@/components/PlaceSearch";
import { Alert, Card, Field, Input, Spinner, Table, Term } from "@/components/ui";
import { errorText } from "@/lib/api";
import { fmtDateTime, fmtTime, todayISO } from "@/lib/format";
import { useNames, usePanchang } from "@/lib/hooks";
import type { PanchangSpan, Place } from "@/lib/types";

/** US-64: today's Panchang for a city. */
export default function PanchangPage() {
  const t = useTranslations("panchang");
  const g = useTranslations("glossary");
  const locale = useLocale();
  const { data: names } = useNames();
  const [on, setOn] = useState(todayISO());
  const [place, setPlace] = useState<Place | null>(null);
  const { data, isLoading, error } = usePanchang(on, place?.latitude ?? null, place?.longitude ?? null, place?.tz_name ?? null);
  const tz = place?.tz_name;

  function spanName(kind: "tithi" | "nakshatra" | "yoga" | "karana", s: PanchangSpan): string {
    if (!names) return "";
    if (kind === "tithi" && typeof s.name === "object") return `${names.paksha[s.name.paksha]} ${names.tithis[s.name.name]}`;
    const key = s.name as string;
    return { nakshatra: names.nakshatras, yoga: names.yogas, karana: names.karanas, tithi: names.tithis }[kind][key] ?? key;
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold"><Term meaning={g("panchang")}>{t("title")}</Term></h1>
      <Card>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("city")} htmlFor="pplace">
            <PlaceSearch inputId="pplace" value={place?.label ?? ""} onPick={setPlace} />
          </Field>
          <Field label={t("date")} htmlFor="pdate">
            <Input id="pdate" type="date" value={on} onChange={(e) => e.target.value && setOn(e.target.value)} />
          </Field>
        </div>
      </Card>
      {!place && <p className="text-sm text-muted">{t("pick")}</p>}
      {error && <Alert kind="error">{errorText(error)}</Alert>}
      {place && (isLoading || !names) && <Spinner />}
      {data && names && (
        <Card title={`${place?.label} · ${names.varas[data.vara.name]}`}>
          <dl className="mb-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div><dt className="text-muted">{t("sunrise")}</dt><dd className="font-semibold">{fmtTime(data.sunrise, locale, tz)}</dd></div>
            <div><dt className="text-muted">{t("sunset")}</dt><dd className="font-semibold">{fmtTime(data.sunset, locale, tz)}</dd></div>
            <div><dt className="text-muted">{t("moonrise")}</dt><dd className="font-semibold">{data.moonrise ? fmtTime(data.moonrise, locale, tz) : "—"}</dd></div>
            <div><dt className="text-muted">{t("moonset")}</dt><dd className="font-semibold">{data.moonset ? fmtTime(data.moonset, locale, tz) : "—"}</dd></div>
          </dl>
          <Table caption={t("title")}>
            <thead><tr><th scope="col">{t("limb")}</th><th scope="col">{t("value")}</th><th scope="col">{t("ends")}</th></tr></thead>
            <tbody>
              {(["tithi", "nakshatra", "yoga", "karana"] as const).flatMap((k) =>
                data[k].map((s, i) => (
                  <tr key={`${k}-${i}`}>
                    {i === 0 && <th scope="row" rowSpan={data[k].length}><Term meaning={g(k)}>{t(k)}</Term></th>}
                    <td>{spanName(k, s)}</td>
                    <td>{s.ends ? fmtDateTime(s.ends, locale, tz) : "—"}</td>
                  </tr>
                )),
              )}
            </tbody>
          </Table>
          <p className="mt-3 text-xs text-muted">{t("note", { tz: data.tz_name })}</p>
        </Card>
      )}
    </div>
  );
}

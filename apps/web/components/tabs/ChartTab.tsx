"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Kundli } from "@/components/chart/Kundli";
import { Alert, Select, Spinner, Term } from "@/components/ui";
import { api } from "@/lib/api";
import { useChart } from "@/lib/hooks";
import { SIGN_KEYS, VARGA_CODES, type Chart, type Names, type Profile, type VargaCode } from "@/lib/types";

export function kundliProps(chart: Chart, code: VargaCode, names: Names) {
  const v = chart.vargas[code]!;
  return {
    lagnaSign: v.lagna_sign_index,
    planets: chart.planets.map((p) => ({
      id: p.id,
      house: v.planets[p.id].house,
      sign_index: v.planets[p.id].sign_index,
      degree: code === "D1" ? p.degree_in_sign : null,
      retrograde: p.retrograde,
    })),
    abbr: names.planet_abbr,
    signShort: SIGN_KEYS.map((k) => names.sign_short[k]),
    signNames: SIGN_KEYS.map((k) => names.signs[k]),
    planetNames: names.planets,
  };
}

export function ChartTab({ profile, names }: { profile: Profile; names: Names }) {
  const t = useTranslations("chart");
  const g = useTranslations("glossary");
  const qc = useQueryClient();
  const [style, setStyle] = useState(profile.settings.chart_style);
  const [second, setSecond] = useState<VargaCode>("D9");
  const [chalit, setChalit] = useState(false);
  const { data: chart, isLoading } = useChart(profile.id, [second], chalit);

  async function changeStyle(s: "north" | "south") {
    setStyle(s); // redraw at once, no reload (US-28)
    await api(`/v1/profiles/${profile.id}`, { method: "PUT", json: { ...profile, settings: { ...profile.settings, chart_style: s } } }).catch(() => undefined);
    qc.invalidateQueries({ queryKey: ["profile", profile.id] });
  }

  if (isLoading || !chart) return <Spinner label={t("loading")} />;
  const common = { style, ascLabel: t("asc"), houseWord: t("house"), emptyWord: t("empty") };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <fieldset className="flex items-center gap-2">
          <legend className="sr-only">{t("style")}</legend>
          {(["north", "south"] as const).map((s) => (
            <label key={s} className="flex min-h-11 items-center gap-2 rounded-lg border border-border px-3 text-sm">
              <input type="radio" name="style" checked={style === s} onChange={() => changeStyle(s)} /> {t(s)}
            </label>
          ))}
        </fieldset>
        <label className="flex flex-col gap-1 text-sm">
          {t("second")}
          <Select value={second} onChange={(e) => setSecond(e.target.value as VargaCode)} className="min-w-56">
            {VARGA_CODES.filter((c) => c !== "D1").map((c) => <option key={c} value={c}>{names.vargas[c]}</option>)}
          </Select>
        </label>
        <label className="flex min-h-11 items-center gap-2 text-sm">
          <input type="checkbox" checked={chalit} onChange={(e) => setChalit(e.target.checked)} className="h-5 w-5" /> {t("chalit")}
        </label>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col items-center gap-2">
          <h2 className="font-semibold"><Term meaning={g("rasi")}>{names.vargas.D1}</Term></h2>
          <Kundli {...common} {...kundliProps(chart, "D1", names)} title={names.vargas.D1} centreText={style === "south" ? "D1" : undefined} />
        </div>
        <div className="flex flex-col items-center gap-2">
          <h2 className="font-semibold"><Term meaning={second === "D9" ? g("navamsa") : g("varga")}>{names.vargas[second]}</Term></h2>
          {chart.vargas[second] ? (
            <Kundli {...common} {...kundliProps(chart, second, names)} title={names.vargas[second]} centreText={style === "south" ? second : undefined} />
          ) : <Spinner />}
        </div>
      </div>

      {chalit && chart.bhava_chalit && (
        <div>
          <h2 className="font-semibold">{t("chalitTitle")}</h2>
          <p className="text-sm text-muted">{t("chalitNote")}</p>
          <ul className="mt-2 flex flex-wrap gap-2 text-sm">
            {chart.planets.map((p) => {
              const b = chart.bhava_chalit!.planets[p.id];
              return (
                <li key={p.id} className={`rounded-md border px-2 py-1 ${b !== p.house ? "border-accent" : "border-border"}`}>
                  {names.planets[p.id]}: {t("house")} {b}{b !== p.house && ` (${t("rasiHouse")} ${p.house})`}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {chart.meta.ephemeris_source.includes("moshier") && <Alert kind="warn">{t("moshier")}</Alert>}
      <p className="text-xs text-muted">
        {t("meta", {
          ayanamsa: names.ayanamsas[chart.meta.ayanamsa],
          value: chart.meta.ayanamsa_value.toFixed(4),
          engine: chart.meta.engine_version,
          swe: chart.meta.ephemeris_version,
          node: t(`node_${chart.meta.settings.node_type}`),
        })}
      </p>
    </div>
  );
}

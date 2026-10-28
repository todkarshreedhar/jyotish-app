"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { Kundli } from "@/components/chart/Kundli";
import { kundliProps } from "@/components/tabs/ChartTab";
import { PlanetsTab } from "@/components/tabs/PlanetsTab";
import { ButtonLink, Card } from "@/components/ui";
import { api } from "@/lib/api";
import { useNames } from "@/lib/hooks";
import type { Chart } from "@/lib/types";

const DEFAULTS = { ayanamsa: "lahiri", node_type: "mean", chart_style: "north", dasha_year_days: 365.25 } as const;

/** Try a chart without an account. Nothing is saved. */
export default function TryPage() {
  const t = useTranslations("try");
  const c = useTranslations("chart");
  const { data: names } = useNames();
  const [chart, setChart] = useState<Chart | null>(null);
  const [style, setStyle] = useState<"north" | "south">("north");

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p className="text-sm text-muted">{t("intro")}</p>
      <Card>
        <BirthForm
          defaults={DEFAULTS}
          submitLabel={t("show")}
          onSubmit={async (p) => {
            const { name: _n, settings, gender: _g, folder: _f, is_main: _m, ...birth } = p;
            void _n; void _g; void _f; void _m;
            setStyle(settings.chart_style);
            setChart(await api<Chart>("/v1/charts", { method: "POST", json: { birth, settings, vargas: ["D1", "D9"] } }));
          }}
        />
      </Card>
      {chart && names && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            {(["D1", "D9"] as const).map((code) => (
              <div key={code} className="flex flex-col items-center gap-2">
                <h2 className="font-semibold">{names.vargas[code]}</h2>
                <Kundli style={style} {...kundliProps(chart, code, names)} ascLabel={c("asc")} houseWord={c("house")} emptyWord={c("empty")} title={names.vargas[code]} />
              </div>
            ))}
          </div>
          <PlanetsTab chart={chart} names={names} />
          <Card><p className="mb-3">{t("save")}</p><ButtonLink href="/login">{t("signup")}</ButtonLink></Card>
        </>
      )}
    </div>
  );
}

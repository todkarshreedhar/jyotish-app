"use client";

import { useTranslations } from "next-intl";
import { Badge, Table, Term } from "@/components/ui";
import type { Chart, Names } from "@/lib/types";

/** US-29: every graha with exact degrees. */
export function PlanetsTab({ chart, names }: { chart: Chart; names: Names }) {
  const t = useTranslations("planets");
  const g = useTranslations("glossary");
  return (
    <Table caption={t("caption")}>
      <thead>
        <tr>
          <th scope="col">{t("planet")}</th>
          <th scope="col">{t("sign")}</th>
          <th scope="col">{t("degree")}</th>
          <th scope="col"><Term meaning={g("nakshatra")}>{t("nakshatra")}</Term></th>
          <th scope="col"><Term meaning={g("pada")}>{t("pada")}</Term></th>
          <th scope="col"><Term meaning={g("house")}>{t("house")}</Term></th>
          <th scope="col"><Term meaning={g("dignity")}>{t("dignity")}</Term></th>
          <th scope="col">{t("status")}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">{t("lagna")}</th>
          <td>{names.signs[chart.lagna.sign]}</td>
          <td className="font-mono">{chart.lagna.dms}</td>
          <td>{names.nakshatras[chart.lagna.nakshatra]}</td>
          <td>{chart.lagna.pada}</td>
          <td>1</td>
          <td />
          <td />
        </tr>
        {chart.planets.map((p) => (
          <tr key={p.id}>
            <th scope="row">{names.planets[p.id]}</th>
            <td>{names.signs[p.sign]}</td>
            <td className="font-mono">{p.dms}</td>
            <td>{names.nakshatras[p.nakshatra]} <span className="text-xs text-muted">({names.planets[p.nakshatra_lord]})</span></td>
            <td>{p.pada}</td>
            <td>{p.house}</td>
            <td>{names.dignities[p.dignity] ?? p.dignity}</td>
            <td className="flex flex-wrap gap-1">
              {p.retrograde && p.id !== "rahu" && p.id !== "ketu" && <Badge tone="danger"><Term meaning={g("retrograde")}>{t("retro")}</Term></Badge>}
              {p.combust && <Badge tone="accent"><Term meaning={g("combust")}>{t("combust")}</Term></Badge>}
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

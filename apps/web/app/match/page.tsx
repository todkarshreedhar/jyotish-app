"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Kundli } from "@/components/chart/Kundli";
import { RequireUser } from "@/components/RequireUser";
import { kundliProps } from "@/components/tabs/ChartTab";
import { Alert, Badge, Button, ButtonLink, Card, Field, Select, Table, Term } from "@/components/ui";
import { api, errorText } from "@/lib/api";
import { useNames, useProfiles } from "@/lib/hooks";
import type { MatchResult } from "@/lib/types";

/** US-65 to US-68: Ashtakoota score, Manglik check, charts side by side, PDF. */
function Match() {
  const t = useTranslations("match");
  const g = useTranslations("glossary");
  const c = useTranslations("chart");
  const qc = useQueryClient();
  const { data: profiles } = useProfiles();
  const { data: names } = useNames();
  const [boy, setBoy] = useState("");
  const [girl, setGirl] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfQueued, setPdfQueued] = useState(false);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api<MatchResult>("/v1/match", { method: "POST", json: { boy_profile_id: boy, girl_profile_id: girl } }));
      setPdfQueued(false);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  async function pdf() {
    await api("/v1/reports", { method: "POST", json: { profile_id: boy, partner_profile_id: girl, kind: "match", lang: names?.lang ?? "en" } });
    qc.invalidateQueries({ queryKey: ["reports"] });
    setPdfQueued(true);
  }

  const items = profiles?.items ?? [];
  if (profiles && items.length < 2) return <Card><p>{t("needTwo")}</p><ButtonLink href="/profiles/new" className="mt-3">{t("add")}</ButtonLink></Card>;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <Card>
        <div className="grid gap-4 sm:grid-cols-3 sm:items-end">
          <Field label={t("boy")} htmlFor="boy">
            <Select id="boy" value={boy} onChange={(e) => setBoy(e.target.value)}>
              <option value="">{t("choose")}</option>
              {items.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
          </Field>
          <Field label={t("girl")} htmlFor="girl">
            <Select id="girl" value={girl} onChange={(e) => setGirl(e.target.value)}>
              <option value="">{t("choose")}</option>
              {items.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
          </Field>
          <Button onClick={run} busy={busy} disabled={!boy || !girl || boy === girl}>{t("run")}</Button>
        </div>
      </Card>
      {error && <Alert kind="error">{error}</Alert>}
      {result && names && (
        <>
          <Card title={<Term meaning={g("ashtakoota")}>{t("score")}</Term>} actions={<Button variant="secondary" onClick={pdf}>{t("pdf")}</Button>}>
            <p className="text-3xl font-bold text-primary">{result.ashtakoota.total} / 36</p>
            <p className="mb-3">{t(`verdict_${result.ashtakoota.verdict}`)}</p>
            {pdfQueued && <Alert kind="ok">{t("pdfQueued")}</Alert>}
            <Table caption={t("score")}>
              <thead><tr><th scope="col">{t("koota")}</th><th scope="col">{t("boy")}</th><th scope="col">{t("girl")}</th><th scope="col">{t("points")}</th></tr></thead>
              <tbody>
                {result.ashtakoota.kootas.map((k) => (
                  <tr key={k.koota}>
                    <th scope="row">{names.kootas[k.koota]}</th>
                    <td>{k.boy ? t.has(`v.${k.boy}`) ? t(`v.${k.boy}`) : names.planets[k.boy] ?? k.boy : ""}</td>
                    <td>{k.girl ? t.has(`v.${k.girl}`) ? t(`v.${k.girl}`) : names.planets[k.girl] ?? k.girl : ""}</td>
                    <td className={k.points === 0 ? "text-danger" : ""}>{k.points} / {k.max}</td>
                  </tr>
                ))}
                <tr>
                  <th scope="row"><Term meaning={g("manglik")}>{t("manglik")}</Term></th>
                  <td>{result.boy.manglik.is_manglik ? <Badge tone="danger">{t("yes")}</Badge> : t("no")}</td>
                  <td>{result.girl.manglik.is_manglik ? <Badge tone="danger">{t("yes")}</Badge> : t("no")}</td>
                  <td />
                </tr>
              </tbody>
            </Table>
            <p className="mt-2 text-xs text-muted">{t("note")}</p>
          </Card>
          <div className="grid gap-6 md:grid-cols-2">
            {(["boy", "girl"] as const).map((who) => (
              <Card key={who} title={`${t(who)}: ${result[who].profile.name}`}>
                <Kundli
                  style="north"
                  {...kundliProps(result[who].chart, "D1", names)}
                  ascLabel={c("asc")}
                  houseWord={c("house")}
                  emptyWord={c("empty")}
                  title={result[who].profile.name}
                />
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default function MatchPage() {
  return <RequireUser>{() => <Match />}</RequireUser>;
}

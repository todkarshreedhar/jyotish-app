"use client";

import { useTranslations } from "next-intl";
import { Spinner, Table, Term } from "@/components/ui";
import { useStrength } from "@/lib/hooks";
import { SIGN_KEYS, type Names } from "@/lib/types";

const SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"];

/** Ashtakavarga and Shadbala (US-61, US-62). */
export function StrengthTab({ profileId, names }: { profileId: string; names: Names }) {
  const t = useTranslations("strength");
  const g = useTranslations("glossary");
  const { data, isLoading } = useStrength(profileId);
  if (isLoading || !data) return <Spinner />;
  const av = data.ashtakavarga;
  const sb = data.shadbala;
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold"><Term meaning={g("ashtakavarga")}>{t("ashtakavarga")}</Term></h2>
        <Table caption={t("ashtakavarga")}>
          <thead>
            <tr>
              <th scope="col">{t("planet")}</th>
              {SIGN_KEYS.map((s) => <th key={s} scope="col" className="text-center">{names.sign_short[s]}</th>)}
              <th scope="col">{t("total")}</th>
            </tr>
          </thead>
          <tbody>
            {SEVEN.map((p) => (
              <tr key={p}>
                <th scope="row">{names.planets[p]}</th>
                {av.bhinna[p].map((n, i) => <td key={i} className="text-center">{n}</td>)}
                <td className="font-semibold">{av.bhinna[p].reduce((a, b) => a + b, 0)}</td>
              </tr>
            ))}
            <tr>
              <th scope="row">{t("sarva")}</th>
              {av.sarva.map((n, i) => <td key={i} className={`text-center font-semibold ${n >= 28 ? "text-ok" : n < 25 ? "text-danger" : ""}`}>{n}</td>)}
              <td className="font-semibold">{av.sarva_total}</td>
            </tr>
          </tbody>
        </Table>
        <p className="text-xs text-muted">{t("savNote")}</p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold"><Term meaning={g("shadbala")}>{t("shadbala")}</Term></h2>
        <Table caption={t("shadbala")}>
          <thead>
            <tr>
              <th scope="col">{t("planet")}</th>
              <th scope="col">{t("sthana")}</th>
              <th scope="col">{t("dig")}</th>
              <th scope="col">{t("kala")}</th>
              <th scope="col">{t("chesta")}</th>
              <th scope="col">{t("naisargika")}</th>
              <th scope="col">{t("drik")}</th>
              <th scope="col">{t("rupas")}</th>
              <th scope="col">{t("ratio")}</th>
            </tr>
          </thead>
          <tbody>
            {sb.ranking.map((p) => {
              const r = sb.planets[p];
              return (
                <tr key={p}>
                  <th scope="row">{names.planets[p]}</th>
                  <td>{r.sthana_total}</td>
                  <td>{r.dig}</td>
                  <td>{r.kala_total}</td>
                  <td>{r.chesta}</td>
                  <td>{r.naisargika}</td>
                  <td>{r.drik}</td>
                  <td className="font-semibold">{r.total_rupas} / {r.required_rupas}</td>
                  <td className={r.ratio >= 1 ? "text-ok" : "text-danger"}>{r.ratio}</td>
                </tr>
              );
            })}
          </tbody>
        </Table>
        <details className="text-xs text-muted">
          <summary className="cursor-pointer">{t("method")}</summary>
          <pre className="mt-2 whitespace-pre-wrap font-sans">{sb.method_notes}</pre>
        </details>
      </section>
    </div>
  );
}

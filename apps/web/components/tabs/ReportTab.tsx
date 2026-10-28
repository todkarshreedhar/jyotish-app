"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { ReportList } from "@/components/ReportList";
import { Alert, Button, Card, Select } from "@/components/ui";
import { api, download, errorText } from "@/lib/api";
import type { Profile } from "@/lib/types";

/** US-48, US-49 and the CSV degree table (US-73). */
export function ReportTab({ profile }: { profile: Profile }) {
  const t = useTranslations("report");
  const locale = useLocale();
  const qc = useQueryClient();
  const [lang, setLang] = useState(locale);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function request() {
    setBusy(true);
    setError(null);
    try {
      await api("/v1/reports", { method: "POST", json: { profile_id: profile.id, kind: "natal", lang } });
      qc.invalidateQueries({ queryKey: ["reports"] });
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card title={t("title")}>
        <p className="mb-3 text-sm text-muted">{t("intro")}</p>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            {t("language")}
            <Select value={lang} onChange={(e) => setLang(e.target.value)}>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="mr">मराठी</option>
            </Select>
          </label>
          <Button onClick={request} busy={busy}>{t("create")}</Button>
          <Button variant="secondary" onClick={() => download(`/v1/profiles/${profile.id}/export.csv`, "chart.csv")}>{t("csv")}</Button>
        </div>
        {error && <div className="mt-3"><Alert kind="error">{error}</Alert></div>}
      </Card>
      <ReportList profileId={profile.id} />
    </div>
  );
}

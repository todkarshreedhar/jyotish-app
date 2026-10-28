"use client";

import { useLocale, useTranslations } from "next-intl";
import { Badge, Button, Spinner } from "@/components/ui";
import { download } from "@/lib/api";
import { fmtDate, fmtDateTime } from "@/lib/format";
import { useReports } from "@/lib/hooks";

export function ReportList({ profileId }: { profileId?: string }) {
  const t = useTranslations("report");
  const locale = useLocale();
  const { data, isLoading } = useReports();
  if (isLoading) return <Spinner />;
  const items = (data?.items ?? []).filter((r) => !profileId || r.profile_id === profileId);
  if (!items.length) return <p className="text-sm text-muted">{t("none")}</p>;
  return (
    <ul className="flex flex-col gap-2" aria-live="polite">
      {items.map((r) => (
        <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-surface p-3 text-sm">
          <span>
            {t(`kind_${r.kind}`)} · {r.lang.toUpperCase()} · {fmtDateTime(r.created_at, locale)}{" "}
            <Badge tone={r.status === "ready" ? "ok" : r.status === "failed" ? "danger" : "neutral"}>{t(`status_${r.status}`)}</Badge>
          </span>
          <span className="flex items-center gap-2">
            {r.expires_at && <span className="text-xs text-muted">{t("expires", { date: fmtDate(r.expires_at, locale) })}</span>}
            {r.status === "ready" && <Button variant="secondary" onClick={() => download(`/v1/reports/${r.id}/download`, "report.pdf")}>{t("download")}</Button>}
            {(r.status === "queued" || r.status === "running") && <Spinner small />}
          </span>
        </li>
      ))}
    </ul>
  );
}

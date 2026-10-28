"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo, useState } from "react";
import { RequireUser } from "@/components/RequireUser";
import { TodayCard } from "@/components/TodayCard";
import { Badge, ButtonLink, Card, Input, Select, Spinner } from "@/components/ui";
import { fmtBirthDate } from "@/lib/format";
import { useProfiles } from "@/lib/hooks";
import type { Me } from "@/lib/types";

function Dashboard({ me }: { me: Me }) {
  const t = useTranslations("dashboard");
  const locale = useLocale();
  const { data, isLoading } = useProfiles();
  const [folder, setFolder] = useState("");
  const [q, setQ] = useState("");
  const pro = me.role !== "user";

  const items = useMemo(
    () => (data?.items ?? []).filter((p) => (!folder || p.folder === folder) && (!q || p.name.toLowerCase().includes(q.toLowerCase()))),
    [data, folder, q],
  );
  const main = data?.items.find((p) => p.is_main);
  const full = data ? data.count >= data.limit : false;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <div className="flex flex-col items-end gap-1">
          {full ? (
            <span aria-disabled className="inline-flex min-h-11 cursor-not-allowed items-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-text opacity-50">
              {t("add")}
            </span>
          ) : (
            <ButtonLink href="/profiles/new">{t("add")}</ButtonLink>
          )}
          {data && <span className="text-xs text-muted">{t("count", { count: data.count, limit: data.limit })}</span>}
        </div>
      </div>
      {full && <p role="status" className="text-sm text-danger">{t("limitReached", { limit: data?.limit ?? 10 })}</p>}

      {main && <TodayCard profile={main} />}

      {pro && data && data.count > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            {t("search")}
            <Input value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("folder")}
            <Select value={folder} onChange={(e) => setFolder(e.target.value)}>
              <option value="">{t("allFolders")}</option>
              {data.folders.map((f) => <option key={f} value={f}>{f}</option>)}
            </Select>
          </label>
        </div>
      )}

      {isLoading ? (
        <Spinner label={t("loading")} />
      ) : data && data.count === 0 ? (
        <Card>
          <p>{t("empty")}</p>
          <ButtonLink href="/profiles/new" className="mt-3">{t("addFirst")}</ButtonLink>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => (
            <li key={p.id}>
              <Link href={`/profiles/${p.id}`} className="flex h-full flex-col gap-1 rounded-xl border border-border bg-surface p-4 hover:border-primary">
                <span className="flex items-center gap-2 text-lg font-semibold">
                  {p.name} {p.is_main && <Badge tone="accent">{t("main")}</Badge>}
                </span>
                <span className="text-sm text-muted">{fmtBirthDate(p.birth_date, locale)} · {p.birth_time.slice(0, 5)}</span>
                {p.place_name && <span className="truncate text-sm text-muted">{p.place_name}</span>}
                {p.folder && <span className="text-xs text-muted">{p.folder}</span>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return <RequireUser>{(me) => <Dashboard me={me} />}</RequireUser>;
}

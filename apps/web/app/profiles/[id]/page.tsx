"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { RequireUser } from "@/components/RequireUser";
import { ChartTab } from "@/components/tabs/ChartTab";
import { DashaTab } from "@/components/tabs/DashaTab";
import { PlanetsTab } from "@/components/tabs/PlanetsTab";
import { ReadingsTab } from "@/components/tabs/ReadingsTab";
import { ReportTab } from "@/components/tabs/ReportTab";
import { StrengthTab } from "@/components/tabs/StrengthTab";
import { TransitsTab } from "@/components/tabs/TransitsTab";
import { Alert, Spinner, Tabs } from "@/components/ui";
import { errorText } from "@/lib/api";
import { fmtBirthDate, offsetLabel } from "@/lib/format";
import { useChart, useNames, useProfile } from "@/lib/hooks";

const TABS = ["chart", "planets", "dasha", "transits", "readings", "strength", "report"] as const;
type Tab = (typeof TABS)[number];

function ProfileView() {
  const { id } = useParams<{ id: string }>();
  const t = useTranslations("profile");
  const locale = useLocale();
  const router = useRouter();
  const params = useSearchParams();
  const tab = (TABS as readonly string[]).includes(params.get("tab") ?? "") ? (params.get("tab") as Tab) : "chart";
  const { data: profile, error } = useProfile(id);
  const { data: chart } = useChart(id, ["D1", "D9"]);
  const { data: names } = useNames();

  if (error) return <Alert kind="error">{errorText(error)}</Alert>;
  if (!profile || !names) return <Spinner label={t("loading")} />;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">{profile.name}</h1>
          <p className="text-sm text-muted">
            {fmtBirthDate(profile.birth_date, locale)} · {profile.birth_time.slice(0, 5)}
            {chart && ` (${offsetLabel(chart.input.utc_offset_minutes)})`} · {profile.place_name ?? `${profile.latitude.toFixed(3)}, ${profile.longitude.toFixed(3)}`}
          </p>
          {chart && (
            <p className="text-sm">
              {t("lagna")}: <strong>{names.signs[chart.lagna.sign]}</strong> · {t("moonSign")}:{" "}
              <strong>{names.signs[chart.planets[1].sign]}</strong> · {t("nakshatra")}:{" "}
              <strong>{names.nakshatras[chart.planets[1].nakshatra]} {chart.planets[1].pada}</strong>
            </p>
          )}
        </div>
        <Link href={`/profiles/${id}/edit`} className="inline-flex min-h-11 items-center rounded-lg border border-border px-3 text-sm">{t("edit")}</Link>
      </div>

      {profile.time_accuracy !== "exact" && (
        <Alert kind="warn">{t("timeWarning", { accuracy: t(`accuracy_${profile.time_accuracy}`) })}</Alert>
      )}

      <Tabs
        label={t("tabsLabel")}
        value={tab}
        onChange={(v) => router.replace(`/profiles/${id}?tab=${v}`, { scroll: false })}
        tabs={TABS.map((x) => ({ id: x, label: t(`tab_${x}`) }))}
      />
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="pt-2">
        {tab === "chart" && <ChartTab profile={profile} names={names} />}
        {tab === "planets" && chart && <PlanetsTab chart={chart} names={names} />}
        {tab === "dasha" && chart && <DashaTab chart={chart} names={names} tz={profile.tz_name} />}
        {tab === "transits" && <TransitsTab profileId={id} names={names} />}
        {tab === "readings" && <ReadingsTab profileId={id} names={names} />}
        {tab === "strength" && <StrengthTab profileId={id} names={names} />}
        {tab === "report" && <ReportTab profile={profile} />}
        {!chart && tab !== "chart" && tab !== "transits" && tab !== "readings" && tab !== "strength" && tab !== "report" && <Spinner />}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <RequireUser>
      {() => (
        <Suspense>
          <ProfileView />
        </Suspense>
      )}
    </RequireUser>
  );
}

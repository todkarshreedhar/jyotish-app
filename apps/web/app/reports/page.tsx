"use client";

import { useTranslations } from "next-intl";
import { ReportList } from "@/components/ReportList";
import { RequireUser } from "@/components/RequireUser";

export default function ReportsPage() {
  const t = useTranslations("report");
  return (
    <RequireUser>
      {() => (
        <div className="flex flex-col gap-4">
          <h1 className="text-2xl font-bold">{t("allTitle")}</h1>
          <p className="text-sm text-muted">{t("retention")}</p>
          <ReportList />
        </div>
      )}
    </RequireUser>
  );
}

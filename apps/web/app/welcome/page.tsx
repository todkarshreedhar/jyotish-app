"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Alert, Button, Card } from "@/components/ui";
import { api, errorText } from "@/lib/api";
import { useConfig } from "@/lib/hooks";

// US-09: nobody continues without agreeing to how birth data is used.
function Welcome() {
  const t = useTranslations("consent");
  const { data: config } = useConfig();
  const router = useRouter();
  const params = useSearchParams();
  const qc = useQueryClient();
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function accept() {
    setBusy(true);
    try {
      await api("/v1/me/consent", { method: "POST", json: { accept: true, version: config?.consent_version } });
      await qc.invalidateQueries({ queryKey: ["me"] });
      router.replace(params.get("next") ?? "/dashboard");
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card level={1} title={t("title")}>
        <div className="flex flex-col gap-3 text-sm">
          <p>{t("intro")}</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>{t("p1")}</li>
            <li>{t("p2")}</li>
            <li>{t("p3")}</li>
            <li>{t("p4")}</li>
          </ul>
          <p>
            {t.rich("more", { link: (c) => <Link href="/privacy" className="underline">{c}</Link> })}
          </p>
          <label className="mt-2 flex items-start gap-3 rounded-lg bg-surface-2 p-3">
            <input type="checkbox" className="mt-1 h-5 w-5" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            <span>{t("checkbox")}</span>
          </label>
          {error && <Alert kind="error">{error}</Alert>}
          <Button onClick={accept} disabled={!agree} busy={busy}>{t("continue")}</Button>
        </div>
      </Card>
    </div>
  );
}

export default function WelcomePage() {
  return (
    <Suspense>
      <Welcome />
    </Suspense>
  );
}

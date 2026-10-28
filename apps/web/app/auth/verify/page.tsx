"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { Alert, ButtonLink, Spinner } from "@/components/ui";
import { api, errorText } from "@/lib/api";

// Email links open this page; the page (not the link itself) signs in, so
// email scanners that pre-open links cannot use up the one-time token.
function Verify() {
  const t = useTranslations("login");
  const params = useSearchParams();
  const router = useRouter();
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const token = params.get("token") ?? "";
    const next = params.get("next") ?? "/dashboard";
    api<{ needs_consent: boolean }>("/v1/auth/email/verify", { method: "POST", json: { token } })
      .then((r) => {
        qc.invalidateQueries({ queryKey: ["me"] });
        router.replace(r.needs_consent ? `/welcome?next=${encodeURIComponent(next)}` : next);
      })
      .catch((e) => setError(errorText(e)));
  }, [params, router, qc]);

  if (error)
    return (
      <div className="mx-auto flex max-w-md flex-col gap-4">
        <Alert kind="error">{error}</Alert>
        <ButtonLink href="/login">{t("tryAgain")}</ButtonLink>
      </div>
    );
  return <Spinner label={t("signingIn")} />;
}

export default function VerifyPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}

"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Alert, Button, Card, Field, Input } from "@/components/ui";
import { api, errorText } from "@/lib/api";
import { useConfig } from "@/lib/hooks";

function LoginForm() {
  const t = useTranslations("login");
  const locale = useLocale();
  const params = useSearchParams();
  const next = params.get("next") ?? "/dashboard";
  const { data: config } = useConfig();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(params.get("error") ? t("googleFailed") : null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api("/v1/auth/email/start", { method: "POST", json: { email, next, locale } });
      setSent(true);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <Card title={<span>{t("title")}</span>}>
        {sent ? (
          <Alert kind="ok">{t("sent", { email })}</Alert>
        ) : (
          <div className="flex flex-col gap-4">
            {config?.google_enabled && (
              <>
                <a
                  href={`/api/v1/auth/google/login?next=${encodeURIComponent(next)}`}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border bg-surface px-4 text-sm font-semibold hover:bg-surface-2"
                >
                  <span aria-hidden className="font-bold text-[#4285F4]">G</span> {t("google")}
                </a>
                <p className="text-center text-xs text-muted">{t("or")}</p>
              </>
            )}
            <form onSubmit={submit} className="flex flex-col gap-3" noValidate>
              <Field label={t("email")} htmlFor="email" hint={t("emailHint")}>
                <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
              </Field>
              <Button type="submit" busy={busy} disabled={!email.includes("@")}>{t("sendLink")}</Button>
            </form>
            {error && <Alert kind="error">{error}</Alert>}
          </div>
        )}
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

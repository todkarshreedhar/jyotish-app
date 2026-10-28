"use client";

import { useTranslations } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { RequireUser } from "@/components/RequireUser";
import { Alert, Button, Card, Spinner } from "@/components/ui";
import { api, errorText } from "@/lib/api";
import { useProfile, useSaveProfile } from "@/lib/hooks";
import { useQueryClient } from "@tanstack/react-query";

export default function EditProfilePage() {
  const { id } = useParams<{ id: string }>();
  const t = useTranslations("form");
  const router = useRouter();
  const qc = useQueryClient();
  const { data: profile } = useProfile(id);
  const save = useSaveProfile(id);
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    try {
      await api(`/v1/profiles/${id}`, { method: "DELETE" });
      qc.invalidateQueries({ queryKey: ["profiles"] });
      router.push("/dashboard");
    } catch (e) {
      setError(errorText(e));
    }
  }

  return (
    <RequireUser>
      {(me) =>
        !profile ? (
          <Spinner />
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-4">
            <Card level={1} title={t("editTitle", { name: profile.name })}>
              <BirthForm
                initial={profile}
                defaults={me.default_settings}
                submitLabel={t("save")}
                showFolder={me.role !== "user"}
                onSubmit={async (body) => {
                  await save.mutateAsync(body);
                  router.push(`/profiles/${id}`);
                }}
              />
            </Card>
            <Card title={t("deleteTitle")}>
              {confirm ? (
                <div className="flex flex-wrap items-center gap-3">
                  <p className="text-sm">{t("deleteConfirm", { name: profile.name })}</p>
                  <Button variant="danger" onClick={remove}>{t("deleteYes")}</Button>
                  <Button variant="secondary" onClick={() => setConfirm(false)}>{t("cancel")}</Button>
                </div>
              ) : (
                <Button variant="secondary" onClick={() => setConfirm(true)}>{t("delete")}</Button>
              )}
              {error && <Alert kind="error">{error}</Alert>}
            </Card>
          </div>
        )
      }
    </RequireUser>
  );
}

"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { BirthForm } from "@/components/BirthForm";
import { RequireUser } from "@/components/RequireUser";
import { Card } from "@/components/ui";
import { useSaveProfile } from "@/lib/hooks";

export default function NewProfilePage() {
  const t = useTranslations("form");
  const router = useRouter();
  const save = useSaveProfile();
  return (
    <RequireUser>
      {(me) => (
        <div className="mx-auto max-w-2xl">
          <Card title={t("newTitle")}>
            <BirthForm
              defaults={me.default_settings}
              submitLabel={t("save")}
              showFolder={me.role !== "user"}
              onSubmit={async (body) => {
                const p = await save.mutateAsync(body);
                router.push(`/profiles/${p.id}`);
              }}
            />
          </Card>
        </div>
      )}
    </RequireUser>
  );
}

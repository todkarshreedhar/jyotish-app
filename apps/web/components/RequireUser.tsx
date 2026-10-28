"use client";

import { useTranslations } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useMe } from "@/lib/hooks";
import type { Me } from "@/lib/types";
import { Spinner } from "./ui";

/** Shows children only to signed-in users who have given consent. */
export function RequireUser({ children, admin }: { children: (me: Me) => ReactNode; admin?: boolean }) {
  const { data: me, isLoading } = useMe();
  const router = useRouter();
  const path = usePathname();
  const t = useTranslations("common");

  useEffect(() => {
    if (isLoading) return;
    if (me === null) router.replace(`/login?next=${encodeURIComponent(path)}`);
    else if (me && !me.consent.given) router.replace(`/welcome?next=${encodeURIComponent(path)}`);
  }, [me, isLoading, router, path]);

  if (!me || !me.consent.given) return <Spinner label={t("loading")} />;
  if (admin && me.role !== "admin") return <p>{t("forbidden")}</p>;
  return <>{children(me)}</>;
}

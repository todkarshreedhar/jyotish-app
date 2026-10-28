"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useMe } from "@/lib/hooks";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { cx } from "./ui";

export function SiteHeader() {
  const t = useTranslations("nav");
  const { data: me } = useMe();
  const path = usePathname();
  const router = useRouter();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const links = me
    ? [
        { href: "/dashboard", label: t("dashboard") },
        { href: "/panchang", label: t("panchang") },
        { href: "/match", label: t("match") },
        { href: "/reports", label: t("reports") },
        { href: "/settings", label: t("settings") },
        ...(me.role === "admin" ? [{ href: "/admin", label: t("admin") }] : []),
      ]
    : [
        { href: "/panchang", label: t("panchang") },
        { href: "/try", label: t("try") },
      ];

  async function logout() {
    await api("/v1/auth/logout", { method: "POST" });
    qc.clear();
    router.push("/");
    router.refresh();
  }

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2 sm:px-6">
        <Link href={me ? "/dashboard" : "/"} className="flex items-center gap-2 text-lg font-bold text-primary">
          <span aria-hidden className="text-2xl">☉</span>
          {t("brand")}
        </Link>
        <button className="min-h-11 rounded-md px-3 md:hidden" aria-expanded={open} aria-controls="main-nav" onClick={() => setOpen((o) => !o)}>
          {t("menu")}
        </button>
        <nav id="main-nav" aria-label={t("main")} className={cx("absolute left-0 right-0 top-14 z-30 border-b border-border bg-surface p-3 md:static md:block md:border-0 md:p-0", open ? "block" : "hidden")}>
          <ul className="flex flex-col gap-1 md:flex-row md:items-center md:gap-2">
            {links.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  onClick={() => setOpen(false)}
                  aria-current={path.startsWith(l.href) ? "page" : undefined}
                  className={cx("block rounded-md px-3 py-2 text-sm", path.startsWith(l.href) ? "bg-surface-2 font-semibold text-primary" : "hover:bg-surface-2")}
                >
                  {l.label}
                </Link>
              </li>
            ))}
            <li><LanguageSwitcher /></li>
            <li>
              {me ? (
                <button onClick={logout} className="min-h-10 rounded-md px-3 text-sm hover:bg-surface-2">{t("logout")}</button>
              ) : (
                <Link href="/login" className="inline-flex min-h-10 items-center rounded-md bg-primary px-3 text-sm font-semibold text-primary-text">{t("login")}</Link>
              )}
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

import { getTranslations } from "next-intl/server";
import Link from "next/link";

export async function SiteFooter() {
  const t = await getTranslations("footer");
  return (
    <footer className="border-t border-border bg-surface text-sm text-muted">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>{t("tagline")}</p>
        <ul className="flex flex-wrap gap-4">
          <li><Link href="/privacy" className="underline">{t("privacy")}</Link></li>
          <li><Link href="/terms" className="underline">{t("terms")}</Link></li>
          <li><Link href="/developers" className="underline">{t("developers")}</Link></li>
          <li><a href="https://github.com/todkarshreedhar/jyotish-app" className="underline" rel="noopener">{t("source")}</a></li>
        </ul>
      </div>
    </footer>
  );
}

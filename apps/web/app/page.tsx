import { getTranslations } from "next-intl/server";
import { ButtonLink } from "@/components/ui";

export default async function Home() {
  const t = await getTranslations("home");
  const features = ["accuracy", "charts", "dasha", "readings", "languages", "privacy"] as const;
  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-2xl bg-surface-2 px-6 py-10 sm:px-10">
        <h1 className="max-w-2xl text-3xl font-bold leading-tight sm:text-4xl">{t("title")}</h1>
        <p className="mt-3 max-w-2xl text-lg text-muted">{t("lead")}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <ButtonLink href="/login">{t("start")}</ButtonLink>
          <ButtonLink href="/try" variant="secondary">{t("try")}</ButtonLink>
        </div>
        <p className="mt-4 text-sm text-muted">{t("free")}</p>
      </section>
      <section aria-labelledby="features">
        <h2 id="features" className="sr-only">{t("featuresTitle")}</h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <li key={f} className="rounded-xl border border-border bg-surface p-5">
              <h3 className="font-semibold">{t(`features.${f}.title`)}</h3>
              <p className="mt-1 text-sm text-muted">{t(`features.${f}.text`)}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

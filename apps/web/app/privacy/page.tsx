import { getTranslations } from "next-intl/server";

export const metadata = { title: "Privacy" };

// US-59: draft text. It must be reviewed by a lawyer before launch, and the
// consent text on /welcome must match it.
export default async function Privacy() {
  const t = await getTranslations("privacy");
  const sections = ["what", "why", "where", "who", "keep", "rights", "contact"] as const;
  return (
    <article className="mx-auto flex max-w-3xl flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p className="rounded-lg bg-surface-2 p-3 text-sm">{t("draft")}</p>
      {sections.map((s) => (
        <section key={s}>
          <h2 className="text-lg font-semibold">{t(`${s}.h`)}</h2>
          <p className="mt-1 text-muted">{t(`${s}.p`)}</p>
        </section>
      ))}
    </article>
  );
}

import { getTranslations } from "next-intl/server";

export const metadata = { title: "Terms" };

export default async function Terms() {
  const t = await getTranslations("terms");
  const sections = ["service", "advice", "accounts", "license", "changes"] as const;
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

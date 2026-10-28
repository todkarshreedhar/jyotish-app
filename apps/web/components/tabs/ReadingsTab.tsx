"use client";

import { useTranslations } from "next-intl";
import { Badge, Spinner } from "@/components/ui";
import { useReadings } from "@/lib/hooks";
import type { Names, Reading } from "@/lib/types";

const ORDER = ["personality", "career", "wealth", "family", "relationships", "health", "spirituality", "general"];

/** US-43: readings grouped by topic, each with its rule ID and source. */
export function ReadingsTab({ profileId, names }: { profileId: string; names: Names }) {
  const t = useTranslations("readings");
  const { data, isLoading } = useReadings(profileId);
  if (isLoading || !data) return <Spinner />;
  const groups = new Map<string, Reading[]>();
  for (const r of data.readings) groups.set(r.topic, [...(groups.get(r.topic) ?? []), r]);
  const topics = ORDER.filter((x) => groups.has(x));

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-muted">{t("intro")}</p>
      {topics.length === 0 && <p>{t("none")}</p>}
      {topics.map((topic) => (
        <section key={topic} aria-labelledby={`topic-${topic}`}>
          <h2 id={`topic-${topic}`} className="mb-2 text-lg font-semibold">{names.topics[topic]}</h2>
          <ul className="flex flex-col gap-3">
            {groups.get(topic)!.map((r) => (
              <li key={r.id} className="rounded-xl border border-border bg-surface p-4">
                <p className="flex flex-wrap items-center gap-2 font-semibold">
                  {r.title} {r.kind === "dosha" && <Badge tone="danger">{t("dosha")}</Badge>} {r.kind === "yoga" && <Badge tone="accent">{t("yoga")}</Badge>}
                </p>
                <p className="mt-1 text-sm">{r.text}</p>
                <p className="mt-2 text-xs text-muted">{t("source", { source: r.source, id: r.id })}</p>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <p className="text-xs text-muted">{t("footer", { version: data.ruleset_version })}</p>
    </div>
  );
}

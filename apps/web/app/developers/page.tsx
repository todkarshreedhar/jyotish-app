import { getTranslations } from "next-intl/server";

export const metadata = { title: "Developers" };

const PY = `import requests

r = requests.post(
    "https://YOUR-DOMAIN/api/public/v1/chart",
    headers={"X-API-Key": "jy_..."},
    json={"birth": {"birth_date": "1990-05-15", "birth_time": "10:30:00",
                    "latitude": 18.5204, "longitude": 73.8567, "tz_name": "Asia/Kolkata"},
          "vargas": ["D1", "D9"]},
    timeout=10,
)
r.raise_for_status()
chart = r.json()
print(chart["lagna"]["sign"], [p["sign"] for p in chart["planets"]])`;

const JS = `const res = await fetch("https://YOUR-DOMAIN/api/public/v1/chart", {
  method: "POST",
  headers: { "X-API-Key": "jy_...", "Content-Type": "application/json" },
  body: JSON.stringify({
    birth: { birth_date: "1990-05-15", birth_time: "10:30:00",
             latitude: 18.5204, longitude: 73.8567, tz_name: "Asia/Kolkata" },
    vargas: ["D1", "D9"],
  }),
});
const chart = await res.json();
console.log(chart.lagna.sign, chart.planets.map((p) => p.sign));`;

/** US-79, US-80: public API documentation and samples. */
export default async function Developers() {
  const t = await getTranslations("developers");
  return (
    <article className="mx-auto flex max-w-3xl flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p>{t("intro")}</p>
      <ul className="list-disc pl-5 text-sm">
        <li><code>POST /api/public/v1/chart</code> — {t("chart")}</li>
        <li><code>GET /api/public/v1/panchang?on=YYYY-MM-DD&amp;lat=..&amp;lon=..</code> — {t("panchang")}</li>
        <li><code>POST /api/public/v1/match</code> — {t("match")}</li>
      </ul>
      <p className="text-sm">{t.rich("docs", { link: (c) => <a className="underline" href="/api/docs">{c}</a> })}</p>
      <p className="text-sm">{t("limits")}</p>
      <h2 className="text-lg font-semibold">Python</h2>
      <pre className="overflow-auto rounded-lg bg-surface-2 p-3 text-xs"><code>{PY}</code></pre>
      <h2 className="text-lg font-semibold">JavaScript</h2>
      <pre className="overflow-auto rounded-lg bg-surface-2 p-3 text-xs"><code>{JS}</code></pre>
      <p className="text-sm text-muted">{t("license")}</p>
    </article>
  );
}

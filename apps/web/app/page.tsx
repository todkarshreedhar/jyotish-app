import { getHealth, summary } from "@/lib/health";

// Always ask the API on each request, so the page shows live status.
export const dynamic = "force-dynamic";

export default async function Home() {
  // Inside Docker the web container reaches the API at http://api:8000.
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const health = await getHealth(apiUrl);

  const rows: [string, string][] = [
    ["API", health ? "up" : "down"],
    ["Database", health?.database ?? "unknown"],
    ["Redis", health?.redis ?? "unknown"],
    ["Engine version", health?.engine_version ?? "unknown"],
    ["Swiss Ephemeris", health?.swiss_ephemeris_version ?? "unknown"],
  ];

  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="text-2xl font-semibold">Jyotish App</h1>
      <p className="mt-2 text-lg">{summary(health)}</p>
      <table className="mt-6 w-full text-left">
        <tbody>
          {rows.map(([name, value]) => (
            <tr key={name} className="border-b">
              <th className="py-2 font-medium">{name}</th>
              <td className="py-2">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
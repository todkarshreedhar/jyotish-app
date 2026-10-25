export type Health = {
  status: "ok" | "degraded";
  database: "up" | "down";
  redis: "up" | "down";
  engine_version: string;
  swiss_ephemeris_version: string;
};

// Asks the API if everything is working. Returns null if the API cannot be reached.
export async function getHealth(apiUrl: string): Promise<Health | null> {
  try {
    const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

export function summary(health: Health | null): string {
  if (health === null) return "API is not reachable";
  return health.status === "ok" ? "All systems working" : "Some parts are down";
}
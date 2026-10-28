// Pure layout for North and South Indian charts (same geometry as the PDF
// renderer in apps/api/src/jyotish_api/services/svg.py).

export const SIZE = 400;

// North Indian: house -> [planet text centre, sign number position]
export const NORTH: Record<number, [[number, number], [number, number]]> = {
  1: [[200, 100], [200, 182]], 2: [[100, 36], [100, 86]], 3: [[36, 100], [86, 100]],
  4: [[100, 200], [182, 200]], 5: [[36, 300], [86, 300]], 6: [[100, 364], [100, 316]],
  7: [[200, 300], [200, 220]], 8: [[300, 364], [300, 316]], 9: [[364, 300], [316, 300]],
  10: [[300, 200], [220, 200]], 11: [[364, 100], [316, 100]], 12: [[300, 36], [300, 86]],
};

// North Indian house outlines (for hit areas and focus rings).
export const NORTH_SHAPES: Record<number, string> = {
  1: "200,0 300,100 200,200 100,100", 2: "0,0 200,0 100,100", 3: "0,0 100,100 0,200",
  4: "0,200 100,100 200,200 100,300", 5: "0,200 100,300 0,400", 6: "0,400 100,300 200,400",
  7: "200,400 100,300 200,200 300,300", 8: "200,400 300,300 400,400", 9: "400,400 300,300 400,200",
  10: "400,200 300,300 200,200 300,100", 11: "400,200 300,100 400,0", 12: "400,0 300,100 200,0",
};

// South Indian: sign index (0 = Aries) -> [col, row]. Pisces is top-left.
export const SOUTH: Record<number, [number, number]> = {
  11: [0, 0], 0: [1, 0], 1: [2, 0], 2: [3, 0], 3: [3, 1], 4: [3, 2],
  5: [3, 3], 6: [2, 3], 7: [1, 3], 8: [0, 3], 9: [0, 2], 10: [0, 1],
};

export type KPlanet = { id: string; house: number; sign_index: number; degree?: number | null; retrograde?: boolean };

export function houseOfSign(sign: number, lagnaSign: number): number {
  return ((sign - lagnaSign + 12) % 12) + 1;
}

export function signInHouse(house: number, lagnaSign: number): number {
  return (lagnaSign + house - 1) % 12;
}

export function groupByHouse(planets: KPlanet[]): Record<number, KPlanet[]> {
  const out: Record<number, KPlanet[]> = {};
  for (let h = 1; h <= 12; h++) out[h] = [];
  for (const p of planets) out[p.house].push(p);
  return out;
}

export function groupBySign(planets: KPlanet[]): Record<number, KPlanet[]> {
  const out: Record<number, KPlanet[]> = {};
  for (let s = 0; s < 12; s++) out[s] = [];
  for (const p of planets) out[p.sign_index].push(p);
  return out;
}

export function planetLabel(p: KPlanet, abbr: Record<string, string>): string {
  const deg = p.degree === null || p.degree === undefined ? "" : `${Math.floor(p.degree)}°`;
  const retro = p.retrograde && p.id !== "rahu" && p.id !== "ketu" ? "(R)" : "";
  return `${abbr[p.id] ?? p.id}${deg}${retro}`;
}

export function stackY(centre: number, count: number, lineHeight = 15): number[] {
  const start = centre - ((count - 1) * lineHeight) / 2;
  return Array.from({ length: count }, (_, i) => start + i * lineHeight);
}

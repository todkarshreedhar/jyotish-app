"use client";

import { useId } from "react";
import { groupByHouse, groupBySign, NORTH, NORTH_SHAPES, planetLabel, signInHouse, SIZE, SOUTH, stackY, type KPlanet } from "@/lib/kundli";

type Props = {
  style: "north" | "south";
  lagnaSign: number;
  planets: KPlanet[];
  abbr: Record<string, string>;
  signShort: string[];
  signNames: string[];
  planetNames: Record<string, string>;
  ascLabel: string;
  title: string;
  centreText?: string;
  houseWord: string;
  emptyWord: string;
};

const LINE = { stroke: "var(--chart-line)", strokeWidth: 2, fill: "none" } as const;

/**
 * North or South Indian chart as accessible SVG. Screen readers get a
 * text description of every house (US-31); sighted users get the drawing.
 */
export function Kundli(props: Props) {
  const { style, title } = props;
  const descId = useId();
  const description = describe(props);

  return (
    <figure className="kundli w-full max-w-[440px]">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-labelledby={`${descId}-t`} aria-describedby={`${descId}-d`} className="h-auto w-full select-none">
        <title id={`${descId}-t`}>{title}</title>
        <desc id={`${descId}-d`}>{description}</desc>
        <rect x={1} y={1} width={398} height={398} {...LINE} />
        {style === "north" ? <North {...props} /> : <South {...props} />}
      </svg>
      <figcaption className="sr-only">{description}</figcaption>
    </figure>
  );
}

function PlanetStack({ x, y, items, abbr }: { x: number; y: number; items: KPlanet[]; abbr: Record<string, string> }) {
  const ys = stackY(y, items.length);
  return (
    <>
      {items.map((p, i) => (
        <text key={p.id} x={x} y={ys[i]} textAnchor="middle" dominantBaseline="middle" className={p.retrograde && p.id !== "rahu" && p.id !== "ketu" ? "kundli-retro" : "kundli-planet"}>
          {planetLabel(p, abbr)}
        </text>
      ))}
    </>
  );
}

function North({ lagnaSign, planets, abbr, ascLabel }: Props) {
  const byHouse = groupByHouse(planets);
  return (
    <g>
      <path d="M0 0L400 400M400 0L0 400M200 0L400 200L200 400L0 200Z" {...LINE} />
      {Object.entries(NORTH).map(([h, [[px, py], [sx, sy]]]) => {
        const house = Number(h);
        return (
          <g key={h}>
            <polygon points={NORTH_SHAPES[house]} fill="transparent" />
            <text x={sx} y={sy} textAnchor="middle" dominantBaseline="middle" className="kundli-sign">
              {signInHouse(house, lagnaSign) + 1}
            </text>
            {house === 1 && (
              <text x={200} y={py - 38} textAnchor="middle" dominantBaseline="middle" className="kundli-asc">
                {ascLabel}
              </text>
            )}
            <PlanetStack x={px} y={py} items={byHouse[house]} abbr={abbr} />
          </g>
        );
      })}
    </g>
  );
}

function South({ lagnaSign, planets, abbr, signShort, ascLabel, centreText }: Props) {
  const c = SIZE / 4;
  const bySign = groupBySign(planets);
  return (
    <g>
      {[1, 2, 3].map((i) => (
        <g key={i}>
          <path d={`M${c * i} 0V${i === 2 ? c : SIZE}M${c * i} ${i === 2 ? c * 3 : 0}V${SIZE}`} {...LINE} />
          <path d={`M0 ${c * i}H${i === 2 ? c : SIZE}M${i === 2 ? c * 3 : 0} ${c * i}H${SIZE}`} {...LINE} />
        </g>
      ))}
      {Object.entries(SOUTH).map(([s, [col, row]]) => {
        const sign = Number(s);
        const x0 = col * c;
        const y0 = row * c;
        return (
          <g key={s}>
            <text x={x0 + 6} y={y0 + 14} className="kundli-sign">{signShort[sign]}</text>
            {sign === lagnaSign && (
              <>
                <path d={`M${x0} ${y0 + 24}L${x0 + 24} ${y0}`} {...LINE} />
                <text x={x0 + c - 6} y={y0 + 14} textAnchor="end" className="kundli-asc">{ascLabel}</text>
              </>
            )}
            <PlanetStack x={x0 + c / 2} y={y0 + c / 2 + 6} items={bySign[sign]} abbr={abbr} />
          </g>
        );
      })}
      {centreText && (
        <text x={200} y={200} textAnchor="middle" dominantBaseline="middle" className="kundli-centre">{centreText}</text>
      )}
    </g>
  );
}

function describe({ lagnaSign, planets, signNames, planetNames, houseWord, emptyWord }: Props): string {
  const byHouse = groupByHouse(planets);
  const parts: string[] = [];
  for (let h = 1; h <= 12; h++) {
    const sign = signNames[signInHouse(h, lagnaSign)];
    const ps = byHouse[h].map((p) => `${planetNames[p.id]}${p.degree != null ? ` ${Math.floor(p.degree)}°` : ""}`);
    parts.push(`${houseWord} ${h}, ${sign}: ${ps.length ? ps.join(", ") : emptyWord}`);
  }
  return parts.join(". ") + ".";
}

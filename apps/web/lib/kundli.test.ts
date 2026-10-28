import { describe, expect, it } from "vitest";
import { groupByHouse, houseOfSign, NORTH, planetLabel, signInHouse, SOUTH } from "./kundli";

describe("kundli layout", () => {
  it("counts houses from the lagna sign", () => {
    expect(houseOfSign(3, 3)).toBe(1);
    expect(houseOfSign(2, 3)).toBe(12);
    expect(signInHouse(1, 3)).toBe(3);
    expect(signInHouse(12, 3)).toBe(2);
  });

  it("has a place for every house and sign", () => {
    expect(Object.keys(NORTH)).toHaveLength(12);
    expect(new Set(Object.values(SOUTH).map(([c, r]) => `${c},${r}`)).size).toBe(12);
    // South Indian layout uses only the outer ring of the 4x4 grid.
    for (const [c, r] of Object.values(SOUTH)) expect(c === 0 || c === 3 || r === 0 || r === 3).toBe(true);
  });

  it("labels planets with degree and retrograde mark", () => {
    const abbr = { mars: "Ma", rahu: "Ra" };
    expect(planetLabel({ id: "mars", house: 1, sign_index: 0, degree: 12.9, retrograde: true }, abbr)).toBe("Ma12°(R)");
    expect(planetLabel({ id: "rahu", house: 1, sign_index: 0, degree: 3, retrograde: true }, abbr)).toBe("Ra3°");
    expect(planetLabel({ id: "mars", house: 1, sign_index: 0, degree: null }, abbr)).toBe("Ma");
  });

  it("groups planets by house", () => {
    const g = groupByHouse([{ id: "sun", house: 10, sign_index: 0 }, { id: "moon", house: 10, sign_index: 0 }]);
    expect(g[10].map((p) => p.id)).toEqual(["sun", "moon"]);
    expect(g[1]).toEqual([]);
  });
});

import { describe, expect, it } from "vitest";
import en from "../messages/en.json";
import hi from "../messages/hi.json";
import mr from "../messages/mr.json";

function flatten(obj: Record<string, unknown>, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === "object") Object.assign(out, flatten(v as Record<string, unknown>, key));
    else out[key] = String(v);
  }
  return out;
}

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}|<(\w+)>/g)].map((m) => m[1] ?? m[2]).sort();

describe("translations", () => {
  const base = flatten(en);
  for (const [name, msgs] of [["hi", hi], ["mr", mr]] as const) {
    const other = flatten(msgs);
    it(`${name} has the same keys as English`, () => {
      expect(Object.keys(other).sort()).toEqual(Object.keys(base).sort());
    });
    it(`${name} uses the same placeholders as English`, () => {
      for (const [k, v] of Object.entries(base)) expect([k, placeholders(other[k] ?? "")]).toEqual([k, placeholders(v)]);
    });
  }
});

import { describe, expect, it } from "vitest";
import { summary, type Health } from "./health";

const healthy: Health = {
  status: "ok",
  database: "up",
  redis: "up",
  engine_version: "0.1.0",
  swiss_ephemeris_version: "2.10.03",
};

describe("summary", () => {
  it("says all is well when the API is ok", () => {
    expect(summary(healthy)).toBe("All systems working");
  });

  it("says when the API cannot be reached", () => {
    expect(summary(null)).toBe("API is not reachable");
  });
});
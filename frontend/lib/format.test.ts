import { describe, expect, it } from "vitest";

import { formatInt, formatPercent, formatRisk } from "./format";

describe("formatRisk", () => {
  it("rounds halves up like the backend", () => {
    expect(formatRisk(22.5)).toBe("23");
    expect(formatRisk(21.49)).toBe("21");
  });

  it("never implies certainty at the extremes", () => {
    expect(formatRisk(99.8)).toBe("> 99");
    expect(formatRisk(0.2)).toBe("< 1");
  });
});

describe("number helpers", () => {
  it("formats percentages and integers", () => {
    expect(formatPercent(0.2769)).toBe("28%");
    expect(formatPercent(0.2769, 1)).toBe("27.7%");
    expect(formatInt(1274.4)).toBe("1,274");
  });
});

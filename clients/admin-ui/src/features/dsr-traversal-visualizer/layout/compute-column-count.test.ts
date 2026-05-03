import { computeColumnCount } from "./compute-column-count";

describe("computeColumnCount", () => {
  it("returns 1 for empty groups", () => {
    expect(computeColumnCount(0)).toBe(1);
  });

  it("stays at 1 column up through LANE_SINGLE_COL_MAX (5)", () => {
    expect(computeColumnCount(1)).toBe(1);
    expect(computeColumnCount(5)).toBe(1);
  });

  it("promotes to 2 columns above 5", () => {
    expect(computeColumnCount(6)).toBe(2);
    expect(computeColumnCount(12)).toBe(2);
  });

  it("promotes to 3 columns above 12", () => {
    expect(computeColumnCount(13)).toBe(3);
    expect(computeColumnCount(50)).toBe(3);
  });
});

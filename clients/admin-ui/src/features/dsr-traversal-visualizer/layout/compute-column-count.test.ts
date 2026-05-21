import { computeColumnCount } from "./compute-column-count";

describe("computeColumnCount", () => {
  it("returns 1 for empty groups", () => {
    expect(computeColumnCount(0)).toBe(1);
  });

  it("stays at 1 column up through LANE_SINGLE_COL_MAX (4)", () => {
    expect(computeColumnCount(1)).toBe(1);
    expect(computeColumnCount(4)).toBe(1);
  });

  it("promotes to 2 columns above 4", () => {
    expect(computeColumnCount(5)).toBe(2);
    expect(computeColumnCount(8)).toBe(2);
  });

  it("promotes to 3 columns above 8", () => {
    expect(computeColumnCount(9)).toBe(3);
    expect(computeColumnCount(50)).toBe(3);
  });
});

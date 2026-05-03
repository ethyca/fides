import { PreviewEdge } from "../types";
import { computeStages } from "./compute-stages";

const dep = (source: string, target: string): PreviewEdge => ({
  source,
  target,
  kind: "depends_on",
  dep_count: 1,
});

describe("computeStages", () => {
  it("treats every reachable integration as Stage 1 when only identity edges exist", () => {
    const reachIds = ["i:a", "i:b", "i:c"];
    const edges: PreviewEdge[] = [
      dep("identity-root", "i:a"),
      dep("identity-root", "i:b"),
      dep("identity-root", "i:c"),
    ];
    const stages = computeStages(reachIds, edges);
    expect(stages).toEqual({
      "i:a": 1,
      "i:b": 1,
      "i:c": 1,
    });
  });

  it("classifies a downstream integration as Stage 2", () => {
    const reachIds = ["i:a", "i:b"];
    const edges: PreviewEdge[] = [
      dep("identity-root", "i:a"),
      dep("i:a", "i:b"),
    ];
    const stages = computeStages(reachIds, edges);
    expect(stages).toEqual({ "i:a": 1, "i:b": 2 });
  });

  it("uses the longest path for converging dependencies", () => {
    const reachIds = ["i:a", "i:b", "i:c"];
    const edges: PreviewEdge[] = [
      dep("identity-root", "i:a"),
      dep("identity-root", "i:b"),
      dep("i:a", "i:c"),
      dep("i:b", "i:c"),
    ];
    const stages = computeStages(reachIds, edges);
    expect(stages["i:c"]).toBe(2);
  });

  it("treats orphans (no incoming dep edge) as Stage 1", () => {
    const reachIds = ["i:lonely"];
    const edges: PreviewEdge[] = [];
    const stages = computeStages(reachIds, edges);
    expect(stages["i:lonely"]).toBe(1);
  });

  it("ignores `gates` edges when computing depth", () => {
    const reachIds = ["i:a", "i:b"];
    const edges: PreviewEdge[] = [
      dep("identity-root", "i:a"),
      dep("identity-root", "i:b"),
      { source: "manual:t", target: "i:a", kind: "gates" },
    ];
    const stages = computeStages(reachIds, edges);
    expect(stages).toEqual({ "i:a": 1, "i:b": 1 });
  });

  it("never assigns a stage to identity-root", () => {
    const reachIds = ["i:a"];
    const edges: PreviewEdge[] = [dep("identity-root", "i:a")];
    const stages = computeStages(reachIds, edges);
    expect(stages["identity-root"]).toBeUndefined();
  });
});

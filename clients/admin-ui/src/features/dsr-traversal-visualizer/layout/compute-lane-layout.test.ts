import { LaneCollapseMap, TraversalPreviewResponse } from "../types";

import { computeLaneLayout } from "./compute-lane-layout";

const allExpanded: LaneCollapseMap = {
  identity: false,
  reach: false,
  gated: false,
  skipped: false,
};

const buildPayload = (
  overrides: Partial<TraversalPreviewResponse> = {},
): TraversalPreviewResponse =>
  ({
    property: { key: "p", name: "P" },
    action_type: "access",
    computed_at: "2026-05-03T00:00:00Z",
    cache_hit: false,
    warnings: [],
    identity_root: {
      id: "identity-root",
      identity_types: ["email"],
      privacy_center_forms: [],
    },
    integrations: [],
    manual_tasks: [],
    edges: [],
    ...overrides,
  }) as TraversalPreviewResponse;

describe("computeLaneLayout", () => {
  it("returns four lanes in identity → reach → gated → skipped order", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    expect(result.lanes.map((l) => l.id)).toEqual([
      "identity",
      "reach",
      "gated",
      "skipped",
    ]);
  });

  it("places identity at x=0", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    const identity = result.lanes.find((l) => l.id === "identity")!;
    expect(identity.x).toBe(0);
    expect(result.positions["identity-root"].x).toBe(0);
  });

  it("hides gated and skipped lanes when empty", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    expect(result.lanes.find((l) => l.id === "gated")!.hidden).toBe(true);
    expect(result.lanes.find((l) => l.id === "skipped")!.hidden).toBe(true);
  });

  it("groups reach integrations into stages", () => {
    const payload = buildPayload({
      integrations: [
        {
          id: "i:a",
          connection_key: "a",
          connector_type: "postgres",
          reachability: "reachable",
          action_status: "active",
          collection_count: { traversed: 1, total: 1 },
          data_categories: [],
          datasets: [],
        } as any,
        {
          id: "i:b",
          connection_key: "b",
          connector_type: "stripe",
          reachability: "reachable",
          action_status: "active",
          collection_count: { traversed: 1, total: 1 },
          data_categories: [],
          datasets: [],
        } as any,
      ],
      edges: [
        { source: "identity-root", target: "i:a", kind: "depends_on", dep_count: 1 },
        { source: "i:a", target: "i:b", kind: "depends_on", dep_count: 1 },
      ],
    });
    const result = computeLaneLayout(payload, allExpanded);
    const reach = result.lanes.find((l) => l.id === "reach")!;
    expect(reach.stages).toBeDefined();
    expect(reach.stages!.length).toBe(2);
    expect(reach.stages![0].nodeIds).toEqual(["i:a"]);
    expect(reach.stages![1].nodeIds).toEqual(["i:b"]);
  });

  it("collapses a lane when collapse map flags it", () => {
    const payload = buildPayload({
      integrations: [
        {
          id: "i:x",
          connection_key: "x",
          connector_type: "postgres",
          reachability: "unreachable",
          action_status: "active",
          collection_count: { traversed: 0, total: 1 },
          data_categories: [],
          datasets: [],
        } as any,
      ],
    });
    const collapse: LaneCollapseMap = { ...allExpanded, skipped: true };
    const result = computeLaneLayout(payload, collapse);
    const skipped = result.lanes.find((l) => l.id === "skipped")!;
    expect(skipped.collapsed).toBe(true);
    expect(skipped.width).toBeLessThan(120);
  });

  it("promotes a lane with 7 cards to a 2-column grid", () => {
    const integrations = Array.from({ length: 7 }, (_, i) => ({
      id: `i:${i}`,
      connection_key: `c${i}`,
      connector_type: "postgres",
      reachability: "reachable",
      action_status: "active",
      collection_count: { traversed: 1, total: 1 },
      data_categories: [],
      datasets: [],
    }));
    const edges = integrations.map((it) => ({
      source: "identity-root",
      target: it.id,
      kind: "depends_on" as const,
      dep_count: 1,
    }));
    const result = computeLaneLayout(
      buildPayload({ integrations: integrations as any, edges }),
      allExpanded,
    );
    const reach = result.lanes.find((l) => l.id === "reach")!;
    expect(reach.stages![0].columns).toBe(2);
  });
});

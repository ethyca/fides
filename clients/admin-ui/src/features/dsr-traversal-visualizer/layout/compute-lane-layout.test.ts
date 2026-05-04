import { STAGE_GAP_HORIZONTAL } from "../constants";
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

  it("anchors the identity lane at x=0 and places its card inside the lane padding", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    const identity = result.lanes.find((l) => l.id === "identity")!;
    expect(identity.x).toBe(0);
    // The card sits inside the lane's horizontal padding, not flush against
    // the lane's left edge. Asserting >0 keeps the test resilient to the
    // exact padding value while pinning the contract.
    expect(result.positions["identity-root"].x).toBeGreaterThan(0);
    expect(result.positions["identity-root"].x).toBeLessThan(identity.width);
  });

  it("hides gated and skipped lanes when empty", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    expect(result.lanes.find((l) => l.id === "gated")!.hidden).toBe(true);
    expect(result.lanes.find((l) => l.id === "skipped")!.hidden).toBe(true);
  });

  it("lays stages out horizontally with per-stage column counts", () => {
    // Stage 1 = 5 reachable systems queried directly from identity → 2-col
    // promotion. Stage 2 = 2 systems queried from Stage 1 → 1-col.
    const stage1 = Array.from({ length: 5 }, (_, i) => ({
      id: `i:s1-${i}`,
      connection_key: `s1-${i}`,
      connector_type: "postgres",
      reachability: "reachable" as const,
      action_status: "active" as const,
      collection_count: { traversed: 1, total: 1 },
      data_categories: [],
      datasets: [],
    }));
    const stage2 = Array.from({ length: 2 }, (_, i) => ({
      id: `i:s2-${i}`,
      connection_key: `s2-${i}`,
      connector_type: "stripe",
      reachability: "reachable" as const,
      action_status: "active" as const,
      collection_count: { traversed: 1, total: 1 },
      data_categories: [],
      datasets: [],
    }));
    const edges = [
      ...stage1.map((it) => ({
        source: "identity-root",
        target: it.id,
        kind: "depends_on" as const,
        dep_count: 1,
      })),
      ...stage2.map((it) => ({
        source: stage1[0].id,
        target: it.id,
        kind: "depends_on" as const,
        dep_count: 1,
      })),
    ];

    const result = computeLaneLayout(
      buildPayload({
        integrations: [...stage1, ...stage2] as any,
        edges,
      }),
      allExpanded,
    );

    const reach = result.lanes.find((l) => l.id === "reach")!;
    expect(reach.stages).toBeDefined();
    expect(reach.stages!.length).toBe(2);

    const [s1, s2] = reach.stages!;

    // Per-stage column promotion: 5 cards → 2 cols, 2 cards → 1 col.
    expect(s1.columns).toBe(2);
    expect(s2.columns).toBe(1);

    // Stages flow left-to-right with strictly ascending xStart.
    expect(s1.xStart).toBeLessThan(s2.xStart);

    // Stage 2's left edge sits exactly STAGE_GAP_HORIZONTAL past Stage 1's right edge.
    expect(s2.xStart - s1.xEnd).toBe(STAGE_GAP_HORIZONTAL);

    // Top-aligned: every stage uses the same gridY.
    expect(s2.gridY).toBe(s1.gridY);

    // Cards in stage 2 sit to the right of cards in stage 1.
    const s1FirstX = result.positions[s1.nodeIds[0]].x;
    const s2FirstX = result.positions[s2.nodeIds[0]].x;
    expect(s2FirstX).toBeGreaterThan(s1FirstX);

    // Cards in different stages share the first-row y (top-aligned).
    const s1FirstY = result.positions[s1.nodeIds[0]].y;
    const s2FirstY = result.positions[s2.nodeIds[0]].y;
    expect(s2FirstY).toBe(s1FirstY);

    // Reach lane is wide enough to hold both stages plus the gap.
    expect(reach.width).toBeGreaterThan(s1.width + s2.width);
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

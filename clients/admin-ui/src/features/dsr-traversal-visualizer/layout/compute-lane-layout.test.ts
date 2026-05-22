import { STAGE_GAP_HORIZONTAL } from "../constants";
import {
  ActionStatus,
  ActionType,
  IntegrationNodeData,
  LaneCollapseMap,
  LaneId,
  Reachability,
  TraversalPreviewResponse,
} from "../types";
import { computeLaneLayout } from "./compute-lane-layout";

const allExpanded: LaneCollapseMap = {
  [LaneId.IDENTITY]: false,
  [LaneId.REACH]: false,
  [LaneId.GATED]: false,
  [LaneId.SKIPPED]: false,
};

const buildPayload = (
  overrides: Partial<TraversalPreviewResponse> = {},
): TraversalPreviewResponse => ({
  property: { id: "p", name: "P" },
  action_type: ActionType.ACCESS,
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
});

const buildIntegration = (
  overrides: Partial<IntegrationNodeData> & Pick<IntegrationNodeData, "id">,
): IntegrationNodeData => ({
  connection_key: overrides.id,
  connector_type: "postgres",
  reachability: Reachability.REACHABLE,
  action_status: ActionStatus.ACTIVE,
  collection_count: { traversed: 1, total: 1 },
  data_categories: [],
  datasets: [],
  ...overrides,
});

describe("computeLaneLayout", () => {
  it("returns four lanes in identity → reach → gated → skipped order", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    expect(result.lanes.map((l) => l.id)).toEqual([
      LaneId.IDENTITY,
      LaneId.REACH,
      LaneId.GATED,
      LaneId.SKIPPED,
    ]);
  });

  it("anchors the identity lane at x=0 and places its card inside the lane padding", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    const identity = result.lanes.find((l) => l.id === LaneId.IDENTITY)!;
    expect(identity.x).toBe(0);
    // The card sits inside the lane's horizontal padding, not flush against
    // the lane's left edge. Asserting >0 keeps the test resilient to the
    // exact padding value while pinning the contract.
    expect(result.positions["identity-root"].x).toBeGreaterThan(0);
    expect(result.positions["identity-root"].x).toBeLessThan(identity.width);
  });

  it("hides gated and skipped lanes when empty", () => {
    const result = computeLaneLayout(buildPayload(), allExpanded);
    expect(result.lanes.find((l) => l.id === LaneId.GATED)!.hidden).toBe(true);
    expect(result.lanes.find((l) => l.id === LaneId.SKIPPED)!.hidden).toBe(
      true,
    );
  });

  it("lays stages out horizontally with per-stage column counts", () => {
    // Stage 1 = 5 reachable systems queried directly from identity → 2-col
    // promotion. Stage 2 = 2 systems queried from Stage 1 → 1-col.
    const stage1 = Array.from({ length: 5 }, (_, i) =>
      buildIntegration({ id: `i:s1-${i}` }),
    );
    const stage2 = Array.from({ length: 2 }, (_, i) =>
      buildIntegration({ id: `i:s2-${i}`, connector_type: "stripe" }),
    );
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
        integrations: [...stage1, ...stage2],
        edges,
      }),
      allExpanded,
    );

    const reach = result.lanes.find((l) => l.id === LaneId.REACH)!;
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
        buildIntegration({
          id: "i:x",
          reachability: Reachability.UNREACHABLE,
          collection_count: { traversed: 0, total: 1 },
        }),
      ],
    });
    const collapse: LaneCollapseMap = {
      ...allExpanded,
      [LaneId.SKIPPED]: true,
    };
    const result = computeLaneLayout(payload, collapse);
    const skipped = result.lanes.find((l) => l.id === LaneId.SKIPPED)!;
    expect(skipped.collapsed).toBe(true);
    expect(skipped.width).toBeLessThan(120);
  });

  it("promotes a lane with 7 cards to a 2-column grid", () => {
    const integrations = Array.from({ length: 7 }, (_, i) =>
      buildIntegration({ id: `i:${i}`, connection_key: `c${i}` }),
    );
    const edges = integrations.map((it) => ({
      source: "identity-root",
      target: it.id,
      kind: "depends_on" as const,
      dep_count: 1,
    }));
    const result = computeLaneLayout(
      buildPayload({ integrations, edges }),
      allExpanded,
    );
    const reach = result.lanes.find((l) => l.id === LaneId.REACH)!;
    expect(reach.stages![0].columns).toBe(2);
  });
});

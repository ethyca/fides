import {
  CARD_PITCH,
  COL_WIDTH,
  COLLAPSED_LANE_WIDTH,
  LANE_GAP,
  LANE_HEADER_HEIGHT,
  LANE_PADDING_BOTTOM,
  LANE_PADDING_X,
  LANE_Y_TOP,
  NODE_WIDTH,
  STAGE_GAP_HORIZONTAL,
  STAGE_HEADER_HEIGHT,
} from "../constants";
import {
  LaneBounds,
  LaneCollapseMap,
  LaneId,
  LaneLayoutResult,
  Reachability,
  StageBlock,
  TraversalPreviewResponse,
} from "../types";
import { computeColumnCount } from "./compute-column-count";
import { computeStages } from "./compute-stages";

/**
 * Lane width that accounts for inter-column gaps only between columns,
 * not after the last one. Symmetric horizontal padding around the card grid.
 */
const laneContentWidth = (cols: number): number =>
  LANE_PADDING_X * 2 + NODE_WIDTH + Math.max(0, cols - 1) * COL_WIDTH;

const LANE_LABELS: Record<LaneId, { label: string; tooltip: string }> = {
  [LaneId.IDENTITY]: {
    label: "Identity input",
    tooltip:
      "The identity values this property's privacy-center forms accept. Every traversal starts here.",
  },
  [LaneId.REACH]: {
    label: "Will be queried",
    tooltip:
      "These systems contain data that will be searched for the data subject's records when this DSR runs.",
  },
  [LaneId.GATED]: {
    label: "Gated by manual review",
    tooltip:
      "These manual tasks must be completed before the systems they gate will run.",
  },
  [LaneId.SKIPPED]: {
    label: "Not touched",
    tooltip:
      "These systems can't be reached with the identity types this property accepts, so the DSR won't query them.",
  },
};

const STAGE_COPY: Record<number, { label: string; tooltip: string }> = {
  1: {
    label: "Stage 1 · From identity",
    tooltip:
      "These systems are queried using the data subject's identity inputs (e.g., email) directly.",
  },
  2: {
    label: "Stage 2 · From upstream",
    tooltip:
      "These systems can't be queried with identity alone — they need an identifier returned from a Stage 1 system first.",
  },
};

const stageCopy = (n: number) =>
  STAGE_COPY[n] ?? {
    label: `Stage ${n} · From upstream`,
    tooltip:
      "These systems are queried after one or more upstream systems return an identifier.",
  };

/**
 * Build the four-lane layout for a traversal preview payload.
 *
 * Determinism: positions only depend on (payload, collapseMap). Same input
 * yields the same output, so React Flow won't re-jitter cards on re-render.
 */
export const computeLaneLayout = (
  payload: TraversalPreviewResponse,
  collapse: LaneCollapseMap,
): LaneLayoutResult => {
  const identityNodeId = payload.identity_root.id;
  const reachIntegrations = payload.integrations.filter(
    (i) => i.reachability !== Reachability.UNREACHABLE,
  );
  const skippedIntegrations = payload.integrations.filter(
    (i) => i.reachability === Reachability.UNREACHABLE,
  );

  const reachIds = reachIntegrations.map((i) => i.id);
  const stageMap = computeStages(reachIds, payload.edges);

  const stageGroups = new Map<number, typeof reachIntegrations>();
  reachIntegrations.forEach((i) => {
    const s = stageMap[i.id] ?? 1;
    const list = stageGroups.get(s);
    if (list) {
      list.push(i);
    } else {
      stageGroups.set(s, [i]);
    }
  });
  const sortedStages = [...stageGroups.entries()].sort((a, b) => a[0] - b[0]);

  const positions: Record<string, { x: number; y: number }> = {};
  const lanes: LaneBounds[] = [];

  let cursorX = 0;

  // ---- Identity lane ----
  const identityCollapsed = collapse.identity;
  const identityHidden = false;
  const identityWidth = identityCollapsed
    ? COLLAPSED_LANE_WIDTH
    : laneContentWidth(1);
  if (!identityCollapsed) {
    positions[identityNodeId] = {
      x: cursorX + LANE_PADDING_X,
      y: LANE_Y_TOP + LANE_HEADER_HEIGHT,
    };
  }
  lanes.push({
    id: LaneId.IDENTITY,
    x: cursorX,
    y: LANE_Y_TOP,
    width: identityWidth,
    height: LANE_HEADER_HEIGHT + CARD_PITCH + LANE_PADDING_BOTTOM,
    cardCount: 1,
    collapsed: identityCollapsed,
    hidden: identityHidden,
    label: LANE_LABELS.identity.label,
    tooltip: LANE_LABELS.identity.tooltip,
  });
  cursorX += identityWidth + LANE_GAP;

  // ---- Reach lane (with stages) ----
  const reachCollapsed = collapse.reach;
  const reachHidden = reachIntegrations.length === 0;

  let reachWidth: number;
  let reachHeight: number;
  const stageBlocks: StageBlock[] = [];

  if (reachCollapsed || reachHidden) {
    reachWidth = reachHidden ? 0 : COLLAPSED_LANE_WIDTH;
    reachHeight = LANE_HEADER_HEIGHT;
  } else {
    const headerY = LANE_HEADER_HEIGHT;
    const gridY = LANE_HEADER_HEIGHT + STAGE_HEADER_HEIGHT;
    let stageCursorX = 0; // lane-local, after LANE_PADDING_X is applied at card-positioning time
    // Only 0 when sortedStages is empty — unreachable here because reachHidden guards above.
    let maxRows = 0;

    sortedStages.forEach(([stageIndex, members], orderIdx) => {
      const cols = computeColumnCount(members.length);
      const rows = Math.ceil(members.length / cols);
      maxRows = Math.max(maxRows, rows);
      const stageWidth = NODE_WIDTH + (cols - 1) * COL_WIDTH;
      const ids: string[] = [];

      members.forEach((m, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        positions[m.id] = {
          x: cursorX + LANE_PADDING_X + stageCursorX + col * COL_WIDTH,
          y: LANE_Y_TOP + gridY + row * CARD_PITCH,
        };
        ids.push(m.id);
      });

      const copy = stageCopy(stageIndex);
      stageBlocks.push({
        index: stageIndex,
        label: copy.label,
        tooltip: copy.tooltip,
        nodeIds: ids,
        xStart: stageCursorX,
        xEnd: stageCursorX + stageWidth,
        width: stageWidth,
        headerY,
        gridY,
        columns: cols,
      });

      const isLast = orderIdx === sortedStages.length - 1;
      stageCursorX += stageWidth + (isLast ? 0 : STAGE_GAP_HORIZONTAL);
    });

    reachWidth = LANE_PADDING_X * 2 + stageCursorX;
    reachHeight =
      LANE_HEADER_HEIGHT +
      STAGE_HEADER_HEIGHT +
      maxRows * CARD_PITCH +
      LANE_PADDING_BOTTOM;
  }

  lanes.push({
    id: LaneId.REACH,
    x: cursorX,
    y: LANE_Y_TOP,
    width: reachWidth,
    height: reachHeight,
    cardCount: reachIntegrations.length,
    collapsed: reachCollapsed,
    hidden: reachHidden,
    label: LANE_LABELS.reach.label,
    tooltip: LANE_LABELS.reach.tooltip,
    stages: reachCollapsed || reachHidden ? undefined : stageBlocks,
  });
  cursorX += reachWidth + (reachHidden ? 0 : LANE_GAP);

  // ---- Gated lane ----
  const gatedTasks = payload.manual_tasks ?? [];
  const gatedHidden = gatedTasks.length === 0;
  const gatedCollapsed = collapse.gated && !gatedHidden;
  let gatedWidth = 0;
  let gatedHeight = LANE_HEADER_HEIGHT;
  if (!gatedHidden) {
    if (gatedCollapsed) {
      gatedWidth = COLLAPSED_LANE_WIDTH;
    } else {
      const cols = computeColumnCount(gatedTasks.length);
      const rows = Math.ceil(gatedTasks.length / cols);
      gatedTasks.forEach((t, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        positions[t.id] = {
          x: cursorX + LANE_PADDING_X + col * COL_WIDTH,
          y: LANE_HEADER_HEIGHT + row * CARD_PITCH,
        };
      });
      gatedWidth = laneContentWidth(cols);
      gatedHeight =
        LANE_HEADER_HEIGHT + rows * CARD_PITCH + LANE_PADDING_BOTTOM;
    }
  }
  lanes.push({
    id: LaneId.GATED,
    x: cursorX,
    y: LANE_Y_TOP,
    width: gatedWidth,
    height: gatedHeight,
    cardCount: gatedTasks.length,
    collapsed: gatedCollapsed,
    hidden: gatedHidden,
    label: LANE_LABELS.gated.label,
    tooltip: LANE_LABELS.gated.tooltip,
  });
  cursorX += gatedWidth + (gatedHidden ? 0 : LANE_GAP);

  // ---- Skipped lane (out of flow) ----
  const skippedHidden = skippedIntegrations.length === 0;
  const skippedCollapsed = collapse.skipped && !skippedHidden;
  let skippedWidth = 0;
  let skippedHeight = LANE_HEADER_HEIGHT;
  if (!skippedHidden) {
    if (skippedCollapsed) {
      skippedWidth = COLLAPSED_LANE_WIDTH;
    } else {
      const cols = computeColumnCount(skippedIntegrations.length);
      const rows = Math.ceil(skippedIntegrations.length / cols);
      skippedIntegrations.forEach((i, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        positions[i.id] = {
          x: cursorX + LANE_PADDING_X + col * COL_WIDTH,
          y: LANE_HEADER_HEIGHT + row * CARD_PITCH,
        };
      });
      skippedWidth = laneContentWidth(cols);
      skippedHeight =
        LANE_HEADER_HEIGHT + rows * CARD_PITCH + LANE_PADDING_BOTTOM;
    }
  }
  lanes.push({
    id: LaneId.SKIPPED,
    x: cursorX,
    y: LANE_Y_TOP,
    width: skippedWidth,
    height: skippedHeight,
    cardCount: skippedIntegrations.length,
    collapsed: skippedCollapsed,
    hidden: skippedHidden,
    label: LANE_LABELS.skipped.label,
    tooltip: LANE_LABELS.skipped.tooltip,
    outOfFlow: true,
  });
  const totalWidth = cursorX + skippedWidth;
  // Stretch collapsed lanes to match the tallest expanded lane so the
  // canvas reads as a row of equal-height strips. Without this, a
  // collapsed lane sits at LANE_HEADER_HEIGHT (~48px) and looks orphaned
  // next to a 700px-tall expanded reach lane.
  const expandedMaxHeight = Math.max(
    LANE_HEADER_HEIGHT,
    ...lanes.filter((l) => !l.collapsed && !l.hidden).map((l) => l.height),
  );
  const balancedLanes = lanes.map((l) =>
    l.collapsed && !l.hidden ? { ...l, height: expandedMaxHeight } : l,
  );
  const totalHeight = Math.max(...balancedLanes.map((l) => l.height));

  return {
    positions,
    lanes: balancedLanes,
    canvas: { width: totalWidth, height: totalHeight },
  };
};

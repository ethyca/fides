import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { EDGE_TYPES, NODE_HEIGHT, NODE_WIDTH } from "../constants";
import { LayoutDirection, layoutTraversal } from "../layout-utils";
import { AppNode, TraversalPreviewResponse } from "../types";

export interface TraversalGraph {
  nodes: AppNode[];
  edges: Edge[];
}

const edgeId = (kind: string, source: string, target: string) =>
  `edge:${kind}:${source}__${target}`;

const GRID_H_SPACING = NODE_WIDTH + 32;
const GRID_V_SPACING = NODE_HEIGHT + 60;
const GRID_GAP_BELOW_DAGRE = 80;
const IDENTITY_GAP_LEFT_OF_DAGRE = 80;
const MANUAL_TASK_ROW_GAP = 100;
const MANUAL_TASK_H_SPACING = NODE_WIDTH + 32;

export const useTraversalGraph = (
  payload: TraversalPreviewResponse | undefined,
  direction: LayoutDirection,
): TraversalGraph =>
  useMemo(() => {
    if (!payload) {
      return { nodes: [], edges: [] };
    }
    const nodes: AppNode[] = [
      {
        id: payload.identity_root.id,
        type: "identityRoot",
        data: payload.identity_root,
        position: { x: 0, y: 0 },
      },
      ...payload.integrations.map<AppNode>((i) => ({
        id: i.id,
        type: "integration",
        data: i,
        position: { x: 0, y: 0 },
      })),
      ...payload.manual_tasks.map<AppNode>((m) => ({
        id: m.id,
        type: "manualTask",
        data: m,
        position: { x: 0, y: 0 },
      })),
    ];

    const edges: Edge[] = payload.edges.map((e) => ({
      id: edgeId(e.kind, e.source, e.target),
      source: e.source,
      target: e.target,
      type: e.kind === "gates" ? EDGE_TYPES.GATES : EDGE_TYPES.DEPENDENCY,
      data: { dep_count: e.dep_count, kind: e.kind },
    }));

    // Split nodes into four groups:
    //   - identity-root: rendered to the left of the integration tree
    //   - manual tasks: rendered in their own row below the integration tree
    //   - linked integrations: have at least one dependency edge → dagre
    //   - isolated integrations: no edges (typically unreachable) → grid
    const dependencyLinkedIds = new Set<string>();
    edges.forEach((e) => {
      if (e.data?.kind === "depends_on") {
        dependencyLinkedIds.add(e.source);
        dependencyLinkedIds.add(e.target);
      }
    });

    let identityNode: AppNode | undefined;
    const manualTaskNodes: AppNode[] = [];
    const linkedNodes: AppNode[] = [];
    const isolatedNodes: AppNode[] = [];
    nodes.forEach((n) => {
      if (n.type === "identityRoot") {
        identityNode = n;
        return;
      }
      if (n.type === "manualTask") {
        manualTaskNodes.push(n);
        return;
      }
      if (dependencyLinkedIds.has(n.id)) {
        linkedNodes.push(n);
      } else {
        isolatedNodes.push(n);
      }
    });

    // Dagre lays out only the integration dependency tree. Identity, manual
    // tasks, and gates edges are excluded so they don't pull nodes into the
    // tree; we re-include them in the final edge list so React Flow still
    // routes them between our hand-placed nodes.
    const dagreInputEdges = edges.filter(
      (e) =>
        e.data?.kind === "depends_on" &&
        e.source !== "identity-root" &&
        e.target !== "identity-root",
    );

    const dagreOut = layoutTraversal(
      linkedNodes as Node[],
      dagreInputEdges,
      direction,
    );
    const dagreNodes = dagreOut.nodes as AppNode[];

    const dagreBounds = dagreNodes.length
      ? dagreNodes.reduce(
          (acc, n) => ({
            minX: Math.min(acc.minX, n.position.x),
            maxX: Math.max(acc.maxX, n.position.x + NODE_WIDTH),
            minY: Math.min(acc.minY, n.position.y),
            maxY: Math.max(acc.maxY, n.position.y + NODE_HEIGHT),
          }),
          { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity },
        )
      : null;

    // Identity-root: left of the dagre block, vertically aligned with the top.
    const identityPlaced: AppNode[] = [];
    if (identityNode) {
      const x = dagreBounds
        ? dagreBounds.minX - NODE_WIDTH - IDENTITY_GAP_LEFT_OF_DAGRE
        : 0;
      const y = dagreBounds ? dagreBounds.minY : 0;
      identityPlaced.push({ ...identityNode, position: { x, y } });
    }

    // Manual tasks: a horizontal row directly below the dagre block, aligned
    // to its left edge. Always below regardless of LR/TB so the gating
    // relationship reads consistently as "tasks support these integrations".
    const manualRowY = dagreBounds
      ? dagreBounds.maxY + MANUAL_TASK_ROW_GAP
      : 0;
    const manualRowX = dagreBounds ? dagreBounds.minX : 0;
    const manualTasksPlaced: AppNode[] = manualTaskNodes.map((n, idx) => ({
      ...n,
      position: {
        x: manualRowX + idx * MANUAL_TASK_H_SPACING,
        y: manualRowY,
      },
    }));

    // Isolated integration nodes: grid below dagre (or below manual-task row
    // when present) for TB; beside dagre for LR.
    let positionedIsolated: AppNode[] = [];
    if (isolatedNodes.length > 0) {
      const cols = Math.max(1, Math.ceil(Math.sqrt(isolatedNodes.length)));
      const gridLaidOut = isolatedNodes.map((n, idx) => ({
        ...n,
        position: {
          x: (idx % cols) * GRID_H_SPACING,
          y: Math.floor(idx / cols) * GRID_V_SPACING,
        },
      }));

      if (!dagreBounds) {
        positionedIsolated = gridLaidOut;
      } else {
        const manualRowBottom = manualTasksPlaced.length
          ? manualRowY + NODE_HEIGHT
          : dagreBounds.maxY;
        const offsetX =
          direction === "TB"
            ? dagreBounds.maxX + GRID_GAP_BELOW_DAGRE
            : dagreBounds.minX;
        const offsetY =
          direction === "TB"
            ? dagreBounds.minY
            : manualRowBottom + GRID_GAP_BELOW_DAGRE;
        positionedIsolated = gridLaidOut.map((n) => ({
          ...n,
          position: {
            x: n.position.x + offsetX,
            y: n.position.y + offsetY,
          },
        }));
      }
    }

    return {
      nodes: [
        ...identityPlaced,
        ...dagreNodes,
        ...manualTasksPlaced,
        ...positionedIsolated,
      ],
      edges,
    };
  }, [payload, direction]);

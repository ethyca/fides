import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { EDGE_TYPES, NODE_HEIGHT, NODE_TYPES, NODE_WIDTH } from "../constants";
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

    // Split nodes into "linked" (touching at least one edge) and "isolated"
    // (no edges — typically unreachable integrations). Linked nodes go through
    // dagre; isolated nodes get a grid layout positioned beside the dagre block.
    const linkedIds = new Set<string>();
    edges.forEach((e) => {
      linkedIds.add(e.source);
      linkedIds.add(e.target);
    });

    const linkedNodes: AppNode[] = [];
    const isolatedNodes: AppNode[] = [];
    nodes.forEach((n) => {
      if (linkedIds.has(n.id)) {
        linkedNodes.push(n);
      } else {
        isolatedNodes.push(n);
      }
    });

    const dagreOut = layoutTraversal(linkedNodes as Node[], edges, direction);
    const dagreNodes = dagreOut.nodes as AppNode[];

    if (isolatedNodes.length === 0) {
      return { nodes: dagreNodes, edges: dagreOut.edges };
    }

    // Lay out isolated nodes in a roughly-square grid.
    const cols = Math.max(1, Math.ceil(Math.sqrt(isolatedNodes.length)));
    const gridLaidOut: AppNode[] = isolatedNodes.map((n, idx) => ({
      ...n,
      position: {
        x: (idx % cols) * GRID_H_SPACING,
        y: Math.floor(idx / cols) * GRID_V_SPACING,
      },
    }));

    if (dagreNodes.length === 0) {
      return { nodes: gridLaidOut, edges: dagreOut.edges };
    }

    // Place the grid below the dagre layout (LR) or beside it (TB).
    const dagreBounds = dagreNodes.reduce(
      (acc, n) => ({
        minX: Math.min(acc.minX, n.position.x),
        maxX: Math.max(acc.maxX, n.position.x + NODE_WIDTH),
        minY: Math.min(acc.minY, n.position.y),
        maxY: Math.max(acc.maxY, n.position.y + NODE_HEIGHT),
      }),
      { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity },
    );

    const offsetX = direction === "TB" ? dagreBounds.maxX + GRID_GAP_BELOW_DAGRE : dagreBounds.minX;
    const offsetY = direction === "TB" ? dagreBounds.minY : dagreBounds.maxY + GRID_GAP_BELOW_DAGRE;

    const positionedGrid = gridLaidOut.map((n) => ({
      ...n,
      position: {
        x: n.position.x + offsetX,
        y: n.position.y + offsetY,
      },
    }));

    return {
      nodes: [...dagreNodes, ...positionedGrid],
      edges: dagreOut.edges,
    };
  }, [payload, direction]);

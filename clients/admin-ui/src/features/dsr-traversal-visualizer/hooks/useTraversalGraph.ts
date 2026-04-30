import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { EDGE_TYPES, NODE_TYPES } from "../constants";
import { LayoutDirection, layoutTraversal } from "../layout-utils";
import { TraversalPreviewResponse } from "../types";

export interface TraversalGraph {
  nodes: Node[];
  edges: Edge[];
}

const edgeId = (kind: string, source: string, target: string) =>
  `edge:${kind}:${source}__${target}`;

export const useTraversalGraph = (
  payload: TraversalPreviewResponse | undefined,
  direction: LayoutDirection,
): TraversalGraph =>
  useMemo(() => {
    if (!payload) {
      return { nodes: [], edges: [] };
    }
    const nodes: Node[] = [];

    nodes.push({
      id: payload.identity_root.id,
      type: NODE_TYPES.IDENTITY_ROOT,
      data: payload.identity_root,
      position: { x: 0, y: 0 },
    });
    payload.integrations.forEach((i) => {
      nodes.push({
        id: i.id,
        type: NODE_TYPES.INTEGRATION,
        data: i,
        position: { x: 0, y: 0 },
      });
    });
    payload.manual_tasks.forEach((m) => {
      nodes.push({
        id: m.id,
        type: NODE_TYPES.MANUAL_TASK,
        data: m,
        position: { x: 0, y: 0 },
      });
    });

    const edges: Edge[] = payload.edges.map((e) => ({
      id: edgeId(e.kind, e.source, e.target),
      source: e.source,
      target: e.target,
      type: e.kind === "gates" ? EDGE_TYPES.GATES : EDGE_TYPES.DEPENDENCY,
      data: { dep_count: e.dep_count, kind: e.kind },
    }));

    return layoutTraversal(nodes, edges, direction);
  }, [payload, direction]);

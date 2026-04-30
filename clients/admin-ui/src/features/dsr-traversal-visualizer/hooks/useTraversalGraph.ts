import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { EDGE_TYPES, NODE_TYPES } from "../constants";
import { LayoutDirection, layoutTraversal } from "../layout-utils";
import { AppNode, TraversalPreviewResponse } from "../types";

export interface TraversalGraph {
  nodes: AppNode[];
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

    const layouted = layoutTraversal(nodes as Node[], edges, direction);
    return { nodes: layouted.nodes as AppNode[], edges: layouted.edges };
  }, [payload, direction]);

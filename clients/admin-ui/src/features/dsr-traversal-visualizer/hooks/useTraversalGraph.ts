import { Edge } from "@xyflow/react";
import { useMemo } from "react";

import { EDGE_TYPES } from "../constants";
import { computeLaneLayout } from "../layout/compute-lane-layout";
import { computeStages } from "../layout/compute-stages";
import {
  AppNode,
  LaneBounds,
  LaneCollapseMap,
  PreviewEdge,
  Reachability,
  TraversalPreviewResponse,
} from "../types";

export interface TraversalGraph {
  nodes: AppNode[];
  edges: Edge[];
  lanes: LaneBounds[];
  canvas: { width: number; height: number };
}

const edgeId = (kind: string, source: string, target: string) =>
  `edge:${kind}:${encodeURIComponent(source)}>${encodeURIComponent(target)}`;

const collectPathEdgeIds = (
  payloadEdges: PreviewEdge[],
  rootId: string,
): Set<string> => {
  const incomingByTarget = new Map<string, PreviewEdge[]>();
  const outgoingBySource = new Map<string, PreviewEdge[]>();
  payloadEdges.forEach((e) => {
    incomingByTarget.set(e.target, [
      ...(incomingByTarget.get(e.target) ?? []),
      e,
    ]);
    outgoingBySource.set(e.source, [
      ...(outgoingBySource.get(e.source) ?? []),
      e,
    ]);
  });

  const result = new Set<string>();
  const walk = (
    seedId: string,
    edgesFor: (id: string) => PreviewEdge[],
    nextNodeId: (e: PreviewEdge) => string,
  ) => {
    const visited = new Set<string>([seedId]);
    const queue: string[] = [seedId];
    while (queue.length) {
      const id = queue.shift()!;
      edgesFor(id).forEach((e) => {
        result.add(edgeId(e.kind, e.source, e.target));
        const next = nextNodeId(e);
        if (!visited.has(next)) {
          visited.add(next);
          queue.push(next);
        }
      });
    }
  };
  walk(
    rootId,
    (id) => incomingByTarget.get(id) ?? [],
    (e) => e.source,
  );
  walk(
    rootId,
    (id) => outgoingBySource.get(id) ?? [],
    (e) => e.target,
  );
  return result;
};

export const useTraversalGraph = (
  payload: TraversalPreviewResponse | undefined,
  collapse: LaneCollapseMap,
  selectedNodeId: string | null = null,
): TraversalGraph =>
  useMemo(() => {
    if (!payload) {
      return {
        nodes: [],
        edges: [],
        lanes: [],
        canvas: { width: 0, height: 0 },
      };
    }

    const { positions, lanes, canvas } = computeLaneLayout(payload, collapse);

    // Stage-2+ subtitles: immediate upstream system name from dep edges.
    const reachIds = payload.integrations
      .filter((i) => i.reachability !== Reachability.UNREACHABLE)
      .map((i) => i.id);
    const stageMap = computeStages(reachIds, payload.edges);
    const upstreamByTarget = new Map<string, string>();
    payload.edges.forEach((e) => {
      if (e.kind !== "depends_on" || e.source === "identity-root") {
        return;
      }
      if (!upstreamByTarget.has(e.target)) {
        const src = payload.integrations.find((i) => i.id === e.source);
        if (src) {
          upstreamByTarget.set(
            e.target,
            src.system?.name ?? src.connection_key,
          );
        }
      }
    });

    const animatedEdgeIds = selectedNodeId
      ? collectPathEdgeIds(payload.edges, selectedNodeId)
      : null;

    const integrationNodes = payload.integrations.map<AppNode>((i) => {
      const stage = stageMap[i.id] ?? 1;
      const stageVia = stage >= 2 ? (upstreamByTarget.get(i.id) ?? null) : null;
      const pos = positions[i.id];
      return {
        id: i.id,
        type: "integration",
        data: { ...i, stage_via: stageVia },
        position: pos ?? { x: 0, y: 0 },
        hidden: !pos,
      };
    });

    const identityNode: AppNode | null = positions[payload.identity_root.id]
      ? {
          id: payload.identity_root.id,
          type: "identityRoot",
          data: payload.identity_root,
          position: positions[payload.identity_root.id]!,
        }
      : null;

    const manualTaskNodes = payload.manual_tasks.map<AppNode>((m) => ({
      id: m.id,
      type: "manualTask",
      data: m,
      position: positions[m.id] ?? { x: 0, y: 0 },
      hidden: !positions[m.id],
    }));

    const nodes: AppNode[] = [
      ...(identityNode ? [identityNode] : []),
      ...integrationNodes,
      ...manualTaskNodes,
    ];

    const edges: Edge[] = payload.edges.map((e) => {
      const id = edgeId(e.kind, e.source, e.target);
      return {
        id,
        source: e.source,
        target: e.target,
        type: e.kind === "gates" ? EDGE_TYPES.GATES : EDGE_TYPES.DEPENDENCY,
        animated: animatedEdgeIds ? animatedEdgeIds.has(id) : false,
        data: { dep_count: e.dep_count, kind: e.kind },
      };
    });

    return { nodes, edges, lanes, canvas };
  }, [payload, collapse, selectedNodeId]);

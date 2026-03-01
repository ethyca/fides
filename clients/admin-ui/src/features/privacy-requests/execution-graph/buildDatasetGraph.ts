import { Edge, Node } from "@xyflow/react";
import dagre from "dagre";

import {
  DatasetGraphNodeData,
  ExecutionGraphNode,
  ExecutionGraphNodeStatus,
} from "../types";
import {
  DATASET_NODE_HEIGHT,
  DATASET_NODE_WIDTH,
  STATUS_PRIORITY,
  isInternalNode,
} from "./execution-graph.constants";

export type DatasetGraphNodeType = Node<DatasetGraphNodeData, "datasetNode">;

function getAggregateStatus(
  statuses: ExecutionGraphNodeStatus[],
): ExecutionGraphNodeStatus {
  if (statuses.length === 0) {
    return "pending";
  }
  let worst: ExecutionGraphNodeStatus = statuses[0];
  for (const s of statuses) {
    if (STATUS_PRIORITY[s] > STATUS_PRIORITY[worst]) {
      worst = s;
    }
  }
  return worst;
}

function getDatasetFromAddress(collectionAddress: string): string {
  const idx = collectionAddress.indexOf(":");
  if (idx === -1) {
    return collectionAddress;
  }
  return collectionAddress.slice(0, idx);
}

export function buildDatasetGraph(graphNodes: ExecutionGraphNode[]): {
  nodes: DatasetGraphNodeType[];
  edges: Edge[];
} {
  const visibleNodes = graphNodes.filter(
    (n) => !isInternalNode(n.collection_address),
  );

  const groups = new Map<
    string,
    {
      statuses: ExecutionGraphNodeStatus[];
      completedCount: number;
      errorCount: number;
      executingCount: number;
    }
  >();

  for (const node of visibleNodes) {
    const ds = node.dataset_name;
    if (!groups.has(ds)) {
      groups.set(ds, {
        statuses: [],
        completedCount: 0,
        errorCount: 0,
        executingCount: 0,
      });
    }
    const group = groups.get(ds)!;
    group.statuses.push(node.status);
    if (node.status === "complete") {
      group.completedCount += 1;
    }
    if (node.status === "error") {
      group.errorCount += 1;
    }
    if (node.status === "executing") {
      group.executingCount += 1;
    }
  }

  const datasetNodes: DatasetGraphNodeType[] = [];
  for (const [dsName, group] of groups) {
    datasetNodes.push({
      id: dsName,
      position: { x: 0, y: 0 },
      type: "datasetNode" as const,
      data: {
        datasetName: dsName,
        status: getAggregateStatus(group.statuses),
        totalCollections: group.statuses.length,
        completedCollections: group.completedCount,
        errorCount: group.errorCount,
        executingCount: group.executingCount,
      },
    });
  }

  const edgeSet = new Set<string>();
  const edges: Edge[] = [];
  const datasetNameSet = new Set(groups.keys());

  for (const node of visibleNodes) {
    const srcDs = node.dataset_name;
    for (const downstream of node.downstream_tasks) {
      if (isInternalNode(downstream)) {
        continue;
      }
      const tgtDs = getDatasetFromAddress(downstream);
      if (tgtDs !== srcDs && datasetNameSet.has(tgtDs)) {
        const edgeId = `${srcDs}->${tgtDs}`;
        if (!edgeSet.has(edgeId)) {
          edgeSet.add(edgeId);
          edges.push({
            id: edgeId,
            source: srcDs,
            target: tgtDs,
            animated: node.status === "executing",
          });
        }
      }
    }
  }

  return layoutDatasetGraph(datasetNodes, edges);
}

function layoutDatasetGraph(
  nodes: DatasetGraphNodeType[],
  edges: Edge[],
): { nodes: DatasetGraphNodeType[]; edges: Edge[] } {
  if (nodes.length === 0) {
    return { nodes, edges };
  }

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: "LR",
    ranksep: 100,
    nodesep: 40,
    edgesep: 20,
    marginx: 20,
    marginy: 20,
  });

  for (const node of nodes) {
    g.setNode(node.id, {
      width: DATASET_NODE_WIDTH,
      height: DATASET_NODE_HEIGHT,
    });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - DATASET_NODE_WIDTH / 2,
        y: pos.y - DATASET_NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

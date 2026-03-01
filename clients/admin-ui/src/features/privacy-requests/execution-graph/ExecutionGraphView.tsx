import {
  Background,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlow,
  useReactFlow,
} from "@xyflow/react";
import dagre from "dagre";
import { useCallback, useEffect, useMemo, useRef } from "react";

import "@xyflow/react/dist/style.css";

import { ExecutionGraphNode } from "../types";
import { buildDatasetGraph } from "./buildDatasetGraph";
import DatasetGraphNodeComponent from "./DatasetGraphNode";
import ExecutionGraphNodeComponent, {
  ExecutionGraphNodeType,
} from "./ExecutionGraphNode";
import {
  isInternalNode,
  isRootNode,
  isTerminatorNode,
} from "./execution-graph.constants";
import { GraphViewMode } from "./useExecutionGraphNavigation";

const NODE_WIDTH = 220;
const NODE_HEIGHT = 80;
const ROOT_NODE_WIDTH = NODE_WIDTH;
const ROOT_NODE_HEIGHT = NODE_HEIGHT;

const GHOST_OPACITY = 0.4;

interface ExecutionGraphViewProps {
  graphNodes: ExecutionGraphNode[];
  viewMode: GraphViewMode;
  selectedDataset: string | null;
  onDatasetClick: (datasetName: string) => void;
  focusNodeId: string | null;
}

function FocusHandler({
  nodeId,
  initialNodeId,
}: {
  nodeId: string | null;
  initialNodeId: string | null;
}) {
  const { setCenter, getNode, getZoom } = useReactFlow();
  const hasFocusedInitial = useRef(false);

  useEffect(() => {
    hasFocusedInitial.current = false;
  }, [initialNodeId]);

  useEffect(() => {
    const targetId = nodeId ?? (hasFocusedInitial.current ? null : initialNodeId);
    if (!targetId) {
      return;
    }
    const timer = setTimeout(() => {
      const node = getNode(targetId);
      if (node) {
        hasFocusedInitial.current = true;
        setCenter(
          node.position.x + (node.measured?.width ?? NODE_WIDTH) / 2,
          node.position.y + (node.measured?.height ?? NODE_HEIGHT) / 2,
          { zoom: getZoom(), duration: 400 },
        );
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [nodeId, initialNodeId, setCenter, getNode]);

  return null;
}

function buildLayout(
  nodes: Node[],
  edges: Edge[],
): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: "LR",
    ranksep: 80,
    nodesep: 30,
    edgesep: 20,
    marginx: 20,
    marginy: 20,
  });

  nodes.forEach((node) => {
    const isRoot = isRootNode(node.id);
    g.setNode(node.id, {
      width: isRoot ? ROOT_NODE_WIDTH : NODE_WIDTH,
      height: isRoot ? ROOT_NODE_HEIGHT : NODE_HEIGHT,
    });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - pos.width / 2,
        y: pos.y - pos.height / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

export function buildGraph(graphNodes: ExecutionGraphNode[]): {
  nodes: ExecutionGraphNodeType[];
  edges: Edge[];
} {
  const visibleNodes = graphNodes.filter(
    (n) => !isTerminatorNode(n.collection_address),
  );

  const addressSet = new Set(visibleNodes.map((n) => n.collection_address));

  const nodes: ExecutionGraphNodeType[] = visibleNodes.map((gn) => ({
    id: gn.collection_address,
    position: { x: 0, y: 0 },
    type: "executionGraphNode" as const,
    data: { graphNode: gn },
  }));

  const edges: Edge[] = [];
  const edgeSet = new Set<string>();

  visibleNodes.forEach((gn) => {
    gn.downstream_tasks.forEach((downstream) => {
      if (
        addressSet.has(downstream) &&
        !isTerminatorNode(downstream)
      ) {
        const edgeId = `${gn.collection_address}->${downstream}`;
        if (!edgeSet.has(edgeId)) {
          edgeSet.add(edgeId);
          edges.push({
            id: edgeId,
            source: gn.collection_address,
            target: downstream,
            animated: gn.status === "executing",
          });
        }
      }
    });
  });

  return { nodes, edges };
}

function buildCollectionGraph(
  graphNodes: ExecutionGraphNode[],
  selectedDataset: string,
): {
  nodes: ExecutionGraphNodeType[];
  edges: Edge[];
} {
  const allVisible = graphNodes.filter(
    (n) => !isTerminatorNode(n.collection_address),
  );

  const primaryNodes = allVisible.filter(
    (n) => n.dataset_name === selectedDataset,
  );

  const primaryAddresses = new Set(primaryNodes.map((n) => n.collection_address));
  const allAddressMap = new Map(allVisible.map((n) => [n.collection_address, n]));

  const ghostAddresses = new Set<string>();
  for (const node of primaryNodes) {
    for (const up of node.upstream_tasks) {
      if (!primaryAddresses.has(up) && allAddressMap.has(up) && !isInternalNode(up)) {
        ghostAddresses.add(up);
      }
    }
    for (const down of node.downstream_tasks) {
      if (
        !primaryAddresses.has(down) &&
        allAddressMap.has(down) &&
        !isInternalNode(down)
      ) {
        ghostAddresses.add(down);
      }
    }
  }

  const includedAddresses = new Set([...primaryAddresses, ...ghostAddresses]);

  const nodes: ExecutionGraphNodeType[] = [];
  for (const addr of includedAddresses) {
    const gn = allAddressMap.get(addr);
    if (!gn) {
      continue;
    }
    nodes.push({
      id: gn.collection_address,
      position: { x: 0, y: 0 },
      type: "executionGraphNode" as const,
      data: { graphNode: gn },
      style: ghostAddresses.has(addr) ? { opacity: GHOST_OPACITY } : undefined,
    });
  }

  const edges: Edge[] = [];
  const edgeSet = new Set<string>();
  for (const addr of includedAddresses) {
    const gn = allAddressMap.get(addr);
    if (!gn) {
      continue;
    }
    for (const downstream of gn.downstream_tasks) {
      if (includedAddresses.has(downstream) && !isTerminatorNode(downstream)) {
        const edgeId = `${addr}->${downstream}`;
        if (!edgeSet.has(edgeId)) {
          edgeSet.add(edgeId);
          const isGhostEdge = ghostAddresses.has(addr) || ghostAddresses.has(downstream);
          edges.push({
            id: edgeId,
            source: addr,
            target: downstream,
            animated: gn.status === "executing",
            style: isGhostEdge ? { opacity: GHOST_OPACITY } : undefined,
          });
        }
      }
    }
  }

  return { nodes, edges };
}

const ExecutionGraphView = ({
  graphNodes,
  viewMode,
  selectedDataset,
  onDatasetClick,
  focusNodeId,
}: ExecutionGraphViewProps) => {
  const handleDatasetClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type === "datasetNode") {
        onDatasetClick(node.id);
      }
    },
    [onDatasetClick],
  );

  const nodeTypes = useMemo(
    () => ({
      executionGraphNode: ExecutionGraphNodeComponent,
      datasetNode: DatasetGraphNodeComponent,
    }),
    [],
  );

  const { nodes, edges } = useMemo(() => {
    if (viewMode === "datasets") {
      return buildDatasetGraph(graphNodes);
    }

    if (selectedDataset) {
      const graph = buildCollectionGraph(graphNodes, selectedDataset);
      if (graph.nodes.length === 0) {
        return graph;
      }
      return buildLayout(graph.nodes, graph.edges);
    }

    const graph = buildGraph(graphNodes);
    if (graph.nodes.length === 0) {
      return graph;
    }
    return buildLayout(graph.nodes, graph.edges);
  }, [graphNodes, viewMode, selectedDataset]);

  const leftmostNodeId = useMemo(() => {
    if (nodes.length === 0) {
      return null;
    }
    let leftmost = nodes[0];
    for (const n of nodes) {
      if (n.position.x < leftmost.position.x) {
        leftmost = n;
      }
    }
    return leftmost.id;
  }, [nodes]);

  if (nodes.length === 0) {
    return null;
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView={!leftmostNodeId}
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={false}
      nodesConnectable={false}
      edgesFocusable={false}
      onNodeClick={viewMode === "datasets" ? handleDatasetClick : undefined}
      onlyRenderVisibleElements
      proOptions={{ hideAttribution: true }}
    >
      <Background />
      <Controls showInteractive={false} />
      <MiniMap zoomable pannable />
      <FocusHandler nodeId={focusNodeId} initialNodeId={leftmostNodeId} />
    </ReactFlow>
  );
};

export default ExecutionGraphView;

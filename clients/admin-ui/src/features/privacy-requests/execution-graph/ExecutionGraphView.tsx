import {
  Background,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlow,
} from "@xyflow/react";
import dagre from "dagre";
import { useMemo } from "react";

import "@xyflow/react/dist/style.css";

import { ExecutionGraphNode } from "../types";
import ExecutionGraphNodeComponent, {
  ExecutionGraphNodeType,
} from "./ExecutionGraphNode";
import { isRootNode, isTerminatorNode } from "./execution-graph.constants";

const NODE_WIDTH = 220;
const NODE_HEIGHT = 80;
const ROOT_NODE_WIDTH = NODE_WIDTH;
const ROOT_NODE_HEIGHT = NODE_HEIGHT;

const nodeTypes = {
  executionGraphNode: ExecutionGraphNodeComponent,
};

interface ExecutionGraphViewProps {
  graphNodes: ExecutionGraphNode[];
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

const ExecutionGraphView = ({ graphNodes }: ExecutionGraphViewProps) => {
  const { nodes, edges } = useMemo(() => {
    const graph = buildGraph(graphNodes);
    if (graph.nodes.length === 0) {
      return graph;
    }
    return buildLayout(graph.nodes, graph.edges);
  }, [graphNodes]);

  if (nodes.length === 0) {
    return null;
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={false}
      nodesConnectable={false}
      edgesFocusable={false}
      proOptions={{ hideAttribution: true }}
    >
      <Background />
      <Controls showInteractive={false} />
      <MiniMap zoomable pannable />
    </ReactFlow>
  );
};

export default ExecutionGraphView;

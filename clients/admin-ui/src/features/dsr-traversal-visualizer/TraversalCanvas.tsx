import "@xyflow/react/dist/style.css";

import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  useReactFlow,
} from "@xyflow/react";
import { useEffect } from "react";

import DependencyEdge from "./edges/DependencyEdge";
import GatesEdge from "./edges/GatesEdge";
import { useNodeSelection } from "./hooks/useNodeSelection";
import { useTraversalGraph } from "./hooks/useTraversalGraph";
import { LayoutDirection } from "./layout-utils";
import IdentityRootNode from "./nodes/IdentityRootNode";
import IntegrationNode from "./nodes/IntegrationNode";
import ManualTaskNode from "./nodes/ManualTaskNode";
import IntegrationDetailPanel from "./panels/IntegrationDetailPanel";
import LegendPanel from "./panels/LegendPanel";
import ManualTaskDetailPanel from "./panels/ManualTaskDetailPanel";
import { TraversalPreviewResponse } from "./types";

const NODE_TYPES = {
  identityRoot: IdentityRootNode,
  integration: IntegrationNode,
  manualTask: ManualTaskNode,
};

const EDGE_TYPES = {
  dependency: DependencyEdge,
  gates: GatesEdge,
};

const DEFAULT_EDGE_OPTIONS = {
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 14,
    height: 14,
  },
};

// Refit the viewport whenever the visible node set or layout direction
// changes (e.g. toggling "show unreachable", switching access/erasure, or
// flipping LR/TB). The short timeout gives React Flow's ResizeObserver a
// chance to measure any newly-mounted cards before fitView reads their
// bounds -- without it, the first fit underestimates the layout extent and
// crops content on the right.
const FIT_VIEW_DELAY_MS = 120;

const FitViewOnLayoutChange = ({
  trigger,
}: {
  trigger: string | number;
}) => {
  const { fitView } = useReactFlow();
  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: 0.2, duration: 250 });
    }, FIT_VIEW_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [trigger, fitView]);
  return null;
};

interface Props {
  payload: TraversalPreviewResponse | undefined;
  direction: LayoutDirection;
}

const TraversalCanvas = ({ payload, direction }: Props) => {
  const { selected, onNodeClick, clear } = useNodeSelection();
  const { nodes, edges } = useTraversalGraph(
    payload,
    direction,
    selected?.id ?? null,
  );

  const integrationData =
    selected?.type === "integration" ? selected.data : null;
  const manualData = selected?.type === "manualTask" ? selected.data : null;

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "calc(100vh - 200px)",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        defaultEdgeOptions={DEFAULT_EDGE_OPTIONS}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap pannable zoomable />
        <FitViewOnLayoutChange trigger={`${direction}:${nodes.length}`} />
      </ReactFlow>
      <LegendPanel />
      <IntegrationDetailPanel
        data={integrationData}
        edges={payload?.edges ?? []}
        integrations={payload?.integrations ?? []}
        onClose={clear}
      />
      <ManualTaskDetailPanel data={manualData} onClose={clear} />
    </div>
  );
};

export default TraversalCanvas;

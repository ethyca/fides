import "@xyflow/react/dist/style.css";

import { Background, Controls, MiniMap, ReactFlow } from "@xyflow/react";

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

interface Props {
  payload: TraversalPreviewResponse | undefined;
  direction: LayoutDirection;
}

const TraversalCanvas = ({ payload, direction }: Props) => {
  const { nodes, edges } = useTraversalGraph(payload, direction);
  const { selected, onNodeClick, clear } = useNodeSelection();

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
        onNodeClick={onNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap pannable zoomable />
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

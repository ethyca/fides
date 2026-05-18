import "@xyflow/react/dist/style.css";

import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  useReactFlow,
} from "@xyflow/react";
import { Flex, Spin } from "fidesui";
import { useEffect } from "react";

import { DependencyEdge } from "./edges/DependencyEdge";
import { GatesEdge } from "./edges/GatesEdge";
import { useLaneCollapseState } from "./hooks/useLaneCollapseState";
import { useNodeSelection } from "./hooks/useNodeSelection";
import { useTraversalGraph } from "./hooks/useTraversalGraph";
import { LaneChrome } from "./LaneChrome";
import { IdentityRootNode } from "./nodes/IdentityRootNode";
import { IntegrationNode } from "./nodes/IntegrationNode";
import { ManualTaskNode } from "./nodes/ManualTaskNode";
import { IntegrationDetailPanel } from "./panels/IntegrationDetailPanel";
import { LegendPanel } from "./panels/LegendPanel";
import { ManualTaskDetailPanel } from "./panels/ManualTaskDetailPanel";
import { LaneId, Reachability, TraversalPreviewResponse } from "./types";

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
  markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
};

const FIT_VIEW_DELAY_MS = 120;

const FitViewOnLayoutChange = ({ trigger }: { trigger: string | number }) => {
  const { fitView } = useReactFlow();
  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: 0.15, duration: 250 });
    }, FIT_VIEW_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [trigger, fitView]);
  return null;
};

interface Props {
  payload: TraversalPreviewResponse | undefined;
}

export const TraversalCanvas = ({ payload }: Props) => {
  const { collapse, toggle, expand, hydrated } = useLaneCollapseState();
  const { selected, onNodeClick, clear } = useNodeSelection();
  const { nodes, edges, lanes } = useTraversalGraph(
    payload,
    collapse,
    selected?.id ?? null,
  );

  // Auto-expand a collapsed lane when the selected chain reaches a node in it.
  // The chain is exactly the set of edges flagged `animated` by useTraversalGraph.
  useEffect(() => {
    if (!selected) {
      return;
    }
    const chainNodeIds = new Set<string>();
    chainNodeIds.add(selected.id);
    edges.forEach((e) => {
      if (e.animated) {
        chainNodeIds.add(e.source);
        chainNodeIds.add(e.target);
      }
    });
    const idToLane = new Map<string, LaneId>();
    if (payload?.identity_root.id) {
      idToLane.set(payload.identity_root.id, LaneId.IDENTITY);
    }
    payload?.integrations.forEach((i) => {
      idToLane.set(
        i.id,
        i.reachability === Reachability.UNREACHABLE
          ? LaneId.SKIPPED
          : LaneId.REACH,
      );
    });
    payload?.manual_tasks.forEach((m) => idToLane.set(m.id, LaneId.GATED));

    const lanesToExpand = new Set<(typeof lanes)[number]["id"]>();
    chainNodeIds.forEach((id) => {
      const laneId = idToLane.get(id);
      if (laneId) {
        lanesToExpand.add(laneId);
      }
    });
    lanesToExpand.forEach((laneId) => {
      const lane = lanes.find((l) => l.id === laneId);
      if (lane?.collapsed) {
        expand(laneId);
      }
    });
  }, [selected, edges, lanes, payload, expand]);

  const integrationData =
    selected?.type === "integration" ? selected.data : null;
  const manualData = selected?.type === "manualTask" ? selected.data : null;

  // Wait for the lane-collapse hook to read localStorage before rendering
  // ReactFlow. Mounting the canvas with default state and then re-laying
  // out once the persisted state arrives causes a visible "snap" as the
  // FitViewOnLayoutChange animation fires on first paint.
  if (!hydrated) {
    return (
      <Flex align="center" justify="center" flex={1}>
        <Spin />
      </Flex>
    );
  }

  return (
    <div className="relative min-h-0 w-full flex-1">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        defaultEdgeOptions={DEFAULT_EDGE_OPTIONS}
        onNodeClick={onNodeClick}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <LaneChrome lanes={lanes} onToggleCollapse={toggle} />
        <Background style={{ opacity: 0 }} />
        <Controls showInteractive={false} />
        <FitViewOnLayoutChange
          trigger={`${nodes.length}:${JSON.stringify(collapse)}`}
        />
      </ReactFlow>
      <LegendPanel />
      <IntegrationDetailPanel
        data={integrationData}
        edges={payload?.edges ?? []}
        integrations={payload?.integrations ?? []}
        manualTasks={payload?.manual_tasks ?? []}
        onClose={clear}
      />
      <ManualTaskDetailPanel
        data={manualData}
        integrations={payload?.integrations ?? []}
        onClose={clear}
      />
    </div>
  );
};

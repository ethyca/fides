import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  Handle,
  type Node,
  type NodeProps,
  type NodeTypes,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import { Flex, Icons } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import { getLayoutedElements } from "~/features/datamap/layout-utils";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift } from "./purposeUtils";

// ─── Dimensions ───────────────────────────────────────────────────────────────
const PURPOSE_W = 220;
const PURPOSE_H = 64;
const SYSTEM_W = 190;
const SYSTEM_H = 32;
const CATEGORY_W = 210;
const CATEGORY_H = 28;

const EDGE_COLOR = palette.FIDESUI_SANDSTONE; // matches taxonomy edge default

const RISK_ORDER: Record<string, number> = {
  drift: 0,
  compliant: 1,
  unknown: 2,
};

// ─── Purpose node ─────────────────────────────────────────────────────────────

type PurposeNodeData = {
  label: string;
  dataUse: string;
  riskStatus: "drift" | "compliant" | "unknown";
  expanded: boolean;
};

const RISK_ACCENT_COLOR: Record<PurposeNodeData["riskStatus"], string> = {
  drift: palette.FIDESUI_ERROR,
  compliant: palette.FIDESUI_SUCCESS,
  unknown: palette.FIDESUI_NEUTRAL_200,
};

const PurposeNode = ({ data }: NodeProps) => {
  const d = data as PurposeNodeData;
  const accent = RISK_ACCENT_COLOR[d.riskStatus];

  return (
    <div
      style={{
        width: PURPOSE_W,
        height: PURPOSE_H,
        background: d.expanded ? "#f0f4ff" : palette.FIDESUI_BG_CORINTH,
        border: `1px solid ${d.expanded ? "#c7d2fe" : palette.FIDESUI_NEUTRAL_200}`,
        borderLeft: `3px solid ${accent}`,
        borderRadius: 8,
        padding: "8px 12px 8px 14px",
        boxSizing: "border-box",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 3,
        position: "relative",
      }}
    >
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />

      {d.riskStatus === "drift" && (
        <span
          style={{
            position: "absolute",
            top: 6,
            right: 8,
            color: palette.FIDESUI_ERROR,
            lineHeight: 0,
          }}
        >
          <Icons.WarningAltFilled size={13} />
        </span>
      )}

      <Flex align="center" gap={5}>
        <span
          style={{
            color: palette.FIDESUI_NEUTRAL_400,
            lineHeight: 0,
            flexShrink: 0,
          }}
        >
          <Icons.RuleDraft size={13} />
        </span>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: palette.FIDESUI_MINOS,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            paddingRight: d.riskStatus === "drift" ? 20 : 0,
          }}
        >
          {d.label}
        </div>
      </Flex>

      <div
        style={{
          fontSize: 11,
          color: palette.FIDESUI_NEUTRAL_400,
          paddingLeft: 18,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {d.dataUse.replace(/_/g, " ")}
      </div>
    </div>
  );
};

// ─── Shared taxonomy-style dot handle ────────────────────────────────────────
// Matches TaxonomyTreeNodeHandle exactly: 8×8, MINOS color, color transition

const TaxonomyDot = ({ isSource }: { isSource?: boolean }) => (
  <Handle
    type={isSource ? "source" : "target"}
    position={isSource ? Position.Right : Position.Left}
    style={{
      width: 8,
      height: 8,
      backgroundColor: palette.FIDESUI_MINOS,
    }}
    className="transition-colors duration-300 ease-in"
  />
);

// ─── System node (text style) ─────────────────────────────────────────────────

type SystemNodeData = {
  label: string;
  systemType: string;
  hasRisk: boolean;
  expanded: boolean;
};

const SystemNode = ({ data }: NodeProps) => {
  const d = data as SystemNodeData;

  return (
    <div
      style={{
        width: SYSTEM_W,
        height: SYSTEM_H,
        display: "flex",
        alignItems: "center",
        gap: 7,
        cursor: "pointer",
        paddingLeft: 16,
        paddingRight: 10,
        boxSizing: "border-box",
        ...(d.expanded && {
          background: "#fff",
          border: `1px solid ${palette.FIDESUI_NEUTRAL_200}`,
          borderRadius: 6,
        }),
      }}
    >
      <TaxonomyDot />
      {/* Source dot only shown when expanded (categories are connected) */}
      {d.expanded && <TaxonomyDot isSource />}

      <span
        style={{
          color: palette.FIDESUI_NEUTRAL_400,
          lineHeight: 0,
          flexShrink: 0,
        }}
      >
        <Icons.Layers size={13} />
      </span>
      <div
        style={{
          fontSize: 13,
          fontWeight: 500,
          color: palette.FIDESUI_MINOS,
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {d.label}
      </div>
      {d.hasRisk && (
        <span
          style={{ color: palette.FIDESUI_ERROR, lineHeight: 0, flexShrink: 0 }}
        >
          <Icons.WarningAltFilled size={11} />
        </span>
      )}
    </div>
  );
};

// ─── Category node (text style) ───────────────────────────────────────────────

type CategoryNodeData = {
  label: string;
  isUndeclared: boolean;
};

const CategoryNode = ({ data }: NodeProps) => {
  const d = data as CategoryNodeData;

  return (
    <div
      style={{
        width: CATEGORY_W,
        height: CATEGORY_H,
        display: "flex",
        alignItems: "center",
        gap: 7,
        cursor: "default",
        paddingLeft: 16,
        paddingRight: 8,
        boxSizing: "border-box",
      }}
    >
      <TaxonomyDot />

      <span
        style={{
          color: palette.FIDESUI_NEUTRAL_400,
          lineHeight: 0,
          flexShrink: 0,
        }}
      >
        <Icons.Tag size={11} />
      </span>
      <div
        style={{
          fontSize: 12,
          color: palette.FIDESUI_MINOS,
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {d.label}
      </div>
      {d.isUndeclared && (
        <span
          style={{ color: palette.FIDESUI_ERROR, lineHeight: 0, flexShrink: 0 }}
        >
          <Icons.WarningAltFilled size={11} />
        </span>
      )}
    </div>
  );
};

const nodeTypes: NodeTypes = {
  purposeNode: PurposeNode,
  systemNode: SystemNode,
  categoryNode: CategoryNode,
};

// ─── Inner graph ──────────────────────────────────────────────────────────────

interface NetworkGraphProps {
  purposes: DataPurpose[];
  summariesByKey: Map<string, PurposeSummary>;
}

const NetworkGraph = ({ purposes, summariesByKey }: NetworkGraphProps) => {
  const [expandedPurposeId, setExpandedPurposeId] = useState<string | null>(
    null,
  );
  const [expandedSystemId, setExpandedSystemId] = useState<string | null>(null);
  const router = useRouter();
  const { fitView } = useReactFlow();

  // Sort: risks first, then compliant, then unscanned
  const sortedPurposes = useMemo(
    () =>
      [...purposes].sort((a, b) => {
        const aDetected =
          summariesByKey.get(a.fides_key)?.detected_data_categories ?? [];
        const bDetected =
          summariesByKey.get(b.fides_key)?.detected_data_categories ?? [];
        const aS = computeCategoryDrift(
          a.data_categories ?? [],
          aDetected,
        ).status;
        const bS = computeCategoryDrift(
          b.data_categories ?? [],
          bDetected,
        ).status;
        return (RISK_ORDER[aS] ?? 2) - (RISK_ORDER[bS] ?? 2);
      }),
    [purposes, summariesByKey],
  );

  const { rawNodes, rawEdges, nodeSizes } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const sizes: Record<string, { width: number; height: number }> = {};

    // ── Purpose nodes ─────────────────────────────────────────────────────────
    sortedPurposes.forEach((p) => {
      const detected =
        summariesByKey.get(p.fides_key)?.detected_data_categories ?? [];
      const drift = computeCategoryDrift(p.data_categories ?? [], detected);
      nodes.push({
        id: p.fides_key,
        type: "purposeNode",
        position: { x: 0, y: 0 },
        data: {
          label: p.name,
          dataUse: p.data_use,
          riskStatus: drift.status,
          expanded: expandedPurposeId === p.fides_key,
        },
      });
      sizes[p.fides_key] = { width: PURPOSE_W, height: PURPOSE_H };
    });

    // ── System nodes for the expanded purpose ─────────────────────────────────
    if (expandedPurposeId) {
      const purpose = sortedPurposes.find(
        (p) => p.fides_key === expandedPurposeId,
      );
      const summary = summariesByKey.get(expandedPurposeId);
      if (purpose && summary) {
        const assignments = summary.systems.filter((a) => a.assigned);
        const definedSet = new Set(purpose.data_categories ?? []);
        const { datasets } = summary;

        assignments.forEach((a) => {
          const systemDatasets = datasets.filter(
            (d) => d.system_name === a.system_name,
          );
          const hasRisk = systemDatasets.some((d) =>
            d.data_categories.some((c) => !definedSet.has(c)),
          );
          nodes.push({
            id: a.system_id,
            type: "systemNode",
            position: { x: 0, y: 0 },
            data: {
              label: a.system_name,
              systemType: a.system_type,
              hasRisk,
              expanded: expandedSystemId === a.system_id,
            },
          });
          sizes[a.system_id] = { width: SYSTEM_W, height: SYSTEM_H };

          edges.push({
            id: `${expandedPurposeId}--${a.system_id}`,
            source: expandedPurposeId,
            target: a.system_id,
            style: { stroke: EDGE_COLOR, strokeWidth: 1 },
          });

          // ── Category nodes for the expanded system ─────────────────────────
          if (expandedSystemId === a.system_id) {
            const categoryMap = new Map<string, boolean>(); // category → isUndeclared
            systemDatasets.forEach((d) => {
              d.data_categories.forEach((c) => {
                categoryMap.set(c, !definedSet.has(c));
              });
            });

            categoryMap.forEach((isUndeclared, category) => {
              const catId = `cat-${a.system_id}-${category}`;

              nodes.push({
                id: catId,
                type: "categoryNode",
                position: { x: 0, y: 0 },
                data: { label: category, isUndeclared },
              });
              sizes[catId] = { width: CATEGORY_W, height: CATEGORY_H };

              edges.push({
                id: `${a.system_id}--${catId}`,
                source: a.system_id,
                target: catId,
                style: { stroke: EDGE_COLOR, strokeWidth: 1 },
              });
            });
          }
        });
      }
    }

    return { rawNodes: nodes, rawEdges: edges, nodeSizes: sizes };
  }, [sortedPurposes, summariesByKey, expandedPurposeId, expandedSystemId]);

  const { nodes, edges } = useMemo(
    () =>
      getLayoutedElements(rawNodes, rawEdges, "LR", {
        ranksep: 90,
        nodesep: 16,
        nodeSizes,
        topAlign: true,
      }),
    [rawNodes, rawEdges, nodeSizes],
  );

  useEffect(() => {
    const t = setTimeout(() => fitView({ padding: 0.14, duration: 300 }), 50);
    return () => clearTimeout(t);
  }, [expandedPurposeId, expandedSystemId, fitView]);

  const onNodeClick = useCallback(
    (e: React.MouseEvent, node: Node) => {
      if (node.type === "purposeNode") {
        if (e.detail === 2) {
          router.push(`${DATA_PURPOSES_ROUTE}/${node.id}`);
          return;
        }
        setExpandedPurposeId((prev) => {
          if (prev === node.id) {
            setExpandedSystemId(null);
            return null;
          }
          setExpandedSystemId(null);
          return node.id;
        });
      } else if (node.type === "systemNode") {
        setExpandedSystemId((prev) => (prev === node.id ? null : node.id));
      }
    },
    [router],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      fitView
      minZoom={0.2}
      maxZoom={2}
      nodesFocusable={false}
      nodesConnectable={false}
      edgesFocusable={false}
      elementsSelectable={false}
      proOptions={{ hideAttribution: true }}
    >
      <Background
        color={palette.FIDESUI_NEUTRAL_100}
        variant={BackgroundVariant.Dots}
        size={3}
      />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
};

// ─── Exported wrapper ─────────────────────────────────────────────────────────

interface PurposeNetworkViewProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
}

const PurposeNetworkView = ({
  purposes,
  summaries,
}: PurposeNetworkViewProps) => {
  const summariesByKey = useMemo(
    () => new Map(summaries.map((s) => [s.fides_key, s])),
    [summaries],
  );

  return (
    <ReactFlowProvider>
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: palette.FIDESUI_BG_CORINTH,
          border: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
          borderRadius: 8,
          overflow: "hidden",
        }}
      >
        <NetworkGraph purposes={purposes} summariesByKey={summariesByKey} />
      </div>
    </ReactFlowProvider>
  );
};

export default PurposeNetworkView;

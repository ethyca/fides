import { Edge, Node } from "@xyflow/react";
import yaml from "js-yaml";

import { ConstraintNodeData } from "./ConstraintNode";
import { ActionNodeData } from "./DecisionNode";
import { ConditionNodeData } from "./MatchNode";
import { PolicyNodeData } from "./PolicyNode";
import {
  AccessPolicyYaml,
  ActionBlock,
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  GeoOperator,
  MatchBlock,
  MatchDimension,
  UnlessItem,
} from "./types";

// ─── YAML parsing ────────────────────────────────────────────────────────────

export const parseYaml = (yamlString: string): AccessPolicyYaml | null => {
  if (!yamlString.trim()) {
    return null;
  }
  try {
    const parsed = yaml.load(yamlString);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    const obj = parsed as Record<string, unknown>;
    // Require either decision or name to be present for a valid policy
    if (typeof obj.decision !== "string" && typeof obj.name !== "string") {
      return null;
    }
    return parsed as AccessPolicyYaml;
  } catch {
    return null;
  }
};

// ─── YAML → Nodes + Edges ────────────────────────────────────────────────────

const CONDITION_PROPERTY_KEYS: ConditionProperty[] = [
  ConditionProperty.DATA_CATEGORIES,
  ConditionProperty.DATA_USE,
  ConditionProperty.DATA_SUBJECTS,
];

export const POLICY_NODE_ID = "policy";

/**
 * Build display edges using a chain topology:
 *   action ──when──▶ cond1 ──and──▶ cond2 ──and──▶ cond3
 *                     │
 *                     └──unless──▶ constraint1 ──and──▶ constraint2
 *
 * Horizontal edges use default Left/Right handles.
 * Vertical "and" edges use Bottom→Top handles so dagre-independent
 * rendering draws them top-to-bottom within a column.
 */
export const yamlToNodesAndEdges = (
  yamlString: string,
): { nodes: Node[]; edges: Edge[] } | null => {
  const policy = parseYaml(yamlString);
  if (!policy) {
    return null;
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Policy node — callbacks are injected by PolicyCanvasPanel at render time
  const policyNode: Node<PolicyNodeData, "policyNode"> = {
    id: POLICY_NODE_ID,
    type: "policyNode",
    position: { x: 0, y: 0 },
    style: { width: 300 },
    data: {
      name: policy.name ?? "",
      description: policy.description ?? "",
      fidesKey: policy.fides_key ?? "",
      enabled: policy.enabled ?? true,
      priority: policy.priority ?? 0,
      controls: policy.controls ?? [],
      controlOptions: [],
      actionMessage: policy.action?.message ?? "",
      onNameChange: () => {},
      onDescriptionChange: () => {},
      onFidesKeyChange: () => {},
      onEnabledChange: () => {},
      onPriorityChange: () => {},
      onControlsChange: () => {},
      onActionMessageChange: () => {},
    },
  };
  nodes.push(policyNode);

  const { decision } = policy;
  const matchBlock: MatchBlock | undefined = policy.match;

  if (!decision || !matchBlock) {
    return { nodes, edges };
  }

  // Action node
  const actionType = decision === "DENY" ? ActionType.DENY : ActionType.ALLOW;
  const actionId = "action-1";
  const actionNode: Node<ActionNodeData, "actionNode"> = {
    id: actionId,
    type: "actionNode",
    position: { x: 0, y: 0 },
    style: { width: 300 },
    data: {
      actionType,
      actionMessage: policy.action?.message ?? "",
    },
  };
  nodes.push(actionNode);
  edges.push({
    id: `e-${POLICY_NODE_ID}-${actionId}`,
    source: POLICY_NODE_ID,
    target: actionId,
    type: "labeledEdge",
  });

  // Condition nodes — chain: first from action ("when"), rest vertical ("and")
  const presentProperties = CONDITION_PROPERTY_KEYS.filter(
    (p) => !!matchBlock[p],
  );

  presentProperties.forEach((property, idx) => {
    const dimension = matchBlock[property] as MatchDimension;
    let operator = ConditionOperator.ALL;
    if (dimension.any) {
      operator = ConditionOperator.ANY;
    }
    const values = dimension.all ?? dimension.any ?? [];
    const conditionId = `condition-${idx + 1}`;

    const conditionNode: Node<ConditionNodeData, "conditionNode"> = {
      id: conditionId,
      type: "conditionNode",
      position: { x: 0, y: 0 },
      style: { width: 300 },
      data: {
        property,
        values,
        operator,
      },
    };
    nodes.push(conditionNode);

    if (idx === 0) {
      // First condition: horizontal from action
      edges.push({
        id: `e-${actionId}-${conditionId}`,
        source: actionId,
        target: conditionId,
        type: "labeledEdge",
        data: { label: "when" },
      });
    } else {
      // Subsequent conditions: vertical "and" from previous
      const prevConditionId = `condition-${idx}`;
      edges.push({
        id: `e-${prevConditionId}-${conditionId}`,
        source: prevConditionId,
        target: conditionId,
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "labeledEdge",
        data: { label: "and" },
      });
    }
  });

  // Constraint nodes from `unless` — flat array, all AND'd
  const constraintList: UnlessItem[] = policy.unless ?? [];

  if (constraintList.length > 0 && presentProperties.length > 0) {
    constraintList.forEach((item, idx) => {
      const constraintId = `constraint-${idx + 1}`;
      let data: ConstraintNodeData = {};

      if (item.type === "consent") {
        data = {
          constraintType: ConstraintType.CONSENT,
          privacyNoticeKey: item.privacy_notice_key ?? "",
          consentRequirement: item.requirement as ConsentRequirement,
        };
      } else if (item.type === "geo_location") {
        data = {
          constraintType: ConstraintType.GEO_LOCATION,
          geoField: item.field ?? "",
          geoOperator: item.operator as GeoOperator,
          geoValues: item.values ?? [],
        };
      } else if (item.type === "data_flow") {
        data = {
          constraintType: ConstraintType.DATA_FLOW,
          dataFlowDirection: item.direction as DataFlowDirection,
          dataFlowOperator: item.operator as DataFlowOperator,
          dataFlowSystems: item.systems ?? [],
        };
      }

      const constraintNode: Node<ConstraintNodeData, "constraintNode"> = {
        id: constraintId,
        type: "constraintNode",
        position: { x: 0, y: 0 },
        style: { width: 300 },
        data,
      };
      nodes.push(constraintNode);

      if (idx === 0) {
        // First constraint: horizontal from first condition
        edges.push({
          id: `e-condition-1-${constraintId}`,
          source: "condition-1",
          target: constraintId,
          type: "labeledEdge",
          data: { label: "unless" },
        });
      } else {
        // Subsequent constraints: vertical "and" from previous
        const prevConstraintId = `constraint-${idx}`;
        edges.push({
          id: `e-${prevConstraintId}-${constraintId}`,
          source: prevConstraintId,
          target: constraintId,
          sourceHandle: "bottom",
          targetHandle: "top",
          type: "labeledEdge",
          data: { label: "and" },
        });
      }
    });
  }

  return { nodes, edges };
};

// ─── Nodes + Edges → YAML ────────────────────────────────────────────────────

/**
 * Collect all conditionNode nodes reachable from actionNodeId via BFS.
 * Works with both fan-out and chain topologies.
 */
const collectConditionNodes = (
  actionNodeId: string,
  nodes: Node[],
  edges: Edge[],
): Node<ConditionNodeData>[] => {
  const result: Node<ConditionNodeData>[] = [];
  const visited = new Set<string>();

  const walk = (sourceId: string) => {
    edges
      .filter((e) => e.source === sourceId && !visited.has(e.target))
      .forEach((e) => {
        const target = nodes.find((n) => n.id === e.target);
        if (!target || target.type !== "conditionNode") {
          return;
        }
        visited.add(target.id);
        result.push(target as Node<ConditionNodeData>);
        walk(target.id);
      });
  };
  walk(actionNodeId);

  return result;
};

/**
 * Collect all constraintNode nodes reachable from the given condition node IDs,
 * walking through constraint chains.
 */
const collectConstraintNodes = (
  conditionNodeIds: Set<string>,
  nodes: Node[],
  edges: Edge[],
): Node<ConstraintNodeData>[] => {
  const result: Node<ConstraintNodeData>[] = [];
  const visited = new Set<string>();
  const queue = [...conditionNodeIds];

  while (queue.length > 0) {
    const sourceId = queue.shift()!;
    edges
      .filter((e) => e.source === sourceId && !visited.has(e.target))
      .forEach((e) => {
        visited.add(e.target);
        const target = nodes.find((n) => n.id === e.target);
        if (!target) {
          return;
        }
        if (target.type === "constraintNode") {
          result.push(target as Node<ConstraintNodeData>);
          queue.push(target.id);
        }
      });
  }

  return result;
};

const buildUnlessItem = (data: ConstraintNodeData): UnlessItem | null => {
  if (data.constraintType === ConstraintType.CONSENT) {
    if (!data.privacyNoticeKey && !data.consentRequirement) {
      return null;
    }
    return {
      type: "consent",
      privacy_notice_key: data.privacyNoticeKey ?? "",
      requirement: data.consentRequirement as ConsentRequirement,
    };
  }
  if (data.constraintType === ConstraintType.GEO_LOCATION) {
    if (!data.geoField && !data.geoValues?.length) {
      return null;
    }
    return {
      type: "geo_location",
      field: data.geoField ?? "",
      operator: (data.geoOperator as GeoOperator) ?? GeoOperator.IN,
      values: data.geoValues ?? [],
    };
  }
  if (data.constraintType === ConstraintType.DATA_FLOW) {
    if (!data.dataFlowSystems?.length) {
      return null;
    }
    return {
      type: "data_flow",
      direction:
        (data.dataFlowDirection as DataFlowDirection) ??
        DataFlowDirection.EGRESS,
      operator:
        (data.dataFlowOperator as DataFlowOperator) ?? DataFlowOperator.ANY_OF,
      systems: data.dataFlowSystems ?? [],
    };
  }
  return null;
};

export const nodesToYaml = (nodes: Node[], edges: Edge[]): string => {
  const policyNode = nodes.find(
    (n): n is Node<PolicyNodeData> => n.id === POLICY_NODE_ID,
  );
  if (!policyNode) {
    return "";
  }

  const { name, description, fidesKey, enabled, priority, controls } =
    policyNode.data as PolicyNodeData;

  // Find action node (connected from policy)
  const actionEdge = edges.find((e) => e.source === POLICY_NODE_ID);
  const actionNode = actionEdge
    ? nodes.find((n): n is Node<ActionNodeData> => n.id === actionEdge.target)
    : undefined;

  // Build the YAML object following PRD schema
  const policyYaml: Record<string, unknown> = {};

  if (fidesKey) {
    policyYaml.fides_key = fidesKey;
  }
  if (name) {
    policyYaml.name = name;
  }
  if (description) {
    policyYaml.description = description;
  }
  if (enabled === false) {
    policyYaml.enabled = false;
  }
  if (priority !== undefined && priority !== 0) {
    policyYaml.priority = priority;
  }
  if (controls && controls.length > 0) {
    policyYaml.controls = controls;
  }

  if (!actionNode) {
    return yaml.dump(policyYaml, { lineWidth: -1 });
  }

  const { actionType } = actionNode.data as ActionNodeData;

  // Decision
  policyYaml.decision = actionType === ActionType.DENY ? "DENY" : "ALLOW";

  // Match block
  const conditionNodes = collectConditionNodes(actionNode.id, nodes, edges);
  const matchBlock: MatchBlock = conditionNodes.reduce<MatchBlock>(
    (acc, condNode) => {
      const { property, values, operator } = condNode.data as ConditionNodeData;
      if (!property || !values?.length) {
        return acc;
      }
      const dimension: MatchDimension =
        operator === ConditionOperator.ALL ? { all: values } : { any: values };
      return { ...acc, [property]: dimension };
    },
    {},
  );
  policyYaml.match = matchBlock;

  // Unless block — flat array, all AND'd
  const conditionIds = new Set(conditionNodes.map((n) => n.id));
  const constraintNodes = collectConstraintNodes(conditionIds, nodes, edges);
  const unlessItems: UnlessItem[] = constraintNodes
    .map((n) => buildUnlessItem(n.data as ConstraintNodeData))
    .filter((item): item is UnlessItem => !!item);

  if (unlessItems.length > 0) {
    policyYaml.unless = unlessItems;
  }

  // Action block — read from the action node
  const { actionMessage } = actionNode.data as ActionNodeData;
  if (actionMessage) {
    policyYaml.action = { message: actionMessage } satisfies ActionBlock;
  }

  return yaml.dump(policyYaml, { lineWidth: -1 });
};

// ─── Layout helpers ──────────────────────────────────────────────────────────

/**
 * Derive fan-out edges from display edges for dagre positioning.
 * Dagre uses these to assign same-rank to same-type sibling nodes,
 * while the original chain edges are rendered by React Flow.
 */
export const deriveLayoutEdges = (nodes: Node[], edges: Edge[]): Edge[] => {
  const layoutEdges: Edge[] = [];

  // Keep policy → action edge
  const policyToAction = edges.find((e) => e.source === POLICY_NODE_ID);
  if (policyToAction) {
    layoutEdges.push(policyToAction);
  }

  const actionNode = nodes.find((n) => n.type === "actionNode");
  if (!actionNode) {
    return layoutEdges;
  }

  // Fan out: action → all conditions (forces same dagre rank)
  const conditionNodes = nodes.filter((n) => n.type === "conditionNode");
  conditionNodes.forEach((cond) => {
    layoutEdges.push({
      id: `layout-${actionNode.id}-${cond.id}`,
      source: actionNode.id,
      target: cond.id,
      type: "labeledEdge",
    });
  });

  // Fan out: first condition → all constraints (forces same dagre rank)
  const constraintNodes = nodes.filter((n) => n.type === "constraintNode");
  const firstCondition = conditionNodes[0];
  if (firstCondition && constraintNodes.length > 0) {
    constraintNodes.forEach((cons) => {
      layoutEdges.push({
        id: `layout-${firstCondition.id}-${cons.id}`,
        source: firstCondition.id,
        target: cons.id,
        type: "labeledEdge",
      });
    });
  }

  return layoutEdges;
};

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

/**
 * Extract top-level fields from a policy YAML string for list display.
 * Avoids building the full node graph — just reads the scalar fields.
 */
export const extractPolicyFields = (
  yamlString?: string,
): { enabled: boolean; priority: number; decision?: ActionType } => {
  if (!yamlString) {
    return { enabled: true, priority: 0 };
  }
  const parsed = parseYaml(yamlString);
  if (!parsed) {
    return { enabled: true, priority: 0 };
  }
  return {
    enabled: parsed.enabled ?? true,
    priority: parsed.priority ?? 0,
    decision: parsed.decision,
  };
};

/**
 * Update a single field in a policy YAML string without disturbing the rest.
 * Returns the modified YAML string.
 */
export const updateYamlField = (
  yamlString: string,
  field: string,
  value: unknown,
): string => {
  try {
    const parsed = yaml.load(yamlString) as Record<string, unknown> | null;
    if (!parsed || typeof parsed !== "object") {
      return yamlString;
    }
    parsed[field] = value;
    return yaml.dump(parsed, { lineWidth: 120 });
  } catch {
    return yamlString;
  }
};

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
      control: policy.control ?? null,
      controlOptions: [],
      actionMessage: policy.action?.message ?? "",
      onNameChange: () => {},
      onDescriptionChange: () => {},
      onFidesKeyChange: () => {},
      onEnabledChange: () => {},
      onPriorityChange: () => {},
      onControlChange: () => {},
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
      field: data.geoField || "environment.geo_location",
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

  const { name, description, fidesKey, enabled, priority, control } =
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
  if (control) {
    policyYaml.control = control;
  }

  if (!actionNode) {
    return yaml.dump(policyYaml, { lineWidth: 120 });
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

  return yaml.dump(policyYaml, { lineWidth: 120 });
};

// ---------------------------------------------------------------------------
// Policy diff: structural comparison of two parsed AccessPolicyYaml objects.
// Drives the agent-update transition (per-node CSS state, ghost-removed
// nodes during the hold phase, and the textual summary in the chat bubble).
// ---------------------------------------------------------------------------

export type ChangeStatus = "added" | "removed" | "modified" | "unchanged";

export interface PolicyDiffSummary {
  added: string[];
  modified: string[];
  removed: string[];
}

export interface PolicyDiff {
  policyMetadata: ChangeStatus;
  action: ChangeStatus;
  conditions: Partial<Record<ConditionProperty, ChangeStatus>>;
  constraints: Array<{ matchKey: string; status: ChangeStatus }>;
  removedConditionProperties: ConditionProperty[];
  removedConstraintKeys: string[];
  hasChanges: boolean;
  summary: PolicyDiffSummary;
}

const constraintMatchKey = (item: UnlessItem): string => {
  if (item.type === "consent") {
    return `consent:${item.privacy_notice_key ?? ""}`;
  }
  if (item.type === "geo_location") {
    return `geo_location:${item.field ?? ""}`;
  }
  return `data_flow:${item.direction ?? ""}`;
};

const constraintMatchKeyFromNode = (
  data: ConstraintNodeData,
): string | null => {
  if (data.constraintType === ConstraintType.CONSENT) {
    return `consent:${data.privacyNoticeKey ?? ""}`;
  }
  if (data.constraintType === ConstraintType.GEO_LOCATION) {
    return `geo_location:${data.geoField ?? ""}`;
  }
  if (data.constraintType === ConstraintType.DATA_FLOW) {
    return `data_flow:${data.dataFlowDirection ?? ""}`;
  }
  return null;
};

const constraintLabel = (item: UnlessItem): string => {
  if (item.type === "consent") {
    return item.privacy_notice_key
      ? `consent constraint (${item.privacy_notice_key})`
      : "consent constraint";
  }
  if (item.type === "geo_location") {
    return "geo_location constraint";
  }
  return "data_flow constraint";
};

const CONDITION_LABELS: Record<ConditionProperty, string> = {
  [ConditionProperty.DATA_USE]: "data use condition",
  [ConditionProperty.DATA_CATEGORIES]: "data category condition",
  [ConditionProperty.DATA_SUBJECTS]: "data subject condition",
};

const dimensionsEqual = (
  a: MatchDimension | undefined,
  b: MatchDimension | undefined,
): boolean => {
  if (!a && !b) {
    return true;
  }
  if (!a || !b) {
    return false;
  }
  const aOp = a.any !== undefined ? "any" : "all";
  const bOp = b.any !== undefined ? "any" : "all";
  if (aOp !== bOp) {
    return false;
  }
  const aVals = a.any ?? a.all ?? [];
  const bVals = b.any ?? b.all ?? [];
  if (aVals.length !== bVals.length) {
    return false;
  }
  return aVals.every((v, i) => v === bVals[i]);
};

const constraintContentEqual = (a: UnlessItem, b: UnlessItem): boolean => {
  if (a.type !== b.type) {
    return false;
  }
  if (a.type === "consent" && b.type === "consent") {
    return (
      a.privacy_notice_key === b.privacy_notice_key &&
      a.requirement === b.requirement
    );
  }
  if (a.type === "geo_location" && b.type === "geo_location") {
    if (a.field !== b.field || a.operator !== b.operator) {
      return false;
    }
    if ((a.values?.length ?? 0) !== (b.values?.length ?? 0)) {
      return false;
    }
    return (a.values ?? []).every((v, i) => v === (b.values ?? [])[i]);
  }
  if (a.type === "data_flow" && b.type === "data_flow") {
    if (a.direction !== b.direction || a.operator !== b.operator) {
      return false;
    }
    if ((a.systems?.length ?? 0) !== (b.systems?.length ?? 0)) {
      return false;
    }
    return (a.systems ?? []).every((v, i) => v === (b.systems ?? [])[i]);
  }
  return false;
};

const metadataEqual = (a: AccessPolicyYaml, b: AccessPolicyYaml): boolean =>
  (a.fides_key ?? "") === (b.fides_key ?? "") &&
  (a.name ?? "") === (b.name ?? "") &&
  (a.description ?? "") === (b.description ?? "") &&
  (a.enabled ?? true) === (b.enabled ?? true) &&
  (a.priority ?? 0) === (b.priority ?? 0) &&
  (a.control ?? null) === (b.control ?? null);

const hasMetadata = (p: AccessPolicyYaml): boolean =>
  !!(
    p.fides_key ||
    p.name ||
    p.description ||
    p.enabled === false ||
    (p.priority && p.priority !== 0) ||
    p.control
  );

const emptyDiff = (): PolicyDiff => ({
  policyMetadata: "unchanged",
  action: "unchanged",
  conditions: {},
  constraints: [],
  removedConditionProperties: [],
  removedConstraintKeys: [],
  hasChanges: false,
  summary: { added: [], modified: [], removed: [] },
});

export const diffPolicies = (
  oldYaml: string | undefined,
  newYaml: string,
): PolicyDiff => {
  const newPolicy = parseYaml(newYaml);
  if (!newPolicy) {
    return emptyDiff();
  }
  const oldPolicy = oldYaml ? parseYaml(oldYaml) : null;

  const summary: PolicyDiffSummary = { added: [], modified: [], removed: [] };

  // --- Policy metadata ---
  let policyMetadata: ChangeStatus = "unchanged";
  if (!oldPolicy) {
    if (hasMetadata(newPolicy)) {
      policyMetadata = "added";
      summary.added.push("policy details");
    }
  } else if (!metadataEqual(oldPolicy, newPolicy)) {
    policyMetadata = "modified";
    summary.modified.push("policy details");
  }

  // --- Action ---
  const oldDecision = oldPolicy?.decision;
  const newDecision = newPolicy.decision;
  const oldMessage = oldPolicy?.action?.message ?? "";
  const newMessage = newPolicy.action?.message ?? "";

  let actionStatus: ChangeStatus = "unchanged";
  if (!oldPolicy) {
    if (newDecision) {
      actionStatus = "added";
      summary.added.push("decision");
    }
  } else if (!oldDecision && newDecision) {
    actionStatus = "added";
    summary.added.push("decision");
  } else if (oldDecision && !newDecision) {
    actionStatus = "removed";
    summary.removed.push("decision");
  } else if (oldDecision !== newDecision || oldMessage !== newMessage) {
    actionStatus = "modified";
    if (oldDecision !== newDecision) {
      summary.modified.push(`decision (${oldDecision} → ${newDecision})`);
    }
    if (oldMessage !== newMessage) {
      summary.modified.push("action message");
    }
  }

  // --- Conditions (keyed by property) ---
  const conditions: Partial<Record<ConditionProperty, ChangeStatus>> = {};
  const removedConditionProperties: ConditionProperty[] = [];
  const oldMatch: MatchBlock = oldPolicy?.match ?? {};
  const newMatch: MatchBlock = newPolicy.match ?? {};

  CONDITION_PROPERTY_KEYS.forEach((property) => {
    const oldDim = oldMatch[property];
    const newDim = newMatch[property];
    if (!oldDim && newDim) {
      conditions[property] = "added";
      summary.added.push(CONDITION_LABELS[property]);
    } else if (oldDim && !newDim) {
      removedConditionProperties.push(property);
      summary.removed.push(CONDITION_LABELS[property]);
    } else if (oldDim && newDim) {
      if (dimensionsEqual(oldDim, newDim)) {
        conditions[property] = "unchanged";
      } else {
        conditions[property] = "modified";
        summary.modified.push(CONDITION_LABELS[property]);
      }
    }
  });

  // --- Constraints (matched by content key) ---
  const oldUnless = oldPolicy?.unless ?? [];
  const newUnless = newPolicy.unless ?? [];
  const oldByKey = new Map<string, UnlessItem>();
  oldUnless.forEach((item) => {
    const key = constraintMatchKey(item);
    if (!oldByKey.has(key)) {
      oldByKey.set(key, item);
    }
  });
  const usedOldKeys = new Set<string>();

  const constraints: Array<{ matchKey: string; status: ChangeStatus }> = [];
  newUnless.forEach((newItem) => {
    const key = constraintMatchKey(newItem);
    const oldItem = oldByKey.get(key);
    if (!oldItem) {
      constraints.push({ matchKey: key, status: "added" });
      summary.added.push(constraintLabel(newItem));
    } else if (constraintContentEqual(oldItem, newItem)) {
      constraints.push({ matchKey: key, status: "unchanged" });
      usedOldKeys.add(key);
    } else {
      constraints.push({ matchKey: key, status: "modified" });
      summary.modified.push(constraintLabel(newItem));
      usedOldKeys.add(key);
    }
  });

  const removedConstraintKeys: string[] = [];
  oldByKey.forEach((item, key) => {
    if (!usedOldKeys.has(key)) {
      removedConstraintKeys.push(key);
      summary.removed.push(constraintLabel(item));
    }
  });

  const hasChanges =
    policyMetadata !== "unchanged" ||
    actionStatus !== "unchanged" ||
    Object.values(conditions).some((s) => s === "added" || s === "modified") ||
    removedConditionProperties.length > 0 ||
    constraints.some((c) => c.status === "added" || c.status === "modified") ||
    removedConstraintKeys.length > 0;

  return {
    policyMetadata,
    action: actionStatus,
    conditions,
    constraints,
    removedConditionProperties,
    removedConstraintKeys,
    hasChanges,
    summary,
  };
};

/**
 * Tag each node and edge with `_diffStatus` and `_diffKey` based on the diff,
 * so node components can drive CSS animations. Bumping `_diffKey` on a fresh
 * diff cycle restarts the CSS animation even if the status is the same.
 */
const resolveNodeStatus = (
  node: Node,
  diff: PolicyDiff,
): ChangeStatus | undefined => {
  if (node.id.startsWith("removed-")) {
    return "removed";
  }
  if (node.id === POLICY_NODE_ID) {
    return diff.policyMetadata !== "unchanged"
      ? diff.policyMetadata
      : undefined;
  }
  if (node.type === "actionNode") {
    return diff.action !== "unchanged" ? diff.action : undefined;
  }
  if (node.type === "conditionNode") {
    const { property } = node.data as ConditionNodeData;
    if (!property) {
      return undefined;
    }
    const s = diff.conditions[property];
    return s && s !== "unchanged" ? s : undefined;
  }
  if (node.type === "constraintNode") {
    const matchKey = constraintMatchKeyFromNode(
      node.data as ConstraintNodeData,
    );
    if (!matchKey) {
      return undefined;
    }
    const c = diff.constraints.find((x) => x.matchKey === matchKey);
    return c && c.status !== "unchanged" ? c.status : undefined;
  }
  return undefined;
};

export const tagNodesWithDiff = (
  nodes: Node[],
  edges: Edge[],
  diff: PolicyDiff,
  diffKey: number,
): { nodes: Node[]; edges: Edge[] } => {
  const statusById = new Map<string, ChangeStatus>();
  const taggedNodes = nodes.map((node) => {
    const status = resolveNodeStatus(node, diff);
    if (!status) {
      return node;
    }
    statusById.set(node.id, status);
    // The className flows through to the React Flow node wrapper, allowing
    // diff styling to live in module SCSS without each node component needing
    // to know about the diff status. The diffKey is appended so changing it
    // forces a class swap and restarts the CSS animation.
    const className = [
      node.className,
      `diffStatus-${status}`,
      `diffKey-${diffKey}`,
    ]
      .filter(Boolean)
      .join(" ");
    return { ...node, className };
  });

  const taggedEdges = edges.map((edge) => {
    const sourceStatus = statusById.get(edge.source);
    const targetStatus = statusById.get(edge.target);
    let edgeStatus: ChangeStatus | undefined;
    if (sourceStatus === "removed" || targetStatus === "removed") {
      edgeStatus = "removed";
    } else if (sourceStatus === "added" || targetStatus === "added") {
      edgeStatus = "added";
    }
    if (!edgeStatus) {
      return edge;
    }
    const className = [edge.className, `diffStatus-${edgeStatus}`]
      .filter(Boolean)
      .join(" ");
    return { ...edge, className };
  });

  return { nodes: taggedNodes, edges: taggedEdges };
};

/**
 * Build a transient graph that overlays the new YAML's nodes with ghost
 * copies of the conditions/constraints removed from the old YAML. Ghost
 * nodes are prefixed with `removed-` so they don't collide with the manual
 * id counter regex in PolicyCanvasPanel.syncCounters.
 */
export const buildUnionGraph = (
  oldYaml: string | undefined,
  newYaml: string,
  diff: PolicyDiff,
): { nodes: Node[]; edges: Edge[] } => {
  const newGraph = yamlToNodesAndEdges(newYaml);
  if (!newGraph) {
    return { nodes: [], edges: [] };
  }
  if (
    !oldYaml ||
    (diff.removedConditionProperties.length === 0 &&
      diff.removedConstraintKeys.length === 0)
  ) {
    return newGraph;
  }
  const oldGraph = yamlToNodesAndEdges(oldYaml);
  if (!oldGraph) {
    return newGraph;
  }

  const ghostNodes: Node[] = [];
  const ghostEdges: Edge[] = [];

  const newActionNode = newGraph.nodes.find((n) => n.type === "actionNode");
  const newFirstCondition = newGraph.nodes.find(
    (n) => n.type === "conditionNode",
  );

  diff.removedConditionProperties.forEach((property) => {
    const oldNode = oldGraph.nodes.find(
      (n) =>
        n.type === "conditionNode" &&
        (n.data as ConditionNodeData).property === property,
    );
    if (!oldNode) {
      return;
    }
    const ghostId = `removed-condition-${property}`;
    ghostNodes.push({
      ...oldNode,
      id: ghostId,
      position: { x: 0, y: 0 },
      selectable: false,
      draggable: false,
    });
    if (newActionNode) {
      ghostEdges.push({
        id: `e-ghost-${newActionNode.id}-${ghostId}`,
        source: newActionNode.id,
        target: ghostId,
        type: "labeledEdge",
        data: { label: "when" },
      });
    }
  });

  diff.removedConstraintKeys.forEach((key) => {
    const oldNode = oldGraph.nodes.find((n) => {
      if (n.type !== "constraintNode") {
        return false;
      }
      const k = constraintMatchKeyFromNode(n.data as ConstraintNodeData);
      return k === key;
    });
    if (!oldNode) {
      return;
    }
    const sanitized = key.replace(/[^a-zA-Z0-9_-]/g, "_");
    const ghostId = `removed-constraint-${sanitized}`;
    ghostNodes.push({
      ...oldNode,
      id: ghostId,
      position: { x: 0, y: 0 },
      selectable: false,
      draggable: false,
    });
    const sourceId =
      newFirstCondition?.id ??
      ghostNodes.find((n) => n.type === "conditionNode")?.id;
    if (sourceId) {
      ghostEdges.push({
        id: `e-ghost-${sourceId}-${ghostId}`,
        source: sourceId,
        target: ghostId,
        type: "labeledEdge",
        data: { label: "unless" },
      });
    }
  });

  return {
    nodes: [...newGraph.nodes, ...ghostNodes],
    edges: [...newGraph.edges, ...ghostEdges],
  };
};

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

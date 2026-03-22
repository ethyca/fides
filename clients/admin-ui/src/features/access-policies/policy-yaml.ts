import { Edge, Node } from "@xyflow/react";
import yaml from "js-yaml";

import { ActionNodeData } from "./ActionNode";
import { ConditionNodeData } from "./ConditionNode";
import { ConstraintNodeData } from "./ConstraintNode";
import { PolicyNodeData } from "./PolicyNode";
import {
  AccessPolicyYaml,
  ActionType,
  ConditionClause,
  ConditionMap,
  ConditionOperator,
  ConditionProperty,
  ConsentConstraintItem,
  ConsentValue,
  ConstraintItem,
  ConstraintType,
  UserConstraintItem,
  UserOperator,
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
    if (typeof obj.name !== "string") {
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
export const JUNCTION_NODE_ID = "junction";

const resolveActionType = (
  policy: AccessPolicyYaml,
): ActionType | undefined => {
  if (policy.deny) {
    return ActionType.DENY;
  }
  if (policy.allow) {
    return ActionType.ALLOW;
  }
  return undefined;
};

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
      controlGroupOptions: [],
      onNameChange: () => {},
      onDescriptionChange: () => {},
      onControlGroupChange: () => {},
    },
  };
  nodes.push(policyNode);

  const actionType = resolveActionType(policy);
  const conditionMap: ConditionMap | undefined = policy.deny ?? policy.allow;

  if (!actionType || !conditionMap) {
    return { nodes, edges };
  }

  // Action node
  const actionId = "action-1";
  const actionNode: Node<ActionNodeData, "actionNode"> = {
    id: actionId,
    type: "actionNode",
    position: { x: 0, y: 0 },
    style: { width: 300 },
    data: { actionType },
  };
  nodes.push(actionNode);
  edges.push({
    id: `e-${POLICY_NODE_ID}-${actionId}`,
    source: POLICY_NODE_ID,
    target: actionId,
    type: "labeledEdge",
  });

  // Condition nodes — fan out from action (same column in dagre)
  const presentProperties = CONDITION_PROPERTY_KEYS.filter(
    (p) => !!conditionMap[p],
  );

  presentProperties.forEach((property, idx) => {
    const clause = conditionMap[property] as ConditionClause;
    const conditionId = `condition-${idx + 1}`;

    const conditionNode: Node<ConditionNodeData, "conditionNode"> = {
      id: conditionId,
      type: "conditionNode",
      position: { x: 0, y: 0 },
      style: { width: 300 },
      data: {
        property,
        values: clause.values ?? [],
        operator: clause.operator ?? ConditionOperator.ANY,
      },
    };
    nodes.push(conditionNode);

    // All conditions fan out from action with "when" label
    edges.push({
      id: `e-${actionId}-${conditionId}`,
      source: actionId,
      target: conditionId,
      type: "labeledEdge",
      data: { label: "when" },
    });
  });

  // Constraint nodes from `unless` — fan out from junction
  const constraintList: ConstraintItem[] =
    policy.unless?.any ?? policy.unless?.all ?? [];

  if (constraintList.length > 0 && presentProperties.length > 0) {
    // Add junction node to bridge conditions → constraints
    nodes.push({
      id: JUNCTION_NODE_ID,
      type: "junctionNode",
      position: { x: 0, y: 0 },
      style: { width: 16, height: 16 },
      data: {},
    });

    // Connect all conditions → junction
    presentProperties.forEach((_, idx) => {
      const conditionId = `condition-${idx + 1}`;
      edges.push({
        id: `e-${conditionId}-${JUNCTION_NODE_ID}`,
        source: conditionId,
        target: JUNCTION_NODE_ID,
        type: "labeledEdge",
      });
    });

    // Connect junction → each constraint
    constraintList.forEach((item, idx) => {
      const constraintId = `constraint-${idx + 1}`;
      let data: ConstraintNodeData = {};

      if ("consent" in item) {
        const consentItem = item as ConsentConstraintItem;
        data = {
          constraintType: ConstraintType.CONSENT,
          preferenceKey: consentItem.consent.preference_key?.[0] ?? "",
          consentValue: consentItem.consent.value as ConsentValue,
        };
      } else if ("user" in item) {
        const userItem = item as UserConstraintItem;
        data = {
          constraintType: ConstraintType.USER,
          userKey: String(userItem.user.key),
          userValue: String(userItem.user.value),
          userOperator: userItem.user.operator as UserOperator,
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

      edges.push({
        id: `e-${JUNCTION_NODE_ID}-${constraintId}`,
        source: JUNCTION_NODE_ID,
        target: constraintId,
        type: "labeledEdge",
        data: { label: "unless" },
      });
    });
  }

  return { nodes, edges };
};

// ─── Nodes + Edges → YAML ────────────────────────────────────────────────────

/**
 * Collect all conditionNode nodes reachable from actionNodeId via BFS.
 * Works with both fan-out (action → cond1, action → cond2) and legacy
 * chain (action → cond1 → cond2) topologies.
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
 * walking through junction nodes and constraint chains.
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
        } else if (target.type === "junctionNode") {
          queue.push(target.id);
        }
      });
  }

  return result;
};

const buildConstraintItem = (
  data: ConstraintNodeData,
): ConstraintItem | null => {
  if (data.constraintType === ConstraintType.CONSENT) {
    if (!data.preferenceKey && !data.consentValue) {
      return null;
    }
    const item: ConsentConstraintItem = {
      consent: {
        preference_key: data.preferenceKey ? [data.preferenceKey] : [],
        value: data.consentValue as ConsentValue,
      },
    };
    return item;
  }
  if (data.constraintType === ConstraintType.USER) {
    if (!data.userKey && !data.userValue) {
      return null;
    }
    const item: UserConstraintItem = {
      user: {
        key: data.userKey ?? "",
        value: data.userValue ?? "",
        operator: data.userOperator as UserOperator,
      },
    };
    return item;
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

  const { name, description } = policyNode.data as PolicyNodeData;

  // Find action node (connected from policy)
  const actionEdge = edges.find((e) => e.source === POLICY_NODE_ID);
  const actionNode = actionEdge
    ? nodes.find((n): n is Node<ActionNodeData> => n.id === actionEdge.target)
    : undefined;

  const policyYaml: AccessPolicyYaml = { name: name ?? "" };

  if (description) {
    policyYaml.description = description;
  }

  if (!actionNode) {
    return yaml.dump(policyYaml, { lineWidth: -1 });
  }

  const { actionType } = actionNode.data as ActionNodeData;

  const conditionNodes = collectConditionNodes(actionNode.id, nodes, edges);

  // Build condition map from collected nodes
  const conditionMap: ConditionMap = conditionNodes.reduce<ConditionMap>(
    (acc, condNode) => {
      const { property, values, operator } = condNode.data as ConditionNodeData;
      if (!property || !values?.length) {
        return acc;
      }
      const clause: ConditionClause = { values };
      if (operator) {
        clause.operator = operator;
      }
      return { ...acc, [property]: clause };
    },
    {},
  );

  if (actionType === ActionType.DENY) {
    policyYaml.deny = conditionMap;
  } else if (actionType === ActionType.ALLOW) {
    policyYaml.allow = conditionMap;
  }

  // Collect constraint nodes reachable from conditions (through junctions)
  const conditionIds = new Set(conditionNodes.map((n) => n.id));
  const constraintNodes = collectConstraintNodes(conditionIds, nodes, edges);
  const constraintItems: ConstraintItem[] = constraintNodes
    .map((n) => buildConstraintItem(n.data as ConstraintNodeData))
    .filter((item): item is ConstraintItem => !!item);

  if (constraintItems.length > 0) {
    policyYaml.unless = { any: constraintItems };
  }

  return yaml.dump(policyYaml, { lineWidth: -1 });
};

import { useMemo } from "react";

import {
  PolicyV2Rule,
  PolicyV2RuleMatch,
  PolicyV2RuleConstraint,
} from "../../types";
import {
  FlowNode,
  FlowEdge,
  ActionNodeData,
  StartNodeData,
  MatchNodeData,
  ConstraintNodeData,
} from "../types";

/**
 * Validation error information
 */
export interface ValidationError {
  ruleId: string;
  ruleName: string;
  message: string;
}

/**
 * Result of converting flow nodes/edges back to policy rules
 */
export interface UseFlowToPolicyResult {
  rules: Omit<PolicyV2Rule, "id" | "order">[];
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * Options for the useFlowToPolicy hook
 */
export interface UseFlowToPolicyOptions {
  nodes: FlowNode[];
  edges: FlowEdge[];
}

/**
 * Custom hook for converting React Flow nodes and edges back into PolicyV2Rule format
 *
 * This hook handles:
 * - Grouping nodes by ruleId
 * - Extracting rule name from START node
 * - Extracting action and denial message from ACTION node
 * - Collecting and formatting MATCH nodes
 * - Collecting and formatting CONSTRAINT nodes
 * - Validating the flow structure
 *
 * @param options - Object containing nodes and edges arrays
 * @returns Object containing rules array, validation status, and errors
 */
export const useFlowToPolicy = ({
  nodes,
  edges,
}: UseFlowToPolicyOptions): UseFlowToPolicyResult => {
  const result = useMemo(() => {
    const rules: Omit<PolicyV2Rule, "id" | "order">[] = [];
    const errors: ValidationError[] = [];

    // Group nodes by ruleId
    const nodesByRule = new Map<string, FlowNode[]>();

    nodes.forEach((node) => {
      const ruleId = node.data.ruleId;
      if (!ruleId) {
        return;
      }

      if (!nodesByRule.has(ruleId)) {
        nodesByRule.set(ruleId, []);
      }
      nodesByRule.get(ruleId)!.push(node);
    });

    // Process each rule
    nodesByRule.forEach((ruleNodes, ruleId) => {
      // Find START node
      const startNodes = ruleNodes.filter(
        (node) => node.data.nodeType === "start"
      );
      if (startNodes.length === 0) {
        errors.push({
          ruleId,
          ruleName: "Unknown",
          message: "Rule is missing a START node",
        });
        return;
      }
      if (startNodes.length > 1) {
        errors.push({
          ruleId,
          ruleName: (startNodes[0].data as StartNodeData).ruleName,
          message: "Rule has multiple START nodes",
        });
        return;
      }

      const startNode = startNodes[0];
      const startData = startNode.data as StartNodeData;
      const ruleName = startData.ruleName;

      // Find ACTION node
      const actionNodes = ruleNodes.filter(
        (node) => node.data.nodeType === "action"
      );
      if (actionNodes.length === 0) {
        errors.push({
          ruleId,
          ruleName,
          message: "Rule is missing an ACTION node",
        });
        return;
      }
      if (actionNodes.length > 1) {
        errors.push({
          ruleId,
          ruleName,
          message: "Rule has multiple ACTION nodes",
        });
        return;
      }

      const actionNode = actionNodes[0];
      const actionData = actionNode.data as ActionNodeData;

      // Collect MATCH nodes
      const matchNodes = ruleNodes.filter(
        (node) => node.data.nodeType === "match"
      );
      const matches: PolicyV2RuleMatch[] = [];

      matchNodes.forEach((matchNode) => {
        const matchData = matchNode.data as MatchNodeData;
        const match = matchData.match;

        // Validate match has at least one value
        if (!match.values || match.values.length === 0) {
          errors.push({
            ruleId,
            ruleName,
            message: `Match node "${match.target_field}" has no values`,
          });
        }

        // Remove the id field if present (it's managed by the backend)
        const { id, ...matchWithoutId } = match;
        matches.push(matchWithoutId);
      });

      // Collect CONSTRAINT nodes
      const constraintNodes = ruleNodes.filter(
        (node) => node.data.nodeType === "constraint"
      );
      const constraints: PolicyV2RuleConstraint[] = [];

      constraintNodes.forEach((constraintNode) => {
        const constraintData = constraintNode.data as ConstraintNodeData;
        const constraint = constraintData.constraint;

        // Validate constraint configuration
        if (constraint.constraint_type === "privacy") {
          const config = constraint.configuration as any;
          if (!config.privacy_notice_key || config.privacy_notice_key.trim() === "") {
            errors.push({
              ruleId,
              ruleName,
              message: "Privacy constraint is missing privacy_notice_key",
            });
          }
        } else if (constraint.constraint_type === "context") {
          const config = constraint.configuration as any;
          if (!config.field || config.field.trim() === "") {
            errors.push({
              ruleId,
              ruleName,
              message: "Context constraint is missing field",
            });
          }
          if (!config.values || config.values.length === 0) {
            errors.push({
              ruleId,
              ruleName,
              message: "Context constraint has no values",
            });
          }
        }

        // Remove the id field if present (it's managed by the backend)
        const { id, ...constraintWithoutId } = constraint;
        constraints.push(constraintWithoutId);
      });

      // Build the rule object
      const rule: Omit<PolicyV2Rule, "id" | "order"> = {
        name: ruleName,
        action: actionData.action,
        matches,
        constraints,
      };

      // Add on_denial_message if action is DENY and message is provided
      if (
        actionData.action === "DENY" &&
        actionData.onDenialMessage &&
        actionData.onDenialMessage.trim() !== ""
      ) {
        rule.on_denial_message = actionData.onDenialMessage;
      }

      rules.push(rule);
    });

    return {
      rules,
      isValid: errors.length === 0,
      errors,
    };
  }, [nodes, edges]);

  return result;
};

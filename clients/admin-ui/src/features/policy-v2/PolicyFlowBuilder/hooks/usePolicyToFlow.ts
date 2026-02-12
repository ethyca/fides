import { useMemo } from "react";

import { PolicyV2 } from "../../types";
import { FlowNode, FlowEdge } from "../types";

/**
 * Custom hook for converting a PolicyV2 object into React Flow nodes and edges
 *
 * Layout: START → MATCH1 → AND → MATCH2 → ... → CONSTRAINT(s) → ACTION
 *
 * When there are multiple matches, AND gates are placed BETWEEN them in a
 * linear flow. This creates an intuitive left-to-right reading of the policy logic.
 *
 * @param policy - The PolicyV2 object to visualize
 * @returns Object containing formatted nodes and edges for ReactFlow
 */
export const usePolicyToFlow = (
  policy: PolicyV2 | null | undefined
): { nodes: FlowNode[]; edges: FlowEdge[] } => {
  const { nodes, edges } = useMemo(() => {
    if (!policy || !policy.rules || policy.rules.length === 0) {
      return { nodes: [], edges: [] };
    }

    const allNodes: FlowNode[] = [];
    const allEdges: FlowEdge[] = [];

    // Layout constants - each node type has its own width estimate + spacing
    const VERTICAL_SPACING = 300; // Space between rule lanes
    const HORIZONTAL_START = 80;

    // Node dimensions (approximate rendered sizes)
    const START_NODE_WIDTH = 160;
    const START_NODE_HEIGHT = 40;
    const MATCH_NODE_WIDTH = 240;
    const MATCH_NODE_HEIGHT = 120;
    const GATE_NODE_WIDTH = 60;
    const GATE_NODE_HEIGHT = 40;
    const CONSTRAINT_NODE_WIDTH = 220;
    const CONSTRAINT_NODE_HEIGHT = 100;
    const ACTION_NODE_WIDTH = 180;
    const ACTION_NODE_HEIGHT = 70;

    // Reference height to center-align all nodes against
    const REFERENCE_HEIGHT = MATCH_NODE_HEIGHT;

    // Spacing between nodes
    const NODE_SPACING = 80;

    policy.rules.forEach((rule, ruleIndex) => {
      const ruleId = rule.id || `rule-${ruleIndex}`;
      const baseY = ruleIndex * VERTICAL_SPACING + 100; // Top of the reference box
      let currentX = HORIZONTAL_START;

      // Helper to vertically center a node of a given height within the row
      const centerY = (nodeHeight: number) =>
        baseY + (REFERENCE_HEIGHT - nodeHeight) / 2;

      // ============================================================
      // 1. Create START node
      // ============================================================
      const startNodeId = `rule-${ruleIndex}-start`;
      allNodes.push({
        id: startNodeId,
        type: "start",
        position: { x: currentX, y: centerY(START_NODE_HEIGHT) },
        data: {
          nodeType: "start",
          ruleId,
          ruleName: rule.name,
        },
      });
      currentX += START_NODE_WIDTH + NODE_SPACING;

      // Track last node for edge connections
      let lastNodeId = startNodeId;

      // ============================================================
      // 2. Create MATCH nodes with AND gates BETWEEN them (linear layout)
      // ============================================================
      const hasMatches = rule.matches && rule.matches.length > 0;

      if (hasMatches) {
        const matchCount = rule.matches.length;

        rule.matches.forEach((match, matchIndex) => {
          const matchNodeId = `rule-${ruleIndex}-match-${matchIndex}`;

          // Create MATCH node
          allNodes.push({
            id: matchNodeId,
            type: "match",
            position: { x: currentX, y: centerY(MATCH_NODE_HEIGHT) },
            data: {
              nodeType: "match",
              ruleId,
              matchIndex,
              match,
            },
          });

          // Edge: previous node → this MATCH
          allEdges.push({
            id: `edge-${lastNodeId}-${matchNodeId}`,
            source: lastNodeId,
            target: matchNodeId,
            type: "smoothstep",
          });

          lastNodeId = matchNodeId;
          currentX += MATCH_NODE_WIDTH + NODE_SPACING;

          // If there are more matches, add an AND gate AFTER this match
          if (matchIndex < matchCount - 1) {
            const gateNodeId = `rule-${ruleIndex}-gate-${matchIndex}`;

            allNodes.push({
              id: gateNodeId,
              type: "gate",
              position: { x: currentX, y: centerY(GATE_NODE_HEIGHT) },
              data: {
                nodeType: "gate",
                ruleId,
                gateType: "AND",
              },
            });

            // Edge: MATCH → GATE
            allEdges.push({
              id: `edge-${matchNodeId}-${gateNodeId}`,
              source: matchNodeId,
              target: gateNodeId,
              type: "smoothstep",
            });

            lastNodeId = gateNodeId;
            currentX += GATE_NODE_WIDTH + NODE_SPACING;
          }
        });
      }

      // ============================================================
      // 3. Create CONSTRAINT nodes (in sequence)
      // ============================================================
      const hasConstraints = rule.constraints && rule.constraints.length > 0;

      if (hasConstraints) {
        rule.constraints.forEach((constraint, constraintIndex) => {
          const constraintNodeId = `rule-${ruleIndex}-constraint-${constraintIndex}`;

          allNodes.push({
            id: constraintNodeId,
            type: "constraint",
            position: { x: currentX, y: centerY(CONSTRAINT_NODE_HEIGHT) },
            data: {
              nodeType: "constraint",
              ruleId,
              constraintIndex,
              constraint,
            },
          });

          // Edge: previous node → this CONSTRAINT
          allEdges.push({
            id: `edge-${lastNodeId}-${constraintNodeId}`,
            source: lastNodeId,
            target: constraintNodeId,
            type: "smoothstep",
          });

          lastNodeId = constraintNodeId;
          currentX += CONSTRAINT_NODE_WIDTH + NODE_SPACING;
        });
      }

      // ============================================================
      // 4. Create ACTION node
      // ============================================================
      const actionNodeId = `rule-${ruleIndex}-action`;

      allNodes.push({
        id: actionNodeId,
        type: "action",
        position: { x: currentX, y: centerY(ACTION_NODE_HEIGHT) },
        data: {
          nodeType: "action",
          ruleId,
          action: rule.action,
          onDenialMessage: rule.on_denial_message,
        },
      });

      // Edge: last element → ACTION
      allEdges.push({
        id: `edge-${lastNodeId}-${actionNodeId}`,
        source: lastNodeId,
        target: actionNodeId,
        type: "smoothstep",
      });
    });

    return { nodes: allNodes, edges: allEdges };
  }, [policy]);

  return { nodes, edges };
};

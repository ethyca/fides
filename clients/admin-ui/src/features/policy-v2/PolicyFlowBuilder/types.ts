import { Node, Edge } from "@xyflow/react";
import {
  PolicyV2RuleMatch,
  PolicyV2RuleConstraint,
  PolicyV2Action,
} from "../types";

export type FlowNodeType =
  | "start"
  | "match"
  | "gate"
  | "constraint"
  | "action";

export interface StartNodeData extends Record<string, unknown> {
  nodeType: "start";
  ruleId: string;
  ruleName: string;
}

export interface MatchNodeData extends Record<string, unknown> {
  nodeType: "match";
  ruleId: string;
  matchIndex: number;
  match: PolicyV2RuleMatch;
}

export interface GateNodeData extends Record<string, unknown> {
  nodeType: "gate";
  ruleId: string;
  gateType: "AND";
}

export interface ConstraintNodeData extends Record<string, unknown> {
  nodeType: "constraint";
  ruleId: string;
  constraintIndex: number;
  constraint: PolicyV2RuleConstraint;
}

export interface ActionNodeData extends Record<string, unknown> {
  nodeType: "action";
  ruleId: string;
  action: PolicyV2Action;
  onDenialMessage?: string | null;
}

export type FlowNodeData =
  | StartNodeData
  | MatchNodeData
  | GateNodeData
  | ConstraintNodeData
  | ActionNodeData;

export type FlowNode = Node<FlowNodeData>;
export type FlowEdge = Edge;

export interface FlowState {
  nodes: FlowNode[];
  edges: FlowEdge[];
  selectedNodeId: string | null;
  isDirty: boolean;
}

export interface RuleLane {
  ruleId: string;
  ruleName: string;
  yOffset: number;
}

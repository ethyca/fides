import { NodeTypes } from "@xyflow/react";
import StartNode from "./StartNode";
import MatchNode from "./MatchNode";
import GateNode from "./GateNode";
import ConstraintNode from "./ConstraintNode";
import ActionNode from "./ActionNode";

// Export individual node components
export { StartNode, MatchNode, GateNode, ConstraintNode, ActionNode };

// Export nodeTypes registry for React Flow
export const nodeTypes: NodeTypes = {
  start: StartNode,
  match: MatchNode,
  gate: GateNode,
  constraint: ConstraintNode,
  action: ActionNode,
};

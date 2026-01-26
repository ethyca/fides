import { EdgeTypes } from "@xyflow/react";
import FlowEdge from "./FlowEdge";

// Export individual edge components
export { default as FlowEdgeComponent } from "./FlowEdge";

// Export edgeTypes registry for React Flow
export const edgeTypes: EdgeTypes = {
  flow: FlowEdge,
};

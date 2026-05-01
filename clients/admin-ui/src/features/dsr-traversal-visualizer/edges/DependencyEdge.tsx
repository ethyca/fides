import { Edge, EdgeProps, getBezierPath } from "@xyflow/react";

interface DependencyEdgeData extends Record<string, unknown> {
  dep_count?: number;
}

const DependencyEdge = (
  props: EdgeProps<Edge<DependencyEdgeData, "dependency">>,
) => {
  const {
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    markerEnd,
  } = props;
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  return (
    <path d={path} className="react-flow__edge-path" markerEnd={markerEnd} />
  );
};

export default DependencyEdge;

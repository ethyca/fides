import { Edge, EdgeProps, getBezierPath } from "@xyflow/react";

const GatesEdge = (props: EdgeProps<Edge<Record<string, unknown>, "gates">>) => {
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
    <path
      d={path}
      className="react-flow__edge-path"
      markerEnd={markerEnd}
      style={{ strokeDasharray: "6 4" }}
    />
  );
};

export default GatesEdge;

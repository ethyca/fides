import { Edge, EdgeProps, getBezierPath } from "@xyflow/react";

interface DependencyEdgeData extends Record<string, unknown> {
  dep_count?: number;
}

export const DependencyEdge = (
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
    animated,
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
      style={{
        stroke: "var(--fidesui-color-link)",
        strokeWidth: 2,
        opacity: animated ? 1 : 0,
        transition: "opacity 180ms ease",
      }}
    />
  );
};

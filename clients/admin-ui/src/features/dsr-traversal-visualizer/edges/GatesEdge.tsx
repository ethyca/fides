import { Edge, EdgeProps, getBezierPath } from "@xyflow/react";

export const GatesEdge = (
  props: EdgeProps<Edge<Record<string, unknown>, "gates">>,
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
      // eslint-disable-next-line tailwindcss/no-custom-classname
      className="react-flow__edge-path"
      markerEnd={markerEnd}
      style={{
        stroke: "var(--fidesui-color-warning)",
        strokeWidth: 2,
        strokeDasharray: "6 4",
        opacity: animated ? 1 : 0,
        transition: "opacity 180ms ease",
      }}
    />
  );
};

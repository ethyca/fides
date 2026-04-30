import { Edge, EdgeProps, getBezierPath } from "@xyflow/react";
import { Tag } from "fidesui";

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
    data,
  } = props;
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  return (
    <>
      <path
        d={path}
        className="react-flow__edge-path"
        markerEnd={markerEnd}
      />
      {data?.dep_count !== undefined && data.dep_count > 1 && (
        <foreignObject
          x={labelX - 16}
          y={labelY - 12}
          width={32}
          height={24}
          requiredExtensions="http://www.w3.org/1999/xhtml"
        >
          <Tag style={{ fontSize: 10, lineHeight: "16px" }}>
            {data.dep_count}
          </Tag>
        </foreignObject>
      )}
    </>
  );
};

export default DependencyEdge;

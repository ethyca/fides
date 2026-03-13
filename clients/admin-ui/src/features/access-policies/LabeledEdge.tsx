import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from "@xyflow/react";

interface LabeledEdgeData {
  label?: string;
}

const LabeledEdge = (props: EdgeProps) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
  } = props;

  const label = (data as LabeledEdgeData | undefined)?.label;
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge id={id} path={edgePath} />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
            className="nodrag nopan"
          >
            <span
              style={{
                fontSize: "var(--ant-font-size-sm)",
                fontWeight: 500,
                padding: "2px 8px",
                borderRadius: "var(--ant-border-radius)",
                backgroundColor: "var(--ant-color-bg-container)",
                border: "1px solid var(--ant-color-border)",
                color: "var(--ant-color-text-secondary)",
              }}
            >
              {label}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

export default LabeledEdge;

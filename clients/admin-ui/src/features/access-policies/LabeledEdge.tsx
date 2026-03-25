import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from "@xyflow/react";

import styles from "./LabeledEdge.module.scss";

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
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
            className={`nodrag nopan ${styles.labelWrapper}`}
          >
            <span className={styles.label}>{label}</span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

export default LabeledEdge;

import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Tooltip } from "fidesui";
import React, { useEffect, useState } from "react";
import palette from "fidesui/src/palette/palette.module.scss";

import { ExecutionGraphNode as ExecutionGraphNodeData } from "../types";
import {
  EXECUTION_GRAPH_STATUS_LABELS,
  isRootNode,
  isTerminatorNode,
} from "./execution-graph.constants";
import styles from "./ExecutionGraphNode.module.scss";

export type ExecutionGraphNodeType = Node<
  {
    graphNode: ExecutionGraphNodeData;
  },
  "executionGraphNode"
>;

function formatElapsed(updatedAt: string): string {
  const ms = Date.now() - new Date(updatedAt).getTime();
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

const ExecutionGraphNodeComponent = React.memo(({
  data,
}: NodeProps<ExecutionGraphNodeType>) => {
  const { graphNode } = data;
  const { status } = graphNode;
  const [elapsed, setElapsed] = useState(
    status === "executing" ? formatElapsed(graphNode.updated_at) : "",
  );

  useEffect(() => {
    if (status !== "executing") {
      return undefined;
    }
    const interval = setInterval(() => {
      setElapsed(formatElapsed(graphNode.updated_at));
    }, 1000);
    return () => clearInterval(interval);
  }, [status, graphNode.updated_at]);

  if (isTerminatorNode(graphNode.collection_address)) {
    return null;
  }

  const hasUpstream = graphNode.upstream_tasks.length > 0;
  const hasDownstream = graphNode.downstream_tasks.length > 0;
  const isRoot = isRootNode(graphNode.collection_address);

  if (isRoot) {
    return (
      <div className={styles.container}>
        <div className={`${styles.node} ${styles["node--root"]}`}>
          <span className={styles.label}>Identity</span>
        </div>
        {hasDownstream && (
          <Handle
            type="source"
            position={Position.Right}
            style={{
              width: 8,
              height: 8,
              backgroundColor: palette.FIDESUI_NEUTRAL_400,
            }}
          />
        )}
      </div>
    );
  }

  const statusLabel = EXECUTION_GRAPH_STATUS_LABELS[status] ?? status;

  const nodeContent = (
    <div className={styles.container}>
      <div className={`${styles.node} ${styles[`node--${status}`] || ""}`}>
        <span className={styles["dataset-label"]}>
          {graphNode.dataset_name}
        </span>
        <span className={styles.label}>{graphNode.collection_name}</span>

        <div className={styles["status-row"]}>
          <span
            className={`${styles["status-dot"]} ${styles[`status-dot--${status}`] || ""}`}
          />
          <span className={styles["status-text"]}>{statusLabel}</span>

          {status === "executing" && elapsed && (
            <span className={styles.elapsed}>{elapsed}</span>
          )}


        </div>

        {status === "error" && graphNode.message && (
          <span className={styles["error-message"]}>{graphNode.message}</span>
        )}
      </div>

      {hasUpstream && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            width: 8,
            height: 8,
            backgroundColor: palette.FIDESUI_NEUTRAL_400,
          }}
        />
      )}
      {hasDownstream && (
        <Handle
          type="source"
          position={Position.Right}
          style={{
            width: 8,
            height: 8,
            backgroundColor: palette.FIDESUI_NEUTRAL_400,
          }}
        />
      )}
    </div>
  );

  if (status === "error" && graphNode.message) {
    return (
      <Tooltip title={graphNode.message} placement="top">
        {nodeContent}
      </Tooltip>
    );
  }

  return nodeContent;
});

ExecutionGraphNodeComponent.displayName = "ExecutionGraphNodeComponent";

export default ExecutionGraphNodeComponent;

import { Handle, NodeProps, Position } from "@xyflow/react";
import React from "react";
import palette from "fidesui/src/palette/palette.module.scss";

import { EXECUTION_GRAPH_STATUS_LABELS } from "./execution-graph.constants";
import { DatasetGraphNodeType } from "./buildDatasetGraph";
import styles from "./DatasetGraphNode.module.scss";

const DatasetGraphNodeComponent = React.memo(
  ({ data }: NodeProps<DatasetGraphNodeType>) => {
    const {
      datasetName,
      status,
      totalCollections,
      completedCollections,
      errorCount,
      executingCount,
    } = data;

    const statusLabel = EXECUTION_GRAPH_STATUS_LABELS[status] ?? status;
    const progressPct =
      totalCollections > 0
        ? Math.round((completedCollections / totalCollections) * 100)
        : 0;

    let summary = `${completedCollections}/${totalCollections} complete`;
    if (errorCount > 0) {
      summary += `, ${errorCount} error`;
    }
    if (executingCount > 0) {
      summary += `, ${executingCount} running`;
    }

    return (
      <div className={styles.container}>
        <div className={`${styles.node} ${styles[`node--${status}`] || ""}`}>
          <span className={styles["dataset-name"]}>{datasetName}</span>

          <div className={styles["status-row"]}>
            <span
              className={`${styles["status-dot"]} ${styles[`status-dot--${status}`] || ""}`}
            />
            <span className={styles["status-text"]}>{statusLabel}</span>
          </div>

          <div className={styles["progress-bar"]}>
            <div
              className={styles["progress-fill"]}
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <span className={styles["progress-text"]}>{summary}</span>
        </div>

        <Handle
          type="target"
          position={Position.Left}
          style={{
            width: 8,
            height: 8,
            backgroundColor: palette.FIDESUI_NEUTRAL_400,
          }}
        />
        <Handle
          type="source"
          position={Position.Right}
          style={{
            width: 8,
            height: 8,
            backgroundColor: palette.FIDESUI_NEUTRAL_400,
          }}
        />
      </div>
    );
  },
);

DatasetGraphNodeComponent.displayName = "DatasetGraphNodeComponent";

export default DatasetGraphNodeComponent;

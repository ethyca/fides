import { Handle, NodeProps, Position } from "@xyflow/react";
import { AntButton as Button, AntTypography as Typography } from "fidesui";
import React from "react";

import styles from "./DatamapSystemNode.module.scss";

export type SystemNodeData = {
  label: string;
  description?: string;
};

const DatamapSystemNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as SystemNodeData;

  return (
    <div className={styles.container} data-testid="datamap-system-node">
      <Button
        className={`${styles.button} ${selected ? styles["button--selected"] : ""}`}
        type="text"
      >
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
      </Button>

      {/* Source handle (right) */}
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />

      {/* Target handle (left) */}
      <Handle
        type="target"
        position={Position.Left}
        className={styles.handle}
      />
    </div>
  );
};

export default DatamapSystemNode;

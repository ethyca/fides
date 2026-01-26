import React, { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { StartNodeData } from "../types";
import styles from "./nodeStyles.module.scss";

export type StartNodeType = Node<StartNodeData, "start">;

const StartNode = ({ data, selected }: NodeProps<StartNodeType>) => {
  return (
    <div
      className={`${styles.startNode} ${selected ? styles.selected : ""}`}
      data-testid="start-node"
    >
      <div className={styles.startIcon} />
      <span className={styles.startLabel}>{data.ruleName}</span>
      <Handle
        type="source"
        position={Position.Right}
        className={`${styles.handle} ${styles.handleSource}`}
      />
    </div>
  );
};

StartNode.displayName = "StartNode";

export default memo(StartNode);

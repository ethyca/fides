import React, { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { ActionNodeData } from "../types";
import styles from "./nodeStyles.module.scss";

export type ActionNodeType = Node<ActionNodeData, "action">;

const ActionNode = ({ data, selected }: NodeProps<ActionNodeType>) => {
  const isAllow = data.action === "ALLOW";

  return (
    <div
      className={`${styles.actionNode} ${selected ? styles.selected : ""}`}
      data-testid="action-node"
    >
      {/* Top accent bar */}
      <div
        className={isAllow ? styles.actionAccentAllow : styles.actionAccentDeny}
      />

      <Handle
        type="target"
        position={Position.Left}
        className={`${styles.handle} ${styles.handleTarget}`}
      />

      <div className={styles.actionInner}>
        <div
          className={isAllow ? styles.actionIconAllow : styles.actionIconDeny}
        >
          {isAllow ? "✓" : "✕"}
        </div>
        <div className={styles.actionBody}>
          <p
            className={
              isAllow ? styles.actionLabelAllow : styles.actionLabelDeny
            }
          >
            {data.action}
          </p>
          {data.onDenialMessage && (
            <p className={styles.actionMessage}>{data.onDenialMessage}</p>
          )}
        </div>
      </div>
    </div>
  );
};

ActionNode.displayName = "ActionNode";

export default memo(ActionNode);

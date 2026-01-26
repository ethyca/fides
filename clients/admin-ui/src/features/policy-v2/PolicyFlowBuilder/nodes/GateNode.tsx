import React, { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { GateNodeData } from "../types";
import styles from "./nodeStyles.module.scss";

export type GateNodeType = Node<GateNodeData, "gate">;

const GateNode = ({ data, selected }: NodeProps<GateNodeType>) => {
  return (
    <div
      className={`${styles.gateNode} ${selected ? styles.selected : ""}`}
      data-testid="gate-node"
    >
      {/* Multiple target handles for inputs */}
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        className={`${styles.gateHandle} ${styles.handleTarget}`}
        style={{ top: "50%", left: "-4px" }}
      />
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        className={`${styles.gateHandle}`}
        style={{ top: "-4px", left: "50%" }}
      />

      <div className={styles.gateContent}>{data.gateType}</div>

      {/* Single source handle for output */}
      <Handle
        type="source"
        position={Position.Right}
        className={`${styles.gateHandle} ${styles.handleSource}`}
        style={{ top: "50%", right: "-4px" }}
      />
    </div>
  );
};

GateNode.displayName = "GateNode";

export default memo(GateNode);

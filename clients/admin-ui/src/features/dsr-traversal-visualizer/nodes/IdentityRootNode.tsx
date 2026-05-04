import { Handle, Node, NodeProps, Position } from "@xyflow/react";

import { IdentityRootData } from "../types";
import styles from "./IdentityRootNode.module.scss";

export type IdentityRootNodeType = Node<IdentityRootData, "identityRoot">;

const IdentityRootNode = ({
  data,
}: NodeProps<Node<IdentityRootData, "identityRoot">>) => {
  const types = data.identity_types?.length
    ? data.identity_types.join(", ")
    : "No identity types";
  const formName = data.privacy_center_forms?.[0]?.name ?? "No form linked";
  return (
    <div className={styles.card} data-testid="identity-root-node">
      <div className={styles.header}>
        <span className={styles.icon}>ID</span>
        <span className={styles.title}>{types}</span>
      </div>
      <div className={styles.sub}>From: {formName}</div>
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};

export default IdentityRootNode;

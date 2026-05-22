import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import classNames from "classnames";
import { Flex, Text } from "fidesui";

import { IdentityRootData } from "../types";
import styles from "./IdentityRootNode.module.scss";

export type IdentityRootNodeType = Node<IdentityRootData, "identityRoot">;

export const IdentityRootNode = ({
  data,
}: NodeProps<Node<IdentityRootData, "identityRoot">>) => {
  const types = data.identity_types?.length
    ? data.identity_types.join(", ")
    : "No identity types";
  const formName = data.privacy_center_forms?.[0]?.name ?? "No form linked";
  return (
    <div
      className={classNames(
        styles.card,
        "relative w-[220px] box-border px-4 py-3",
      )}
      data-testid="identity-root-node"
    >
      <Flex align="center" gap="small">
        <span className={styles.icon}>ID</span>
        <Text strong className="min-w-0 flex-1" ellipsis={{ tooltip: types }}>
          {types}
        </Text>
      </Flex>
      <Text
        type="secondary"
        className={classNames(styles.sub, "block mt-1.5")}
        ellipsis={{ tooltip: `From: ${formName}` }}
      >
        From: {formName}
      </Text>
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};

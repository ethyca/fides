import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Tag, Text } from "fidesui";

import { IdentityRootData } from "../types";
import styles from "./IntegrationNode.module.scss";

export type IdentityRootNodeType = Node<IdentityRootData, "identityRoot">;

const IdentityRootNode = ({ data }: NodeProps<IdentityRootNodeType>) => (
  <div className={styles.node} data-testid="identity-root-node">
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.User size={16} />}
        className={styles.avatar}
      />
      <Text strong className={styles.headerLabel}>
        Identity
      </Text>
    </Flex>
    <div className={styles.body}>
      <Text type="secondary" className={styles.metaText}>
        Identity types
      </Text>
      <Flex gap={4} wrap className={styles.metaRow}>
        {data.identity_types.map((t) => (
          <Tag key={t} className={styles.tag}>
            {t}
          </Tag>
        ))}
      </Flex>
      {data.privacy_center_forms.length > 0 && (
        <>
          <Text type="secondary" className={styles.metaText}>
            Privacy center forms
          </Text>
          <Flex vertical className={styles.metaRow}>
            {data.privacy_center_forms.map((f) => (
              <Text key={f.id} className={styles.metaText}>
                {f.name}
              </Text>
            ))}
          </Flex>
        </>
      )}
    </div>
    <Handle
      type="source"
      position={Position.Right}
      className={styles.handle}
    />
  </div>
);

export default IdentityRootNode;

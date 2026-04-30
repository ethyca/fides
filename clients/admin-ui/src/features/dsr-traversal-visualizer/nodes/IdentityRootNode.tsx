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
      <Text strong style={{ flex: 1 }}>
        Identity
      </Text>
    </Flex>
    <div className={styles.body}>
      <Text type="secondary" style={{ fontSize: 12 }}>
        Identity types
      </Text>
      <Flex gap={4} wrap style={{ marginTop: 4, marginBottom: 8 }}>
        {data.identity_types.map((t) => (
          <Tag key={t} style={{ fontSize: 10 }}>
            {t}
          </Tag>
        ))}
      </Flex>
      {data.privacy_center_forms.length > 0 && (
        <>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Privacy center forms
          </Text>
          <Flex vertical style={{ marginTop: 4 }}>
            {data.privacy_center_forms.map((f) => (
              <Text key={f.id} style={{ fontSize: 12 }}>
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

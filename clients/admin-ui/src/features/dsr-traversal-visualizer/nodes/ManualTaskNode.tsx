import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import classNames from "classnames";
import { Avatar, Flex, Icons, Tag, Text } from "fidesui";

import { ManualTaskNodeData } from "../types";
import styles from "./ManualTaskNode.module.scss";

export type ManualTaskNodeType = Node<ManualTaskNodeData, "manualTask">;

export const ManualTaskNode = ({ data }: NodeProps<ManualTaskNodeType>) => {
  const primaryField = data.fields[0];
  const primaryLabel = primaryField?.label ?? primaryField?.name;
  const primaryHelp = primaryField?.help_text;
  const extraCount = Math.max(0, data.fields.length - 1);

  return (
    <div
      className={classNames(styles.node, "relative w-60 box-border")}
      data-testid={`manual-task-node:${data.id}`}
    >
      <Flex align="center" gap="small" className="px-4 py-3">
        <Avatar
          shape="square"
          size="small"
          icon={<Icons.Activity size={16} />}
          className={styles.avatar}
        />
        <Text
          strong
          className="min-w-0 flex-1"
          ellipsis={{ tooltip: data.name }}
        >
          {data.name}
        </Text>
      </Flex>
      <div className={classNames(styles.body, "px-4 py-3")}>
        {primaryLabel && (
          <Text
            className={styles.metaText}
            ellipsis={{ tooltip: primaryLabel }}
          >
            {primaryLabel}
          </Text>
        )}
        {primaryHelp && (
          <Text
            type="secondary"
            className={classNames(styles.miniText, "block mt-0.5")}
            ellipsis={{ tooltip: primaryHelp }}
          >
            {primaryHelp}
          </Text>
        )}
        {extraCount > 0 && (
          <Text
            type="secondary"
            className={classNames(styles.miniText, "block mt-1")}
          >
            +{extraCount} more field{extraCount === 1 ? "" : "s"}
          </Text>
        )}
        {data.conditions.length > 0 && (
          <div className="mt-1.5">
            <Tag color="warning" className={styles.tag}>
              {data.conditions.length} condition
              {data.conditions.length === 1 ? "" : "s"}
            </Tag>
          </div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};

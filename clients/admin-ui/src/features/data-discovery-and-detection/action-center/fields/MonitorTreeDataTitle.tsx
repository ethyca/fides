import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntSkeleton as Skeleton,
  AntText as Text,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";
import { Key } from "react";

import {
  MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO,
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_SKELETON_KEY_PREFIX,
} from "./MonitorFields.const";
import { CustomTreeDataNode, TreeNodeAction } from "./types";

const findNodeParent = (data: CustomTreeDataNode[], key: string) => {
  return data.find((node) => {
    const { children } = node;

    return children && !!children.find((child) => child.key.toString() === key);
  });
};

const recFindNodeParent = (
  data: CustomTreeDataNode[],
  key: string,
): CustomTreeDataNode | null => {
  return (
    findNodeParent(data, key) ??
    data.reduce(
      (agg, current) => {
        if (current.children) {
          return (
            findNodeParent(current.children, key) ??
            recFindNodeParent(current.children, key)
          );
        }
        return agg;
      },
      null as null | CustomTreeDataNode,
    )
  );
};

export type TreeNodeProps = {
  node: CustomTreeDataNode;
  treeData: CustomTreeDataNode[];
  onLoadMore: (key: string) => void;
  actions: Map<Key, TreeNodeAction>;
};

export const MonitorTreeDataTitle = ({
  node,
  treeData,
  onLoadMore,
  actions,
}: TreeNodeProps) => {
  if (!node.title) {
    return null;
  }

  if (node.key.toString().startsWith(TREE_NODE_LOAD_MORE_KEY_PREFIX)) {
    const nodeParent = recFindNodeParent(treeData, node.key.toString());

    return (
      <Button
        type="link"
        block
        onClick={() => {
          if (nodeParent?.key) {
            onLoadMore(nodeParent.key.toString());
          }
        }}
        className="p-0"
      >
        {node.title}
      </Button>
    );
  }

  if (node.key.toString().startsWith(TREE_NODE_SKELETON_KEY_PREFIX)) {
    return (
      <Skeleton paragraph={false} title={{ width: "80px" }} active>
        {node.title}
      </Skeleton>
    );
  }

  const statusInfo = node.status
    ? MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO[node.status]
    : null;

  return (
    <Flex gap={4} align="center">
      {statusInfo && (
        <Tooltip title={statusInfo.tooltip}>
          <Icons.CircleSolid
            className="size-2 min-w-min"
            style={{ color: statusInfo.color }}
          />
        </Tooltip>
      )}
      <Text ellipsis={{ tooltip: node.title }} className="flex-auto">
        {node.title}
      </Text>
      {[...actions.values()].some(
        ({ disabled = () => true }) => !disabled(node),
      ) && (
        <Dropdown
          menu={{
            items: actions
              ? [...actions.entries()].map(
                  ([key, { label, disabled = () => false }]) => ({
                    key,
                    label,
                    disabled: disabled(node),
                  }),
                )
              : [],
            onClick: ({ key }) => {
              actions.get(key)?.callback(node.key);
            },
          }}
        >
          <Button
            aria-label="Show More Resource Actions"
            icon={<Icons.OverflowMenuVertical />}
            type="text"
            size="small"
            className="self-end"
          />
        </Dropdown>
      )}
    </Flex>
  );
};

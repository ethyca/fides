import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntDropdownProps as DropdownProps,
  AntFlex as Flex,
  AntSkeleton as Skeleton,
  AntText as Text,
  Icons,
} from "fidesui";
import { Key, useState } from "react";

import {
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
  const [availableActions, setAvailableActions] = useState<Key[]>();
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
  const asyncGetActions: DropdownProps["onOpenChange"] = async (open) => {
    if (open && actions) {
      Promise.all(
        [...actions.entries()].map(async ([key, { disabled }]) => {
          const isDisabled = disabled ? await disabled(node) : true;
          return [key, isDisabled] as const;
        }),
      ).then((result) => {
        setAvailableActions(
          result.flatMap(([key, disabled]) => (disabled ? [] : [key])),
        );
      });
    }
  };

  return (
    /** TODO: migrate group class to semantic dom after upgrading ant */
    <Flex gap={4} align="center" className="group">
      <Text ellipsis={{ tooltip: node.title }} className="flex-auto">
        {node.title}
      </Text>
      <Dropdown
        menu={{
          items: actions
            ? [...actions.entries()].map(([key, { label }]) => ({
                key,
                label,
                disabled: !availableActions?.includes(key),
              }))
            : [],
          onClick: ({ key, domEvent }) => {
            domEvent.preventDefault();
            domEvent.stopPropagation();
            actions.get(key)?.callback(node.key, node);
          },
        }}
        onOpenChange={asyncGetActions}
        destroyOnHidden
        className="group"
      >
        <Button
          aria-label="Show More Resource Actions"
          icon={
            <Icons.OverflowMenuVertical className="opacity-0 group-hover:opacity-100 group-[.ant-dropdown-open]:opacity-100" />
          }
          type="text"
          size="small"
          className="self-end"
        />
      </Dropdown>
    </Flex>
  );
};

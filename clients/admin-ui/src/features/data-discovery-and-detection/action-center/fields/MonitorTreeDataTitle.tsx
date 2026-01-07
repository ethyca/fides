import { Button, Dropdown, Flex, Icons, Skeleton, Text } from "fidesui";

import { DiffStatus } from "~/types/api";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_SKELETON_KEY_PREFIX,
} from "./MonitorFields.const";
import { CustomTreeDataNode, NodeAction } from "./types";

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
  actions: Record<string, NodeAction<CustomTreeDataNode>>;
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

  const isMuted = node.diffStatus === DiffStatus.MUTED;

  return (
    /** TODO: migrate group class to semantic dom after upgrading ant */
    <Flex
      gap={4}
      align="center"
      className={`group ml-1 flex grow ${isMuted ? "opacity-40" : ""}`}
      aria-label={isMuted ? `${node.title} (ignored)` : undefined}
    >
      <Text ellipsis={{ tooltip: node.title }} className="grow select-none">
        {node.title}
      </Text>
      <Dropdown
        menu={{
          items: actions
            ? Object.entries(actions).map(([key, { disabled, ...rest }]) => ({
                key,
                disabled: disabled([node]),
                ...rest,
              }))
            : [],
          onClick: ({ key, domEvent }) => {
            domEvent.preventDefault();
            domEvent.stopPropagation();
            actions[key]?.callback([node.key], [node]);
          },
        }}
        destroyOnHidden
        className="group mr-1 flex-none group-[.multi-select]/monitor-tree:pointer-events-none group-[.multi-select]/monitor-tree:opacity-0"
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

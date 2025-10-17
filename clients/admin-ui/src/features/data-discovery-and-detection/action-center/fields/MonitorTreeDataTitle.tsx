import {
  AntButton as Button,
  AntFlex as Flex,
  AntSkeleton as Skeleton,
  AntText as Text,
  Icons,
} from "fidesui";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";

import { TreeResourceChangeIndicator } from "~/types/api";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_SKELETON_KEY_PREFIX,
} from "./MonitorFields.const";
import { CustomTreeDataNode } from "./types";

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
  return data.reduce(
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
  );
};

export const MonitorTreeDataTitle = ({
  node,
  treeData,
  onLoadMore,
}: {
  node: CustomTreeDataNode;
  treeData: CustomTreeDataNode[];
  onLoadMore: (key: string) => void;
}) => {
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

  const statusIconColor = (() => {
    switch (node.status) {
      case TreeResourceChangeIndicator.ADDITION:
        return palette.FIDESUI_SUCCESS;
      case TreeResourceChangeIndicator.REMOVAL:
        return palette.FIDESUI_ERROR;
      case TreeResourceChangeIndicator.CHANGE:
        return palette.FIDESUI_WARNING;
      default:
        return null;
    }
  })();

  return (
    <Flex gap={4} align="center" className="inline-flex">
      {statusIconColor && (
        <Icons.CircleSolid
          className="size-2"
          style={{ color: statusIconColor }}
        />
      )}
      <Text ellipsis={{ tooltip: node.title }}>{node.title}</Text>
    </Flex>
  );
};

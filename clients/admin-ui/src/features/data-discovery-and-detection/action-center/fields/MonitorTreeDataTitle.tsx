import {
  AntButton as Button,
  AntSkeleton as Skeleton,
  AntSpace as Space,
  AntText as Text,
  Icons,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { TreeResourceChangeIndicator } from "~/types/api";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_SKELETON_KEY_PREFIX,
} from "./MonitorFields.const";
import { CustomTreeDataNode as TreeDataNode } from "./MonitorTree";

const findNodeParent = (data: TreeDataNode[], key: string) => {
  return data.find((node) => {
    const { children } = node;
    return children && !!children.find((child) => child.key.toString() === key);
  });
};

const recFindNodeParent = (
  data: TreeDataNode[],
  key: string,
): TreeDataNode | null => {
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
    null as null | TreeDataNode,
  );
};

export const MonitorTreeDataTitle = ({
  node,
  treeData,
  onLoadMore,
}: {
  node: TreeDataNode;
  treeData: TreeDataNode[];
  onLoadMore: (key: string) => void;
}) => {
  if (node.key.toString().startsWith(TREE_NODE_LOAD_MORE_KEY_PREFIX)) {
    const nodeParent = recFindNodeParent(treeData, node.key.toString());
    return (
      <Button
        type="link"
        block
        onClick={() => {
          if (nodeParent?.key) {
            onLoadMore(nodeParent?.key.toString());
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
    <Space size={4}>
      {statusIconColor && (
        <Icons.CircleSolid
          className="size-2"
          style={{ color: statusIconColor }}
        />
      )}
      <Text ellipsis={{ tooltip: node.title }}>{node.title}</Text>
    </Space>
  );
};

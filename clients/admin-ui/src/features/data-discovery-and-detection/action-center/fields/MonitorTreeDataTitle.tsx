import {
  AntButton as Button,
  AntSkeleton as Skeleton,
  AntText as Text,
  AntTreeDataNode as TreeDataNode,
} from "fidesui";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_SKELETON_KEY_PREFIX,
} from "./MonitorFields.const";

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
        {typeof node.title === "function" ? node.title(node) : node.title}
      </Button>
    );
  }

  if (node.key.toString().startsWith(TREE_NODE_SKELETON_KEY_PREFIX)) {
    return (
      <Skeleton paragraph={false} title={{ width: "80px" }} active>
        {typeof node.title === "function" ? node.title(node) : node.title}
      </Skeleton>
    );
  }

  return (
    <Text
      ellipsis={{
        tooltip:
          typeof node.title === "function" ? node.title(node) : node.title,
      }}
    >
      {typeof node.title === "function" ? node.title(node) : node.title}
    </Text>
  );
};

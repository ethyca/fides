import { TreeProps } from "fidesui";
import { Key } from "react";

import { CursorPaginationState } from "~/features/common/pagination";
import { DEFAULT_PAGE_SIZE } from "~/features/common/table/constants";

import { AsyncTreeNode } from "./types";

export const TREE_NODE_LOAD_MORE_KEY_PREFIX = "";
export const TREE_NODE_SKELETON_KEY_PREFIX = "";

export const ROOT_NODE_KEY = "ROOT_NODE";

export const DEFAULT_ROOT_NODE: AsyncTreeNode & CursorPaginationState = {
  key: ROOT_NODE_KEY,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
};

export const DEFAULT_ROOT_NODE_STATE: {
  keys: Key[];
  nodes: Array<AsyncTreeNode & CursorPaginationState>;
} = {
  keys: [ROOT_NODE_KEY],
  nodes: [DEFAULT_ROOT_NODE],
};

export const DEFAULT_TREE_PROPS: TreeProps = {
  showIcon: true,
  showLine: true,
  blockNode: true,
  multiple: true,
  expandAction: "doubleClick",
};

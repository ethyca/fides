import { Key, } from "react";

import { DEFAULT_PAGE_SIZE } from "~/features/common/table/constants";
import { AsyncTreeNode } from "./types";
import { PaginationState } from "~/features/common/pagination";

export const TREE_NODE_LOAD_MORE_KEY_PREFIX = ''
export const TREE_NODE_SKELETON_KEY_PREFIX = ''

export const ROOT_NODE_KEY = "ROOT_NODE";

export const DEFAULT_ROOT_NODE: AsyncTreeNode & PaginationState = {
  key: ROOT_NODE_KEY,
  pageIndex: 0,
  pageSize: DEFAULT_PAGE_SIZE
}

export const DEFAULT_ROOT_NODE_STATE: {
  keys: Key[],
  nodes: Array<AsyncTreeNode & PaginationState>
} = {
  keys: [ROOT_NODE_KEY], nodes: [DEFAULT_ROOT_NODE]
}


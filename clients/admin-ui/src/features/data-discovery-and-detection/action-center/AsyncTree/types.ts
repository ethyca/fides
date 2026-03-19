import { TreeDataNode, TreeProps } from "fidesui";
import { Key } from "react";

import {
  CursorPaginatedResponse,
  CursorPaginationQueryParams,
} from "~/features/common/pagination";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[];
};

type ATreeDataNode = Omit<TreeDataNode, "children" | "key">;

export type AsyncTreeNode<T extends ATreeDataNode = ATreeDataNode> =
  ReactDataNode<T> &
    Omit<CursorPaginatedResponse<T>, "items"> & {
      parent?: Key;
      actions?: ActionDict;
    };

export type Plural = [string, string];

export interface InternalTreeProps<T extends AsyncTreeNode = AsyncTreeNode>
  extends Omit<TreeProps<T>, "loadData" | "treeData"> {
  loadData: (
    pagination: CursorPaginationQueryParams,
    key?: Key,
  ) => Promise<CursorPaginatedResponse<TreeDataNode> | undefined>;
  refreshData: (
    key?: Key,
    childKeys?: Key[],
  ) => Promise<CursorPaginatedResponse<TreeDataNode> | undefined>;
  queryKeys?: Key[];
  actions?: TreeActions<ActionDict>;
  pageSize?: number;
  loadMoreText?: string;
  showFooter?: boolean;
  taxonomy?: Plural;
}

export type AsyncTreeProps = Omit<TreeProps, "loadData"> & {
  pageSize?: number;
  actions?: TreeActions<ActionDict>;
  loadMoreText?: string;
  showFooter?: boolean;
  taxonomy?: Plural;
  loadData: (
    pagination: CursorPaginationQueryParams,
    key?: Key,
  ) => Promise<CursorPaginatedResponse<TreeDataNode> | undefined>;
};

export type AsyncTreeNodeComponentProps = {
  node: AsyncTreeNode;
  actions?: ActionDict;
  refreshCallback?: (key: Key) => void;
};

export type ParentMapNode = Omit<CursorPaginatedResponse<unknown>, "items"> & {
  key: Key;
  parent?: Key;
  children: Key[];
};

type LeafMapNode = {
  key: Key;
  parent?: Key;
};

export type MapNode = ParentMapNode | LeafMapNode;

export interface ActionDict<N extends AsyncTreeNode = AsyncTreeNode>
  extends Record<string, NodeAction<N>> {}

export type TreeActions<AD extends ActionDict> = {
  nodeActions: AD;
  primaryAction: keyof AD;
};

export type NodeAction<N> = {
  label: string;
  /** TODO: should be generically typed * */
  callback: (keys: Key[], nodes: N[]) => Promise<void>;
  disabled: (nodes: N[]) => boolean;
};

export type TreeNodeAction = NodeAction<AsyncTreeNode>;

import { Key } from 'react'
import { TreeDataNode, TreeProps } from "fidesui"

import { PaginatedResponse, PaginationQueryParams } from "~/types/query-params";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[];
};

export type AsyncTreeNode = Omit<PaginatedResponse<unknown>, 'items'> & ReactDataNode<TreeDataNode> & {
  parent?: Key;
}

export type Plural = [string, string]

export type AsyncTreeProps = Omit<TreeProps, "loadData"> & {
  pageSize?: number;
  actions: TreeActions<ActionDict>,
  loadMoreText?: string,
  showFooter?: boolean,
  taxonomy?: Plural,
  loadData: (
    pagination: PaginationQueryParams,
    key?: Key,
  ) => Promise<PaginatedResponse<TreeDataNode> | undefined>;
};

export type AsyncTreeNodeComponentProps = {
  node: AsyncTreeNode;
  actions: ActionDict;
};

export type ParentMapNode = Omit<PaginatedResponse<unknown>, 'items'> & {
  key: Key;
  parent?: Key,
  children: Key[];
}

type LeafMapNode = {
  key: Key;
  parent?: Key,
}

export type MapNode = ParentMapNode | LeafMapNode

export type ActionDict = Record<string, NodeAction<AsyncTreeNode>>

export type TreeActions<AD extends ActionDict> = {
  nodeActions: AD;
  primaryAction: keyof AD;
}

export type NodeAction<N> = {
  label: string;
  /** TODO: should be generically typed * */
  callback: (keys: Key[], nodes: N[]) => void;
  disabled: (nodes: N[]) => boolean;
};

export type TreeNodeAction = NodeAction<AsyncTreeNode>;

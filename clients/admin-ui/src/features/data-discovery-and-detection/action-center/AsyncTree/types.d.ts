import { TreeDataNode } from "fidesui"
import { PaginatedResponse, PaginationQueryParams } from "~/types/query-params";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[];
};

export type AsyncTreeNode = Omit<PaginatedResponse, 'items'> & ReactDataNode<TreeDataNode> & {
  parent?: Key;
}

export type AsyncTreeProps = Omit<TreeProps, "loadData"> & {
  pageSize?: number;
  actions: TreeActions<TreeNodeAction, ActionDict<TreeNodeAction>>,
  loadMoreText?: string,
  loadData: (
    pagination: PaginationQueryParams,
    key?: Key,
  ) => Promise<PaginatedResponse<TreeDataNode> | undefined>;
};

export type AsyncTreeNodeComponentProps = {
  node: AsyncTreeNode;
  actions: ActionDict;
};

export type ParentMapNode = Omit<PaginatedResponse, 'items'> & {
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

export interface TreeActions<Action, AD extends ActionDict<Action>> {
  nodeActions: AD;
  primaryAction: keyof AD;
}

export type NodeAction<N extends ReactDataNode> = {
  label: string;
  /** TODO: should be generically typed * */
  callback: (key: Key[], nodes: N[]) => void;
  disabled: (nodes: N[]) => boolean;
};

export type TreeNodeAction = NodeAction<CustomTreeDataNode>;

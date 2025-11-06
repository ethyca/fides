import {AntTreeDataNode as TreeDataNode } from "fidesui" 
import { PaginatedResponse } from "~/types/query-params";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[];
};

export type AsyncTreeNode = ReactDataNode<TreeDataNode> & {
  parent?: Key;
}

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

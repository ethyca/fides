import { Tree, TreeProps, TreeDataNode } from "fidesui";
import { Key, useEffect, useState } from "react";

import { PaginationState } from "~/features/common/pagination";
import { DEFAULT_PAGE_SIZE } from "~/features/common/table/constants";
import { PaginatedResponse, PaginationQueryParams } from "~/types/query-params";

import { AsyncTreeNode, MapNode, ParentMapNode } from "./types";

export type AsyncTreeProps = Omit<TreeProps, "loadData"> & {
  pageSize?: number;
  loadData: (
    pagination: PaginationQueryParams,
    key?: Key,
  ) => Promise<PaginatedResponse<TreeDataNode> | undefined>;
};

const ROOT_NODE_KEY = "ROOT_NODE";

export const AsyncTree = ({
  pageSize = DEFAULT_PAGE_SIZE,
  ...props
}: AsyncTreeProps) => {

  /* Storing lookup data as normalized nodes */
  const [asyncNodes, setAsyncNodes] = useState<
    Map<Key, AsyncTreeNode & PaginationState>
  >(new Map());

  /* Mapping of nodes for tree traversal */
  const [nodeMap, setNodeMap] = useState<
    Map<Key, AsyncTreeNode & PaginationState>
  >(new Map());

  const [expandedKeys, setExpandedKeys] = useState<Key[]>([]);

  const recBuildTree = (node: TreeDataNode): TreeDataNode => ({
    ...node,
    children: Array.from(asyncNodes?.values())?.flatMap(
      (child) => child.parent === node.key ? [recBuildTree(child)] : []
    )
  });

  /* Building tree from async data */
  const rootNode = asyncNodes?.get(ROOT_NODE_KEY)
  const treeData: TreeProps["treeData"] = rootNode ? [recBuildTree(rootNode)] : []



  // /**
  //  * Handles tree expansion - if a node without children is being expanded, load its data
  //  */
  // const onExpand = (
  //   newExpandedKeys: Key[],
  //   info: { expanded: boolean; node: AsyncTreeNode },
  // ) => {
  //   setExpandedKeys(newExpandedKeys);
  //
  // };

  // const onSelect = (
  //   _: Key[],
  //   info: { selectedNodes: CustomTreeDataNode[] },
  // ) => {
  //   const classifyableKeys = info.selectedNodes
  //     .filter((node) => node.classifyable)
  //     .map((node) => node.key);
  //   setSelectedNodeKeys(classifyableKeys);
  // };
  const _loadData = (key?: Key) => {
    return new Promise(async (resolve) => {
      const node = asyncNodes.get(key ?? ROOT_NODE_KEY);
      console.log(node)
      const result = await props.loadData(
        { page: node?.pageIndex ?? 1, size: pageSize },
        key,
      );

      const mapNodes: MapNode[] = result ? result.items.map((item) => ({ key: item.key, parent: key })) : []
      const dataNodes = result ? result.items.map((item) => ({ ...item })) : []
      const newAsyncNodes = dataNodes.flatMap(
        (n) => n.key ? [[n.key, n] as const] : []
      )

      const parentNode = result?.items ? {
        key: key,
        children: result?.items.map((item) => item.key),

      } : {
        key: key
      }

      setAsyncNodes(
        new Map(
          [
            ...asyncNodes, ...newAsyncNodes
          ]
        )
          .set(key ?? ROOT_NODE_KEY, parentNode),
      );
      resolve(result);
    });
  };

  const loadData: TreeProps["loadData"] = (args) => _loadData(args.key);

  const onExpand: TreeProps["onExpand"] = (args) => {
    return new Promise(async (resolve) => {
      const expandResult = args.map(async (key) => {
        const result = await _loadData(key)
        return result
      })
      resolve(expandResult)
    });
  };

  useEffect(() => {
    const initialize = async () => {
      await _loadData();
    };
    initialize();
  }, []);

  return (
    <Tree.DirectoryTree
      {...props}
      loadData={loadData}
      treeData={treeData}
      expandedKeys={expandedKeys}
      onExpand={onExpand}
      // onSelect={onSelect}
      showIcon
      showLine
      blockNode
      rootClassName="h-full overflow-x-hidden"
    />
  );
};

export default AsyncTree;

import { Key, useEffect, useState } from "react";

import { Tree, TreeProps, TreeDataNode } from "fidesui";
import _ from "lodash";

import { PaginationState } from "~/features/common/pagination";
import { DEFAULT_PAGE_SIZE } from "~/features/common/table/constants";
import { AsyncTreeNode, AsyncTreeProps } from "./types";
import { ROOT_NODE_KEY, DEFAULT_ROOT_NODE, DEFAULT_ROOT_NODE_STATE } from './const'
import { AsyncTreeDataLink } from "./AsyncTreeLinkNode";
import { AsyncTreeDataTitle } from "./AsyncNodeTitle";

export const AsyncTree = ({
  pageSize = DEFAULT_PAGE_SIZE,
  loadMoreText = "Load More",
  actions,
  ...props
}: AsyncTreeProps) => {
  /* Storing lookup data as normalized nodes */
  const [asyncNodes, _setAsyncNodes] = useState<{
    keys: Key[],
    nodes: Array<AsyncTreeNode & PaginationState>
  }>(DEFAULT_ROOT_NODE_STATE);

  const setAsyncNodes = (nodes: Array<AsyncTreeNode & PaginationState>) => {
    _setAsyncNodes({
      keys: nodes.flatMap(({ key }) => key),
      nodes
    })
  }

  const updateAsyncNodes = (next: Array<AsyncTreeNode & PaginationState>) => {
    _setAsyncNodes((prev) => {
      const nextKeys = _.uniq([
        ...(prev?.nodes ?? []),
        ...next
      ].flatMap(({ key }) => key))

      return {
        keys: nextKeys,
        nodes: nextKeys.flatMap((nextKey) => {
          const target = next.find(({ key }) => nextKey === key) ??
            prev?.nodes.find(({ key }) => nextKey === key)

          return target ? [target] : []
        }
        )
      }
    }
    )
  }

  const [expandedKeys, setExpandedKeys] = useState<Key[]>([]);

  /**
   * @description This is the heart of the component that builds the tree data from our async state
   */
  const recBuildTree = (node: AsyncTreeNode): TreeDataNode => ({
    ...node,
    children: [
      ...asyncNodes?.nodes?.flatMap(
        (child) => child.parent === node.key ? [recBuildTree(child)] : []
      ),
      ...(node.total > node.pageIndex * node.pageSize ?
        [{
          key: `SHOW_MORE__${node.key}`,
          title: () => <AsyncTreeDataLink
            node={{ ...node, title: loadMoreText }}
            buttonProps={{ onClick: () => _loadData(node.key) }}
          />,
          icon: () => null,
          isLeaf: true
        }] :
        [])
    ]
  });

  /**
  * @description initiates the tree construction
  */
  const treeData: TreeProps["treeData"] = recBuildTree(
    asyncNodes.nodes.find(({ key }) => key === ROOT_NODE_KEY) ??
    DEFAULT_ROOT_NODE
  ).children

  const _loadData = (key?: Key) => {
    return new Promise(async (resolve) => {
      const node = asyncNodes?.nodes.find((node) => node.key === (key ?? ROOT_NODE_KEY));
      const pageIndex = (node?.pageIndex ?? 0) + 1

      const result = await props.loadData(
        { page: pageIndex, size: pageSize },
        key,
      );

      const dataNodes = result?.items.flatMap((dn) => ([{
        ...dn,
        title: () => <AsyncTreeDataTitle node={dn} actions={actions.nodeActions} />,
        parent: key ?? ROOT_NODE_KEY,
        pageIndex: 0,
        pageSize,
        
      }])) ?? []

      updateAsyncNodes([
        ...dataNodes,
        ...(node ? [{ // update parent node's pagination
          ...node,
          pageIndex,
          pageSize,
          total: result?.total
        }] : [])
      ])
      resolve(result);
    });
  };

  const loadData: TreeProps["loadData"] = (args) => _loadData(args.key);

  useEffect(() => {
    const initialize = async () => await _loadData();
    initialize();

    return () => setAsyncNodes(DEFAULT_ROOT_NODE.nodes)
  }, []);

  return <Tree.DirectoryTree
    {...props}
    loadData={loadData}
    treeData={treeData}
    expandedKeys={expandedKeys}
    onExpand={(newExpandedKeys) => setExpandedKeys(newExpandedKeys)}
    // onSelect={onSelect}
    showIcon
    showLine
    blockNode
    rootClassName="h-full overflow-x-hidden"
    expandAction="doubleClick"
  />
};

export default AsyncTree;

/* eslint-disable react/no-unstable-nested-components */
import { Spin, Tree, TreeDataNode, TreeProps } from "fidesui";
import _ from "lodash";
import { Key, useCallback, useEffect, useRef, useState } from "react";

import {
  CursorPaginatedResponse,
  CursorPaginationState,
} from "~/features/common/pagination";
import { DEFAULT_PAGE_SIZE } from "~/features/common/table/constants";

import { AsyncTreeDataTitle } from "./AsyncNodeTitle";
import { AsyncTreeFooter } from "./AsyncTreeFooter";
import { AsyncTreeDataLink } from "./AsyncTreeLinkNode";
import {
  DEFAULT_ROOT_NODE,
  DEFAULT_ROOT_NODE_STATE,
  DEFAULT_TREE_PROPS,
  ROOT_NODE_KEY,
} from "./const";
import { AsyncTreeNode, InternalTreeProps } from "./types";

const DEFAULT_NODE_PAGINATION_PROPS = {
  cursor: undefined,
  total: 0,
} as const;

export const AsyncTree = ({
  pageSize = DEFAULT_PAGE_SIZE,
  loadMoreText = "Load More",
  showFooter = false,
  taxonomy = ["item", "items"],
  actions,
  selectedKeys,
  loadData,
  refreshData,
  queryKeys,
  ...props
}: InternalTreeProps) => {
  /* Storing lookup data as normalized nodes */
  const [asyncNodes, rawSetAsyncNodes] = useState<{
    keys: Key[];
    nodes: Array<AsyncTreeNode & CursorPaginationState>;
  }>(DEFAULT_ROOT_NODE_STATE);
  const asyncNodesRef = useRef<typeof asyncNodes>();
  const [expandedKeys, setExpandedKeys] = useState<Key[]>([]);

  useEffect(() => {
    asyncNodesRef.current = asyncNodes;
  });

  const setAsyncNodes = (
    nodes: Array<AsyncTreeNode & CursorPaginationState>,
  ) => {
    rawSetAsyncNodes({
      keys: nodes.flatMap(({ key }) => key),
      nodes,
    });
  };

  const removeAsyncNodes = (keys: Key[]) => {
    rawSetAsyncNodes((prev) => {
      const nextKeys = _.difference(prev?.keys ?? [], keys);

      return {
        keys: nextKeys,
        nodes: nextKeys.flatMap((nextKey) => {
          const target = prev.nodes.find(({ key }) => nextKey === key);

          return target ? [target] : [];
        }),
      };
    });
    setExpandedKeys((prev) => _.difference(prev, keys));
  };

  const updateAsyncNodes = (
    next: Array<AsyncTreeNode & CursorPaginationState>,
  ) => {
    rawSetAsyncNodes((prev) => {
      const nextKeys = _.uniq(
        [...(prev?.nodes ?? []), ...next].flatMap(({ key }) => key),
      );

      return {
        keys: nextKeys,
        nodes: nextKeys.flatMap((nextKey) => {
          const target =
            next.find(({ key }) => nextKey === key) ??
            prev?.nodes.find(({ key }) => nextKey === key);

          return target ? [target] : [];
        }),
      };
    });
  };

  const handleRefresh = useCallback(
    (
      parentNode: TreeDataNode,
      refreshedNodeKeys: Key[],
      callback: (keys?: Key[]) => void,
      resetPaginationNodes?: CursorPaginatedResponse<TreeDataNode>,
      refreshedNodes?: CursorPaginatedResponse<TreeDataNode>,
    ) => {
      const foundKeys =
        refreshedNodes?.items?.map(({ key }) => key.toString()) ?? [];
      const keysToRemove = _.difference(refreshedNodeKeys, foundKeys);
      removeAsyncNodes(keysToRemove);

      const dataNodes =
        [
          ...(resetPaginationNodes?.items ?? []),
          ...(refreshedNodes?.items ?? []),
        ]?.flatMap((dn) => [
          {
            ...dn,
            title: () => (
              <AsyncTreeDataTitle
                node={{
                  ...dn,
                  parent: parentNode.key ?? ROOT_NODE_KEY,
                  ...DEFAULT_NODE_PAGINATION_PROPS,
                }}
                actions={actions?.nodeActions}
                refreshCallback={(key) => callback([key])}
              />
            ),
            parent: parentNode.key ?? ROOT_NODE_KEY,
            next_page: asyncNodes.nodes.find(
              (existingNode) => dn.key === existingNode.key,
            )?.next_page,
            ...DEFAULT_NODE_PAGINATION_PROPS,
            pageSize,
          },
        ]) ?? [];
      updateAsyncNodes([
        ...dataNodes,
        ...(parentNode
          ? [
              {
                ...parentNode,
                pageSize,
                total: resetPaginationNodes?.total ?? 0,
                current_page: resetPaginationNodes?.current_page,
                next_page: resetPaginationNodes?.next_page,
              },
            ]
          : []),
      ]);
    },
    [actions?.nodeActions, asyncNodes.nodes, pageSize],
  );

  const refreshCallback = useCallback(
    (keys?: Key[]) => {
      const refreshingNodes = keys
        ? asyncNodesRef.current?.nodes.flatMap((node) =>
            keys.includes(node.key) ? [node] : [],
          )
        : asyncNodesRef.current?.nodes;

      // const relatedNodes = refreshingNodes.reduce((agg, current) => {
      //   const parentNode = asyncNodes.nodes.find((n) => n.key === current.parent)
      //   return [
      //     ...agg,
      //     ...(parentNode ? [parentNode] : [])
      //   ]
      // }, [] as typeof refreshingNodes)
      updateAsyncNodes(
        refreshingNodes?.map((node) => ({
          ...node,
          icon: <Spin size="small" />,
        })) ?? [],
      );

      const refresh = async (
        node: TreeDataNode,
        parentKey: string,
        childKeys: string[],
      ) => {
        const resolvedParentKey =
          parentKey === ROOT_NODE_KEY ? undefined : parentKey;
        await Promise.all([
          refreshData(resolvedParentKey, childKeys),
          loadData({ size: pageSize }, resolvedParentKey),
        ]).then(([refreshedNodes, resetPaginationNodes]) => {
          handleRefresh(
            node,
            childKeys,
            refreshCallback,
            resetPaginationNodes,
            refreshedNodes,
          );
        });
      };

      const parentNodes = asyncNodesRef.current?.nodes.flatMap((node) =>
        asyncNodesRef.current?.nodes.some(({ parent }) => parent === node.key)
          ? [node]
          : [],
      );
      parentNodes?.map((node) =>
        refresh(
          node,
          node.key.toString(),
          refreshingNodes?.flatMap((child) =>
            child.parent === node.key ? [child.key.toString()] : [],
          ) ?? [],
        ),
      );
    },
    [handleRefresh, loadData, pageSize, refreshData],
  );

  const rawLoadData = (key?: Key) => {
    return new Promise((resolve) => {
      const asyncNode = asyncNodes?.nodes.find(
        (node) => node.key === (key ?? ROOT_NODE_KEY),
      );
      loadData({ cursor: asyncNode?.next_page, size: pageSize }, key).then(
        (result) => {
          const dataNodes =
            result?.items?.flatMap((dn) => [
              {
                ...dn,
                title: () => (
                  <AsyncTreeDataTitle
                    node={{
                      ...dn,
                      parent: key ?? ROOT_NODE_KEY,
                      ...DEFAULT_NODE_PAGINATION_PROPS,
                    }}
                    actions={actions?.nodeActions}
                    refreshCallback={(k) => refreshCallback([k])}
                  />
                ),
                parent: key ?? ROOT_NODE_KEY,
                ...DEFAULT_NODE_PAGINATION_PROPS,
                pageSize,
              },
            ]) ?? [];

          updateAsyncNodes([
            ...dataNodes,
            ...(asyncNode
              ? [
                  {
                    // update parent node's pagination
                    ...asyncNode,
                    pageSize,
                    total: result?.total ?? 0,
                    current_page: result?.current_page,
                    next_page: result?.next_page,
                  },
                ]
              : []),
          ]);

          resolve(result);
        },
      );
    });
  };

  /**
   * @description This is the heart of the component that builds the tree data from our async state
   */
  const recBuildTree = (node: AsyncTreeNode): TreeDataNode => ({
    ...node,
    children: [
      ...(asyncNodes?.nodes
        ?.flatMap((child) =>
          child.parent === node.key ? [recBuildTree(child)] : [],
        )
        .sort((a, b) => a.key.toString().localeCompare(b.key.toString())) ??
        []),
      ...(node.next_page
        ? [
            {
              key: `SHOW_MORE__${node.key}`,
              title: () => (
                <AsyncTreeDataLink
                  node={{ ...node, title: loadMoreText, disabled: false }}
                  buttonProps={{ onClick: () => rawLoadData(node.key) }}
                />
              ),
              selectable: false,
              icon: () => null,
              isLeaf: true,
            },
          ]
        : []),
    ],
  });

  /**
   * @description initiates the tree construction
   */
  const treeData: TreeProps["treeData"] = recBuildTree(
    asyncNodes.nodes.find(({ key }) => key === ROOT_NODE_KEY) ??
      DEFAULT_ROOT_NODE,
  ).children;

  const antLoadData: TreeProps["loadData"] = (args) => rawLoadData(args.key);

  useEffect(() => {
    refreshCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(queryKeys)]);

  useEffect(() => {
    const initialize = async () => rawLoadData();
    initialize();

    return () => {
      setAsyncNodes([DEFAULT_ROOT_NODE]);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Tree.DirectoryTree
        {...DEFAULT_TREE_PROPS}
        {...props}
        loadData={antLoadData}
        treeData={treeData}
        loadedKeys={expandedKeys}
        expandedKeys={expandedKeys}
        onExpand={(newExpandedKeys) => {
          setExpandedKeys(newExpandedKeys);
        }}
        selectedKeys={selectedKeys}
      />
      {showFooter ? (
        <AsyncTreeFooter
          selectedKeys={selectedKeys ?? []}
          actions={{
            nodeActions: actions?.nodeActions
              ? Object.fromEntries(
                  Object.entries(actions.nodeActions).map(([key, action]) => {
                    const selectedNodes = selectedKeys?.flatMap(
                      (selectedKey) => [
                        asyncNodes.nodes.find((an) => an.key === selectedKey),
                      ],
                    );
                    const selectedNodeDisabledActions = selectedNodes?.reduce(
                      (agg, current) => {
                        const disabledActions = current?.actions
                          ? Object.entries(current.actions)?.flatMap(() =>
                              action.disabled?.([current]) ? [key] : [],
                            )
                          : [];
                        return _.uniq([...agg, ...disabledActions]);
                      },
                      [] as Array<Key>,
                    );

                    return [
                      key,
                      {
                        ...action,
                        disabled: () =>
                          selectedNodeDisabledActions?.includes(key) ?? false,
                      },
                    ];
                  }),
                )
              : {},
            primaryAction: actions?.primaryAction ?? "",
          }}
          taxonomy={taxonomy}
        />
      ) : null}
    </>
  );
};

export default AsyncTree;

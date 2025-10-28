import {
  AntButton as Button,
  AntFlex as Flex,
  AntTitle as Title,
  AntTree as Tree,
  SparkleIcon,
} from "fidesui";
import { useRouter } from "next/router";
import {
  forwardRef,
  Key,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { PaginationState } from "~/features/common/pagination";
import {
  useLazyGetMonitorTreeAncestorsStatusesQuery,
  useLazyGetMonitorTreeQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  Page_DatastoreStagedResourceTreeAPIResponse_,
  StagedResourceTypeValue,
} from "~/types/api";

import {
  MAP_DATASTORE_RESOURCE_TYPE_TO_ICON,
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_LOAD_MORE_TEXT,
  TREE_NODE_SKELETON_KEY_PREFIX,
  TREE_PAGE_SIZE,
} from "./MonitorFields.const";
import { MonitorTreeDataTitle } from "./MonitorTreeDataTitle";
import {
  collectAllDescendantUrns,
  findNodeByUrn,
  removeChildrenFromNode,
  updateNodeStatus,
} from "./treeUtils";
import { CustomTreeDataNode } from "./types";

const mapResponseToTreeData = (
  data: Page_DatastoreStagedResourceTreeAPIResponse_,
  key?: string,
): CustomTreeDataNode[] => {
  const dataItems: CustomTreeDataNode[] = data.items.map((treeNode) => {
    const IconComponent = treeNode.resource_type
      ? MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
          treeNode.resource_type as StagedResourceTypeValue
        ]
      : undefined;
    return {
      title: treeNode.name,
      key: treeNode.urn,
      selectable: true, // all nodes are selectable since we ignore lowest level descendants in the data
      icon: IconComponent
        ? () => <IconComponent className="h-full" />
        : undefined,
      status: treeNode.update_status,
      isLeaf: !treeNode.has_grandchildren,
    };
  });

  return (dataItems?.length ?? 0) < TREE_PAGE_SIZE
    ? dataItems
    : [
        ...dataItems,
        {
          title: TREE_NODE_LOAD_MORE_TEXT,
          key: `${TREE_NODE_LOAD_MORE_KEY_PREFIX}-${data.page}-${key}`,
          selectable: false,
          isLeaf: true,
        },
      ];
};

const appendTreeNodeData = (
  list: CustomTreeDataNode[],
  key: React.Key,
  children: CustomTreeDataNode[],
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      return {
        ...node,
        children: [
          ...(node.children?.filter(
            (child) =>
              !(
                child.key
                  .toString()
                  .startsWith(TREE_NODE_LOAD_MORE_KEY_PREFIX) ||
                child.key.toString().startsWith(TREE_NODE_SKELETON_KEY_PREFIX)
              ),
          ) ?? []),
          ...children,
        ],
      };
    }
    if (node.children) {
      return {
        ...node,
        children: appendTreeNodeData(node.children, key, children),
      };
    }

    return node;
  });

const updateTreeData = (
  list: CustomTreeDataNode[],
  key: React.Key,
  children: CustomTreeDataNode[],
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      return {
        ...node,
        children,
      };
    }
    if (node.children) {
      return {
        ...node,
        children: updateTreeData(node.children, key, children),
      };
    }

    return node;
  });

/**
 * Merges new children into existing children by updating nodes with matching keys.
 * Used when the detailed query returns to update nodes that were initially added by the fast query.
 */
const mergeTreeNodeData = (
  list: CustomTreeDataNode[],
  key: React.Key,
  newChildren: CustomTreeDataNode[],
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      const existingChildren = node.children ?? [];

      // Filter out skeleton and load more nodes
      const filteredChildren = existingChildren.filter(
        (child) =>
          !(
            child.key.toString().startsWith(TREE_NODE_LOAD_MORE_KEY_PREFIX) ||
            child.key.toString().startsWith(TREE_NODE_SKELETON_KEY_PREFIX)
          ),
      );

      // Create maps for efficient O(1) lookups
      const newChildrenMap = new Map(
        newChildren.map((child) => [child.key, child]),
      );
      const existingChildrenMap = new Map(
        filteredChildren.map((child) => [child.key, child]),
      );

      // Merge new children: update existing ones with detailed data, keep order
      const mergedChildren = filteredChildren.map((existingChild) => {
        const matchingNewChild = newChildrenMap.get(existingChild.key);
        return matchingNewChild ?? existingChild;
      });

      // Add any new children that weren't in the existing list
      newChildren.forEach((newChild) => {
        if (!existingChildrenMap.has(newChild.key)) {
          mergedChildren.push(newChild);
        }
      });

      return {
        ...node,
        children: mergedChildren,
      };
    }
    if (node.children) {
      return {
        ...node,
        children: mergeTreeNodeData(node.children, key, newChildren),
      };
    }

    return node;
  });

export interface MonitorTreeRef {
  refreshResourcesAndAncestors: (urns: string[]) => Promise<void>;
}

interface MonitorTreeProps {
  selectedNodeKeys: Key[];
  setSelectedNodeKeys: (keys: Key[]) => void;
  onClickClassifyButton: () => void;
}

const MonitorTree = forwardRef<MonitorTreeRef, MonitorTreeProps>(
  ({ selectedNodeKeys, setSelectedNodeKeys, onClickClassifyButton }, ref) => {
    const router = useRouter();
    const { errorAlert } = useAlert();
    const monitorId = decodeURIComponent(router.query.monitorId as string);
    const [trigger] = useLazyGetMonitorTreeQuery();
    const [triggerAncestorsStatuses] =
      useLazyGetMonitorTreeAncestorsStatusesQuery();
    const [nodePagination, setNodePaginationState] = useState<
      Record<string, PaginationState>
    >({});
    const [treeData, setTreeData] = useState<CustomTreeDataNode[]>([]);
    const [expandedKeys, setExpandedKeys] = useState<Key[]>([]);
    // Track request sequences to prevent race conditions
    const requestSequenceRef = useRef<Record<string, number>>({});
    // Track whether detailed query has completed for each node to prevent fast query from overwriting it
    const detailedQueryCompletedRef = useRef<Record<string, number>>({});

    /**
     * Fetches tree data with the double-query pattern (fast then detailed)
     * Handles race conditions by tracking request sequences per node
     */
    const fetchTreeDataWithDetails = useCallback(
      async ({
        nodeKey,
        queryParams,
        fastUpdateFn,
        detailedUpdateFn,
      }: {
        nodeKey: string;
        queryParams: {
          monitor_config_id: string;
          staged_resource_urn?: string;
          size: number;
          page?: number;
        };
        fastUpdateFn: (
          data: Page_DatastoreStagedResourceTreeAPIResponse_,
        ) => void;
        detailedUpdateFn?: (
          data: Page_DatastoreStagedResourceTreeAPIResponse_,
        ) => void;
      }) => {
        // Increment sequence for this node to track this request
        const currentSequence = (requestSequenceRef.current[nodeKey] ?? 0) + 1;
        requestSequenceRef.current[nodeKey] = currentSequence;

        // Trigger both queries simultaneously
        const fastQuery = trigger({
          ...queryParams,
          include_descendant_details: false,
        });
        const detailedQuery = trigger({
          ...queryParams,
          include_descendant_details: true,
        });

        // Handle fast query result as soon as it arrives
        fastQuery.then(({ data: fastData }) => {
          // Only update if this is still the latest request for this node
          // AND the detailed query hasn't already completed for this sequence
          if (
            fastData &&
            requestSequenceRef.current[nodeKey] === currentSequence &&
            detailedQueryCompletedRef.current[nodeKey] !== currentSequence
          ) {
            fastUpdateFn(fastData);
          }
        });

        // Handle detailed query result when it arrives
        detailedQuery.then(({ data: detailedData }) => {
          // Only update if this is still the latest request for this node
          if (
            detailedData &&
            requestSequenceRef.current[nodeKey] === currentSequence
          ) {
            // Mark that detailed query has completed for this sequence
            detailedQueryCompletedRef.current[nodeKey] = currentSequence;
            // Use the detailed update function if provided, otherwise fall back to the fast one
            (detailedUpdateFn ?? fastUpdateFn)(detailedData);
          }
        });
      },
      [trigger],
    );

    const onLoadData = useCallback(
      (treeNode: CustomTreeDataNode) => {
        return new Promise<void>((resolve) => {
          const { children, key } = treeNode;
          // if already loaded children, state will be used
          if (children) {
            resolve();
            return;
          }

          const nodeKey = key.toString();
          fetchTreeDataWithDetails({
            nodeKey,
            queryParams: {
              monitor_config_id: monitorId,
              staged_resource_urn: nodeKey,
              size: TREE_PAGE_SIZE,
            },
            fastUpdateFn: (data) => {
              setTreeData((origin) =>
                updateTreeData(
                  origin,
                  key,
                  mapResponseToTreeData(data, nodeKey),
                ),
              );
              setNodePaginationState((prevState) => ({
                ...prevState,
                [nodeKey]: { pageSize: TREE_PAGE_SIZE, pageIndex: 1 },
              }));
            },
          });

          resolve();
        });
      },
      [fetchTreeDataWithDetails, monitorId],
    );

    const onLoadMore = useCallback(
      (key: string) => {
        const currentNodePagination = nodePagination[key];

        if (currentNodePagination) {
          // Show skeleton loaders while loading
          setTreeData((origin) => {
            return appendTreeNodeData(
              origin,
              key,
              [...Array(TREE_PAGE_SIZE)].map((_, i) => ({
                key: `${TREE_NODE_SKELETON_KEY_PREFIX}-${key}-${i}`,
                title: "SKELETON",
                isLeaf: true,
              })),
            );
          });

          fetchTreeDataWithDetails({
            nodeKey: key,
            queryParams: {
              monitor_config_id: monitorId,
              staged_resource_urn: key,
              size: TREE_PAGE_SIZE,
              page: currentNodePagination.pageIndex + 1,
            },
            fastUpdateFn: (data) => {
              // Fast query: append the new nodes
              setTreeData((origin) =>
                appendTreeNodeData(
                  origin,
                  key,
                  mapResponseToTreeData(data, key),
                ),
              );
              // Note: pagination state is updated in detailedUpdateFn to avoid double increment
            },
            detailedUpdateFn: (data) => {
              // Detailed query: merge/update the nodes with the same keys
              setTreeData((origin) =>
                mergeTreeNodeData(
                  origin,
                  key,
                  mapResponseToTreeData(data, key),
                ),
              );
              setNodePaginationState((prevState) => ({
                ...prevState,
                [key]: {
                  pageSize: TREE_PAGE_SIZE,
                  pageIndex: (prevState[key]?.pageIndex ?? 0) + 1,
                },
              }));
            },
          });
        }
      },
      [nodePagination, fetchTreeDataWithDetails, monitorId],
    );

    /**
     * Collapses a node by removing it from expandedKeys and removing its children from the tree
     * Also cleans up all descendant nodes from all state tracking
     * @param urn The URN of the node to collapse
     */
    const collapseNodeAndRemoveChildren = useCallback((urn: string) => {
      setTreeData((currentTreeData) => {
        // First, find the node to get all its descendants
        const node = findNodeByUrn(currentTreeData, urn);
        const allUrnsToClean = [urn];

        if (node) {
          // Collect all descendant URNs recursively
          allUrnsToClean.push(...collectAllDescendantUrns(node));
        }

        // Remove the URN and all its descendants from expandedKeys
        setExpandedKeys((currentExpandedKeys) =>
          currentExpandedKeys.filter(
            (key) => !allUrnsToClean.includes(key.toString()),
          ),
        );

        // Clear pagination state for this node and all descendants
        setNodePaginationState((currentPagination) => {
          const newPagination = { ...currentPagination };
          allUrnsToClean.forEach((urnToClean) => {
            delete newPagination[urnToClean];
          });
          return newPagination;
        });

        // Clear request tracking refs for this node and all descendants
        allUrnsToClean.forEach((urnToClean) => {
          delete requestSequenceRef.current[urnToClean];
          delete detailedQueryCompletedRef.current[urnToClean];
        });

        // Remove children from the tree
        return removeChildrenFromNode(currentTreeData, urn);
      });
    }, []);

    /**
     * Refreshes the specified resources and all their ancestors in the tree
     * @param urns The URNs of the resources that were updated
     */
    const refreshResourcesAndAncestors = useCallback(
      async (urns: string[]) => {
        const updateAncestorsForUrn = async (urn?: string) => {
          try {
            const result = await triggerAncestorsStatuses({
              monitor_config_id: monitorId,
              ...(urn && { staged_resource_urn: urn }),
            });

            if (result.error) {
              errorAlert(
                getErrorMessage(result.error),
                "Failed to get schema explorer ancestors statuses",
              );
              return;
            }

            const ancestorsData = result.data;
            if (!ancestorsData) {
              return;
            }

            // Collapse the affected URN and remove its children
            if (urn) {
              collapseNodeAndRemoveChildren(urn);
            } else {
              // ancestorsData contains the databases of the monitor
              ancestorsData.forEach((ancestorNode) => {
                collapseNodeAndRemoveChildren(ancestorNode.urn);
              });
            }

            // Update the status of each ancestor node
            setTreeData((origin) =>
              ancestorsData.reduce(
                (tree, ancestorNode) =>
                  updateNodeStatus(
                    tree,
                    ancestorNode.urn,
                    ancestorNode.update_status,
                  ),
                origin,
              ),
            );
          } catch (error) {
            errorAlert(
              "An unexpected error occurred while refreshing the schema explorer",
            );
          }
        };

        if (urns.length === 0) {
          await updateAncestorsForUrn();
          return;
        }

        // Process all URNs in parallel
        await Promise.all(urns.map((urn) => updateAncestorsForUrn(urn)));
      },
      [
        triggerAncestorsStatuses,
        monitorId,
        collapseNodeAndRemoveChildren,
        errorAlert,
      ],
    );

    /**
     * Handles tree expansion - if a node without children is being expanded, load its data
     */
    const handleExpand = useCallback(
      (
        newExpandedKeys: Key[],
        info: { expanded: boolean; node: CustomTreeDataNode },
      ) => {
        setExpandedKeys(newExpandedKeys);

        // If expanding a node without children, manually trigger loadData
        if (info.expanded && !info.node.children && onLoadData) {
          onLoadData(info.node);
        }
      },
      [onLoadData],
    );

    // Expose the function through the ref
    useImperativeHandle(ref, () => ({
      refreshResourcesAndAncestors,
    }));

    useEffect(() => {
      const getInitTreeData = async () => {
        // Only load if tree is empty
        if (treeData.length > 0) {
          return;
        }

        fetchTreeDataWithDetails({
          nodeKey: "root",
          queryParams: {
            monitor_config_id: monitorId,
            size: TREE_PAGE_SIZE,
          },
          fastUpdateFn: (data) => {
            setTreeData(mapResponseToTreeData(data));
          },
        });
      };

      getInitTreeData();
    }, [fetchTreeDataWithDetails, monitorId, setTreeData, treeData.length]);

    return (
      <Flex gap="middle" vertical className="h-full">
        <Title level={3} className="sticky top-0">
          Schema explorer
        </Title>
        <Tree
          loadData={onLoadData}
          treeData={treeData}
          expandedKeys={expandedKeys}
          onExpand={handleExpand}
          onSelect={(_, info) =>
            setSelectedNodeKeys(info.selectedNodes.map(({ key }) => key))
          }
          showIcon
          showLine
          blockNode
          rootClassName="h-full overflow-x-hidden"
          // eslint-disable-next-line react/no-unstable-nested-components
          titleRender={(node) => (
            <MonitorTreeDataTitle
              node={node}
              treeData={treeData}
              onLoadMore={onLoadMore}
            />
          )}
        />
        {selectedNodeKeys.length > 0 && (
          <Flex justify="space-between" align="center">
            <span>{selectedNodeKeys.length} selected</span>
            <Button
              aria-label={`Classify ${selectedNodeKeys.length} Selected Nodes`}
              icon={<SparkleIcon size={12} />}
              size="small"
              onClick={onClickClassifyButton}
            />
          </Flex>
        )}
      </Flex>
    );
  },
);

MonitorTree.displayName = "MonitorTree";

export default MonitorTree;

import {
  AntButton as Button,
  AntFlex as Flex,
  AntTitle as Title,
  AntTree as Tree,
  AntTreeProps as TreeProps,
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
import { removeChildrenFromNode, updateNodeStatus } from "./treeUtils";
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
        updateFn,
        onFastDataLoaded,
      }: {
        nodeKey: string;
        queryParams: {
          monitor_config_id: string;
          staged_resource_urn?: string;
          size: number;
          page?: number;
        };
        updateFn: (data: Page_DatastoreStagedResourceTreeAPIResponse_) => void;
        onFastDataLoaded?: (pageIndex: number) => void;
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
            updateFn(fastData);
            onFastDataLoaded?.(queryParams.page ?? 1);
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
            updateFn(detailedData);
          }
        });
      },
      [trigger],
    );

    const onLoadData: TreeProps["loadData"] = useCallback(
      ({ children, key }: { children?: any; key: React.Key }) => {
        return new Promise<void>((resolve) => {
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
            updateFn: (data) => {
              setTreeData((origin) =>
                updateTreeData(
                  origin,
                  key,
                  mapResponseToTreeData(data, nodeKey),
                ),
              );
            },
            onFastDataLoaded: () => {
              setNodePaginationState({
                ...nodePagination,
                [nodeKey]: { pageSize: TREE_PAGE_SIZE, pageIndex: 1 },
              });
            },
          });

          resolve();
        });
      },
      [fetchTreeDataWithDetails, monitorId, nodePagination],
    );

    const onLoadMore = (key: string) => {
      const currentNodePagination = nodePagination?.[key];

      if (currentNodePagination) {
        const newPage = currentNodePagination.pageIndex + 1;

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
            page: newPage,
          },
          updateFn: (data) => {
            setTreeData((origin) =>
              appendTreeNodeData(origin, key, mapResponseToTreeData(data, key)),
            );
          },
          onFastDataLoaded: (pageIndex) => {
            setNodePaginationState({
              ...nodePagination,
              [key]: { pageSize: TREE_PAGE_SIZE, pageIndex },
            });
          },
        });
      }
    };

    /**
     * Collapses a node by removing it from expandedKeys and removing its children from the tree
     * @param urn The URN of the node to collapse
     */
    const collapseNodeAndRemoveChildren = useCallback((urn: string) => {
      // Remove the URN from expandedKeys to collapse it
      setExpandedKeys((currentExpandedKeys) =>
        currentExpandedKeys.filter((key) => key.toString() !== urn),
      );

      // Remove children from the tree
      setTreeData((origin) => removeChildrenFromNode(origin, urn));

      // Clear pagination state for this node to force re-fetch
      setNodePaginationState((currentPagination) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { [urn]: removedPagination, ...rest } = currentPagination;
        return rest;
      });

      // Clear request tracking refs for this node
      delete requestSequenceRef.current[urn];
      delete detailedQueryCompletedRef.current[urn];
    }, []);

    /**
     * Refreshes the specified resources and all their ancestors in the tree
     * @param urns The URNs of the resources that were updated
     */
    const refreshResourcesAndAncestors = useCallback(
      async (urns: string[]) => {
        const updateAncestorsForUrn = async (urn?: string) => {
          const { data: ancestorsData } = await triggerAncestorsStatuses({
            monitor_config_id: monitorId,
            ...(urn && { staged_resource_urn: urn }),
          });

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
          setTreeData((origin) => {
            let updatedTree = origin;

            ancestorsData.forEach((ancestorNode) => {
              updatedTree = updateNodeStatus(
                updatedTree,
                ancestorNode.urn,
                ancestorNode.update_status,
                ancestorNode.has_grandchildren ?? false,
              );
            });

            return updatedTree;
          });
        };

        if (urns.length === 0) {
          await updateAncestorsForUrn();
          return;
        }

        // Process all URNs in parallel
        await Promise.all(urns.map((urn) => updateAncestorsForUrn(urn)));
      },
      [triggerAncestorsStatuses, monitorId, collapseNodeAndRemoveChildren],
    );

    /**
     * Handles tree expansion - if a node without children is being expanded, load its data
     */
    const handleExpand = useCallback(
      (newExpandedKeys: Key[], info: { expanded: boolean; node: any }) => {
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
          updateFn: (data) => {
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

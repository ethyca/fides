import {
  Badge,
  Button,
  Dropdown,
  Flex,
  Icons,
  SparkleIcon,
  Text,
  Title,
  Tooltip,
  Tree,
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
import { Node } from "~/features/common/hooks/useNodeMap";
import { CursorPaginationState } from "~/features/common/pagination";
import { pluralize } from "~/features/common/utils";
import {
  useLazyGetMonitorTreeAncestorsStatusesQuery,
  useLazyGetMonitorTreeQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DiffStatus, StagedResourceTypeValue } from "~/types/api";
import { CursorPage_DatastoreStagedResourceTreeAPIResponse_ } from "~/types/api/models/CursorPage_DatastoreStagedResourceTreeAPIResponse_";

import { DatastorePageSettings } from "../types";
import {
  DEFAULT_FILTER_STATUSES,
  MAP_DATASTORE_RESOURCE_TYPE_TO_ICON,
  MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO,
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_LOAD_MORE_TEXT,
  TREE_NODE_SKELETON_KEY_PREFIX,
  TREE_PAGE_SIZE,
} from "./MonitorFields.const";
import styles from "./MonitorTree.module.scss";
import { MonitorTreeDataTitle } from "./MonitorTreeDataTitle";
import {
  collectAllDescendantUrns,
  findNodeByUrn,
  removeChildrenFromNode,
  shouldShowBadgeDot,
  updateNodeStatus,
} from "./treeUtils";
import { CustomTreeDataNode, TreeNodeAction } from "./types";
import { intoDiffStatus } from "./utils";

const mapResponseToTreeData = (
  data: CursorPage_DatastoreStagedResourceTreeAPIResponse_,
  key?: string,
): CustomTreeDataNode[] => {
  const dataItems: CustomTreeDataNode[] = data.items.map((treeNode) => {
    const IconComponent = treeNode.resource_type
      ? MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
          treeNode.resource_type as StagedResourceTypeValue
        ]
      : undefined;
    const statusInfo = treeNode.update_status
      ? MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO[
          treeNode.update_status
        ]
      : undefined;

    return {
      title: treeNode.name,
      key: treeNode.urn,
      selectable: true, // all nodes are selectable since we ignore lowest level descendants in the data
      icon: IconComponent
        ? () => (
            <Tooltip title={statusInfo?.tooltip}>
              <Badge
                className="h-full"
                offset={[0, 5]}
                color={statusInfo?.color}
                dot={shouldShowBadgeDot(treeNode)}
              >
                <IconComponent className="h-full" />
              </Badge>
            </Tooltip>
          )
        : undefined,
      status: treeNode.update_status,
      diffStatus: treeNode.diff_status,
      isLeaf:
        treeNode.resource_type === StagedResourceTypeValue.FIELD ||
        !treeNode.has_grandchildren,
      classifyable: [
        StagedResourceTypeValue.SCHEMA,
        StagedResourceTypeValue.TABLE,
        StagedResourceTypeValue.ENDPOINT,
        StagedResourceTypeValue.FIELD,
      ].includes(treeNode.resource_type as StagedResourceTypeValue),
    };
  });

  return !data.next_page
    ? dataItems
    : [
        ...dataItems,
        {
          title: TREE_NODE_LOAD_MORE_TEXT,
          key: `${TREE_NODE_LOAD_MORE_KEY_PREFIX}-${data.current_page}-${key}`,
          /* eslint-disable react/jsx-no-useless-fragment */
          icon: <></>,
          selectable: false,
          isLeaf: true,
        },
      ];
};

const appendTreeNodeData = (
  list: Node<CustomTreeDataNode>[],
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

interface NodeActions<Action, ActionDict extends Record<string, Action>> {
  nodeActions: ActionDict;
  primaryAction: keyof ActionDict;
}

interface MonitorTreeProps
  extends NodeActions<TreeNodeAction, Record<string, TreeNodeAction>> {
  setSelectedNodeKeys: (keys: Key[]) => void;
  selectedNodeKeys: Key[];
}

const MonitorTree = forwardRef<
  MonitorTreeRef,
  MonitorTreeProps & DatastorePageSettings
>(
  (
    {
      setSelectedNodeKeys,
      selectedNodeKeys,
      nodeActions,
      primaryAction,
      showApproved,
      showIgnored,
    },
    ref,
  ) => {
    const router = useRouter();
    const { errorAlert } = useAlert();
    const monitorId = decodeURIComponent(router.query.monitorId as string);
    const [trigger] = useLazyGetMonitorTreeQuery();
    const [triggerAncestorsStatuses] =
      useLazyGetMonitorTreeAncestorsStatusesQuery();
    const [nodePagination, setNodePaginationState] = useState<
      Record<string, CursorPaginationState>
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
          cursor?: string;
          diff_status?: DiffStatus[];
        };
        fastUpdateFn: (
          data: CursorPage_DatastoreStagedResourceTreeAPIResponse_,
        ) => void;
        detailedUpdateFn?: (
          data: CursorPage_DatastoreStagedResourceTreeAPIResponse_,
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
      [trigger, showApproved, showIgnored],
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
              diff_status: [
                ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
                ...(showIgnored ? intoDiffStatus("Ignored") : []),
                ...(showApproved ? intoDiffStatus("Approved") : []),
              ],
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
                [nodeKey]: {
                  pageSize: TREE_PAGE_SIZE,
                  cursor_start: data.current_page ?? undefined,
                  cursor_end: data.next_page ?? undefined,
                },
              }));
            },
          });

          resolve();
        });
      },
      [fetchTreeDataWithDetails, monitorId, showApproved, showIgnored],
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
              diff_status: [
                ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
                ...(showIgnored ? intoDiffStatus("Ignored") : []),
                ...(showApproved ? intoDiffStatus("Approved") : []),
              ],
              size: TREE_PAGE_SIZE,
              cursor: currentNodePagination.cursor_end,
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
                  cursor_start: data?.current_page ?? undefined,
                  cursor_end: data?.next_page ?? undefined,
                },
              }));
            },
          });
        }
      },
      [
        nodePagination,
        fetchTreeDataWithDetails,
        monitorId,
        showApproved,
        showIgnored,
      ],
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

            // Update the status and diffStatus of each ancestor node
            setTreeData((origin) =>
              ancestorsData.reduce(
                (tree, ancestorNode) =>
                  updateNodeStatus(
                    tree,
                    ancestorNode.urn,
                    ancestorNode.update_status,
                    ancestorNode.diff_status,
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

    const handleSelect = (keys: Key[]) => {
      setSelectedNodeKeys(keys);
    };

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
            diff_status: [
              ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
              ...(showIgnored ? intoDiffStatus("Ignored") : []),
              ...(showApproved ? intoDiffStatus("Approved") : []),
            ],
            size: TREE_PAGE_SIZE,
          },
          fastUpdateFn: (data) => {
            setTreeData(mapResponseToTreeData(data));
          },
        });
      };

      getInitTreeData();
    }, [
      fetchTreeDataWithDetails,
      monitorId,
      setTreeData,
      treeData.length,
      showIgnored,
      showApproved,
    ]);

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
            diff_status: [
              ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
              ...(showIgnored ? intoDiffStatus("Ignored") : []),
              ...(showApproved ? intoDiffStatus("Approved") : []),
            ],
            size: TREE_PAGE_SIZE,
          },
          fastUpdateFn: (data) => {
            setTreeData(mapResponseToTreeData(data));
          },
        });
      };
      setTreeData([]);

      setExpandedKeys([]);
      setNodePaginationState({});

      getInitTreeData();
    }, [showIgnored, showApproved]);

    return (
      <Flex gap="middle" vertical className="h-full">
        <Title level={3} className="sticky top-0" ellipsis>
          Schema explorer
        </Title>
        <Tree.DirectoryTree
          loadData={onLoadData}
          treeData={treeData}
          expandedKeys={expandedKeys}
          onExpand={handleExpand}
          onSelect={handleSelect}
          showIcon
          showLine
          blockNode
          multiple
          rootClassName={`h-full overflow-x-hidden ${styles["monitor-tree"]} group/monitor-tree ${selectedNodeKeys.length > 1 ? "multi-select" : ""}`}
          expandAction="doubleClick"
          // eslint-disable-next-line react/no-unstable-nested-components
          titleRender={(node) => (
            <MonitorTreeDataTitle
              node={node}
              treeData={treeData}
              onLoadMore={onLoadMore}
              actions={nodeActions}
            />
          )}
        />
        {selectedNodeKeys.length > 0 && (
          <Flex justify="space-between" align="center" gap="small">
            <Button
              aria-label={`Classify ${selectedNodeKeys.length} Selected Nodes`}
              icon={<SparkleIcon size={12} />}
              size="small"
              onClick={() =>
                nodeActions[primaryAction]?.callback(
                  selectedNodeKeys,
                  selectedNodeKeys.flatMap((nodeKey) => {
                    const node = findNodeByUrn(treeData, nodeKey.toString());
                    return node ? [node] : [];
                  }),
                )
              }
              className="flex-none"
            />
            <Text
              ellipsis
            >{`${selectedNodeKeys.length} ${pluralize(selectedNodeKeys.length, "resource", "resources")} selected`}</Text>
            <Dropdown
              menu={{
                items: nodeActions
                  ? Object.entries(nodeActions).map(
                      ([key, { label, disabled }]) => ({
                        key,
                        label,
                        disabled: disabled(
                          selectedNodeKeys.flatMap((nodeKey) => {
                            const node = findNodeByUrn(
                              treeData,
                              nodeKey.toString(),
                            );
                            return node ? [node] : [];
                          }),
                        ),
                      }),
                    )
                  : [],
                onClick: ({ key, domEvent }) => {
                  domEvent.preventDefault();
                  domEvent.stopPropagation();
                  nodeActions[key]?.callback(
                    selectedNodeKeys,
                    selectedNodeKeys.flatMap((nodeKey) => {
                      const node = findNodeByUrn(treeData, nodeKey.toString());
                      return node ? [node] : [];
                    }),
                  );
                },
              }}
              destroyOnHidden
              className="group mr-1 flex-none"
            >
              <Button
                aria-label="Show More Resource Actions"
                icon={<Icons.OverflowMenuVertical />}
                size="small"
                className="self-end"
              />
            </Dropdown>
          </Flex>
        )}
      </Flex>
    );
  },
);

MonitorTree.displayName = "MonitorTree";

export default MonitorTree;

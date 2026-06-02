import {
  Badge,
  Button,
  Dropdown,
  Empty,
  Flex,
  Icons,
  Spin,
  Text,
  Title,
  Tree,
  useMessage,
  useNotification,
} from "fidesui";
import {
  forwardRef,
  Key,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { nFormatter, pluralize } from "~/features/common/utils";
import { DiffStatus } from "~/types/api";

import {
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredSystemAggregateQuery,
  useIgnoreMonitorResultSystemsMutation,
} from "../action-center.slice";
import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import styles from "./WebsiteAssetExplorerTree.module.scss";
import {
  applyCountDelta,
  isUncategorizedKey,
  mapAggregateToTreeNodes,
  WebsiteSystemTreeNodeData,
} from "./websiteTreeUtils";

// The system-aggregate endpoint caps `size` at 100, which comfortably covers
// website monitors' modest system counts. (>100 systems would need paging.)
const EXPLORER_PAGE_SIZE = 100;
// How long a temporary "recently changed" alert dot stays on a node.
const RECENT_CHANGE_TTL_MS = 5000;

const WebsiteTreeNodeTitle = ({
  nodeData,
  isRecentlyChanged,
}: {
  nodeData: WebsiteSystemTreeNodeData;
  isRecentlyChanged: boolean;
}) => {
  // Render the leading icon inside the title so it shares the same flex
  // row as the name and stays vertically centered with it. Uncategorized
  // uses the carbon tag-group icon; systems use the same fallback icon as
  // the infrastructure monitor.
  const LeadingIcon = isUncategorizedKey(nodeData.key)
    ? Icons.TagGroup
    : Icons.TransformInstructions;

  return (
    <Flex align="center" justify="space-between" gap="small" className="w-full">
      <Flex align="center" gap="small" className="overflow-hidden">
        <LeadingIcon className="flex-none" />
        <Badge
          dot={isRecentlyChanged}
          color="var(--fidesui-warning)"
          offset={[-2, 4]}
          className="overflow-hidden"
        >
          <Text ellipsis={{ tooltip: nodeData.title }}>{nodeData.title}</Text>
        </Badge>
      </Flex>
      <Flex align="center" gap="small" className="flex-none">
        {/* warning icon sits to the left of the asset count */}
        <DiscoveryStatusIcon consentStatus={nodeData.record.consent_status} />
        <Text type="secondary">{nFormatter(nodeData.count)}</Text>
      </Flex>
    </Flex>
  );
};

export interface WebsiteAssetExplorerTreeRef {
  /**
   * Optimistically adjust system asset counts after a reassignment and flash a
   * temporary alert dot on the affected node(s), without refetching.
   */
  bumpSystemCounts: (args: {
    fromSystemId?: string;
    toSystemId?: string;
  }) => void;
}

interface WebsiteAssetExplorerTreeProps {
  monitorId: string;
  diffStatus?: DiffStatus[];
  search?: string;
  /** undefined = no system selected (show all assets). */
  onSelectSystem: (systemId: string | undefined) => void;
}

const WebsiteAssetExplorerTree = forwardRef<
  WebsiteAssetExplorerTreeRef,
  WebsiteAssetExplorerTreeProps
>(({ monitorId, diffStatus, search, onSelectSystem }, ref) => {
  const message = useMessage();
  const notification = useNotification();

  const { data, isLoading, isFetching } = useGetDiscoveredSystemAggregateQuery({
    key: monitorId,
    page: 1,
    size: EXPLORER_PAGE_SIZE,
    search,
    diff_status: diffStatus,
  });

  const [nodes, setNodes] = useState<WebsiteSystemTreeNodeData[]>([]);
  // Multi-selection (datastore parity): keys of all selected system nodes.
  const [selectedKeys, setSelectedKeys] = useState<Key[]>([]);
  const [recentlyChanged, setRecentlyChanged] = useState<Set<string>>(
    new Set(),
  );
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const [addMonitorResultSystemsMutation, { isLoading: isApproving }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoring }] =
    useIgnoreMonitorResultSystemsMutation();

  // Seed/refresh local node state whenever the aggregate query returns.
  useEffect(() => {
    if (data?.items) {
      setNodes(mapAggregateToTreeNodes(data.items));
    }
  }, [data?.items]);

  // Clear any pending badge-expiry timers on unmount.
  useEffect(
    () => () => {
      Object.values(timersRef.current).forEach(clearTimeout);
    },
    [],
  );

  useImperativeHandle(
    ref,
    () => ({
      bumpSystemCounts: ({ fromSystemId, toSystemId }) => {
        setNodes((prev) => applyCountDelta(prev, { fromSystemId, toSystemId }));
        const changedKeys = [fromSystemId, toSystemId].filter(
          (k): k is string => !!k,
        );
        if (!changedKeys.length) {
          return;
        }
        setRecentlyChanged((prev) => {
          const next = new Set(prev);
          changedKeys.forEach((k) => next.add(k));
          return next;
        });
        changedKeys.forEach((key) => {
          if (timersRef.current[key]) {
            clearTimeout(timersRef.current[key]);
          }
          timersRef.current[key] = setTimeout(() => {
            setRecentlyChanged((prev) => {
              const next = new Set(prev);
              next.delete(key);
              return next;
            });
            delete timersRef.current[key];
          }, RECENT_CHANGE_TTL_MS);
        });
      },
    }),
    [],
  );

  const treeData = useMemo(
    () =>
      nodes.map((node) => ({
        key: node.key,
        title: node.title,
        isLeaf: node.isLeaf,
        selectable: node.selectable,
      })),
    [nodes],
  );

  const nodesByKey = useMemo(
    () => new Map(nodes.map((node) => [node.key, node])),
    [nodes],
  );

  const selectedSystemIds = useMemo(
    () => selectedKeys.map((k) => k.toString()),
    [selectedKeys],
  );

  const handleApproveSystems = useCallback(async () => {
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedSystemIds,
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      notification.success({
        message: "Approved",
        description: `Assets from ${selectedSystemIds.length} ${pluralize(
          selectedSystemIds.length,
          "system",
          "systems",
        )} have been added to the system inventory.`,
      });
      setSelectedKeys([]);
      onSelectSystem(undefined);
    }
  }, [
    addMonitorResultSystemsMutation,
    monitorId,
    selectedSystemIds,
    message,
    notification,
    onSelectSystem,
  ]);

  const handleIgnoreSystems = useCallback(async () => {
    const result = await ignoreMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedSystemIds,
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success(
        `${selectedSystemIds.length} ${pluralize(
          selectedSystemIds.length,
          "system",
          "systems",
        )} ignored.`,
      );
      setSelectedKeys([]);
      onSelectSystem(undefined);
    }
  }, [
    ignoreMonitorResultSystemsMutation,
    monitorId,
    selectedSystemIds,
    message,
    onSelectSystem,
  ]);

  const isActioning = isApproving || isIgnoring;

  return (
    <Flex vertical gap="small" className="h-full overflow-hidden">
      <Title level={3} ellipsis>
        Asset explorer
      </Title>
      {isLoading ? (
        <Flex justify="center" className="mt-6">
          <Spin />
        </Flex>
      ) : null}
      {!isLoading && nodes.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No systems found"
        />
      ) : null}
      {nodes.length > 0 ? (
        <div className="flex-1 overflow-y-auto">
          <Tree.DirectoryTree
            blockNode
            multiple
            showIcon={false}
            rootClassName={styles["asset-explorer-tree"]}
            selectedKeys={selectedKeys}
            treeData={treeData}
            data-testid="asset-explorer-tree"
            // eslint-disable-next-line react/no-unstable-nested-components
            titleRender={(node) => {
              const nodeData = nodesByKey.get(node.key.toString());
              if (!nodeData) {
                return null;
              }
              return (
                <WebsiteTreeNodeTitle
                  nodeData={nodeData}
                  isRecentlyChanged={recentlyChanged.has(nodeData.key)}
                />
              );
            }}
            onSelect={(_keys, info) => {
              // Custom toggle so a plain click on the sole selected node
              // deselects it (revealing all assets), matching the request,
              // while cmd/ctrl-click multi-selects (datastore parity).
              const clickedKey = info.node.key.toString();
              const multi =
                info.nativeEvent.metaKey || info.nativeEvent.ctrlKey;
              const prevKeys = selectedKeys.map((k) => k.toString());
              let next: string[];
              if (multi) {
                next = prevKeys.includes(clickedKey)
                  ? prevKeys.filter((k) => k !== clickedKey)
                  : [...prevKeys, clickedKey];
              } else {
                next =
                  prevKeys.length === 1 && prevKeys[0] === clickedKey
                    ? []
                    : [clickedKey];
              }
              setSelectedKeys(next);
              onSelectSystem(next.length ? next[0] : undefined);
            }}
          />
          {isFetching ? (
            <Flex justify="center" className="mt-2">
              <Spin size="small" />
            </Flex>
          ) : null}
        </div>
      ) : null}

      {/* Bulk system actions footer (datastore pattern) */}
      {selectedKeys.length > 0 && (
        <Flex justify="space-between" align="center" gap="small">
          <Button
            aria-label={`Approve ${selectedKeys.length} selected systems`}
            icon={<Icons.Checkmark />}
            size="small"
            loading={isApproving}
            disabled={isActioning}
            onClick={handleApproveSystems}
            className="flex-none"
          />
          <Text ellipsis>
            {`${selectedKeys.length} ${pluralize(
              selectedKeys.length,
              "system",
              "systems",
            )} selected`}
          </Text>
          <Dropdown
            trigger={["click"]}
            menu={{
              items: [
                { key: "approve", label: "Approve" },
                { key: "ignore", label: "Ignore" },
              ],
              onClick: ({ key, domEvent }) => {
                domEvent.stopPropagation();
                if (key === "approve") {
                  handleApproveSystems();
                } else if (key === "ignore") {
                  handleIgnoreSystems();
                }
              },
            }}
            destroyOnHidden
            className="group mr-1 flex-none"
          >
            <Button
              aria-label="Show more system actions"
              icon={<Icons.OverflowMenuVertical />}
              size="small"
              loading={isActioning}
              className="self-end"
            />
          </Dropdown>
        </Flex>
      )}
    </Flex>
  );
});

WebsiteAssetExplorerTree.displayName = "WebsiteAssetExplorerTree";

export default WebsiteAssetExplorerTree;

import {
  Button,
  Dropdown,
  Empty,
  Flex,
  Icons,
  SparkleIcon,
  Spin,
  Text,
  Title,
  Tree,
} from "fidesui";
import { ReactNode, useMemo } from "react";

import { nFormatter } from "~/features/common/utils";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import styles from "./WebsiteAssetExplorerTree.module.scss";
import {
  isUncategorizedKey,
  WebsiteSystemTreeNodeData,
} from "./websiteTreeUtils";

const NODE_LOGO_SIZE = 18;

/**
 * A row action surfaced both in the per-node hover menu and the multi-select
 * footer (mirrors the datastore monitor tree's pattern). Actions receive the
 * list of target nodes — one for the hover menu, many for the footer.
 */
export interface AssetExplorerNodeAction {
  key: string;
  label: string;
  icon?: ReactNode;
  onClick: (nodes: WebsiteSystemTreeNodeData[]) => void;
  /** Return true to render the action disabled for the given node(s). */
  disabled?: (nodes: WebsiteSystemTreeNodeData[]) => boolean;
}

const TreeNodeActions = ({
  nodeData,
  actions,
}: {
  nodeData: WebsiteSystemTreeNodeData;
  actions: AssetExplorerNodeAction[];
}) => (
  <Dropdown
    destroyOnHidden
    menu={{
      items: actions.map((action) => ({
        key: action.key,
        label: action.label,
        icon: action.icon,
        disabled: action.disabled?.([nodeData]),
      })),
      onClick: ({ key, domEvent }) => {
        domEvent.preventDefault();
        domEvent.stopPropagation();
        actions.find((action) => action.key === key)?.onClick([nodeData]);
      },
    }}
  >
    <Button
      aria-label="Show node actions"
      type="text"
      size="small"
      // Tight (override antd's icon-only 24px width + padding) so the kebab
      // sits centered in the same slot the count occupies.
      className="!h-5 !w-4 !min-w-0 flex-none !p-0"
      onClick={(e) => e.stopPropagation()}
      icon={<Icons.OverflowMenuVertical />}
    />
  </Dropdown>
);

const TreeNodeLeadingVisual = ({
  nodeData,
}: {
  nodeData: WebsiteSystemTreeNodeData;
}) => {
  // The uncategorized "Resources" grouping always uses the tag-group icon.
  if (isUncategorizedKey(nodeData.key)) {
    return <Icons.TagGroup className="flex-none" />;
  }
  // Known inventory (Compass) system → its connector logo.
  if (nodeData.logoSource) {
    return (
      <ConnectionTypeLogo
        data={nodeData.logoSource}
        size={NODE_LOGO_SIZE}
        className="flex-none"
      />
    );
  }
  // Fides-suggested staged system → sparkle icon.
  if (nodeData.suggested) {
    return (
      <SparkleIcon
        className="flex-none"
        style={{ color: "var(--fidesui-brand-minos)" }}
      />
    );
  }
  // User-created / no Compass match → generic system icon.
  return (
    <Icons.TransformInstructions
      className="flex-none"
      style={{ color: "var(--fidesui-brand-minos)" }}
    />
  );
};

const TreeNodeTitle = ({
  nodeData,
  actions,
}: {
  nodeData: WebsiteSystemTreeNodeData;
  actions?: AssetExplorerNodeAction[];
}) => {
  return (
    <Flex
      align="center"
      justify="space-between"
      gap="small"
      className="group w-full"
    >
      <Flex align="center" gap="small" className="overflow-hidden">
        <TreeNodeLeadingVisual nodeData={nodeData} />
        <Text ellipsis={{ tooltip: nodeData.title }}>{nodeData.title}</Text>
      </Flex>
      <Flex align="center" gap="small" className="flex-none">
        <DiscoveryStatusIcon consentStatus={nodeData.record.consent_status} />
        {actions?.length ? (
          // The slot shrink-wraps the count (no extra right padding); on hover
          // the kebab fades in centered over the count, so it stays in place.
          <span className="relative inline-flex items-center">
            <Text
              type="secondary"
              className="transition-opacity group-hover:opacity-0"
            >
              {nFormatter(nodeData.count)}
            </Text>
            <span className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
              <TreeNodeActions nodeData={nodeData} actions={actions} />
            </span>
          </span>
        ) : (
          <Text type="secondary">{nFormatter(nodeData.count)}</Text>
        )}
      </Flex>
    </Flex>
  );
};

const TreeActionFooter = ({
  selectedNodes,
  actions,
}: {
  selectedNodes: WebsiteSystemTreeNodeData[];
  actions: AssetExplorerNodeAction[];
}) => {
  const [primaryAction] = actions;
  return (
    <Flex
      justify="space-between"
      align="center"
      gap="small"
      className="flex-none"
    >
      <Text ellipsis>{`${selectedNodes.length} selected`}</Text>
      <Button
        aria-label={`${primaryAction.label} ${selectedNodes.length} selected`}
        icon={primaryAction.icon}
        size="small"
        disabled={primaryAction.disabled?.(selectedNodes)}
        onClick={() => primaryAction.onClick(selectedNodes)}
        className="flex-none"
        data-testid={`tree-footer-action-${primaryAction.key}`}
      />
    </Flex>
  );
};

export interface WebsiteAssetExplorerTreeProps {
  /** Flat tree nodes to render (the parent owns the data + grouping). */
  nodes: WebsiteSystemTreeNodeData[];
  /** Currently-selected node keys (empty = nothing selected → show all). */
  selectedKeys: string[];
  /**
   * Fired when the selection changes. Supports modifier-key multi-select
   * (shift for ranges, cmd/ctrl for individual toggles) via the tree.
   */
  onSelectKeys: (keys: string[]) => void;
  isLoading?: boolean;
  /** Panel heading. */
  title?: string;
  /**
   * Optional actions for a node (hover overflow menu) and any multi-selection
   * (footer bar) — e.g. approve a system + its resources.
   */
  nodeActions?: AssetExplorerNodeAction[];
}

/**
 * Presentational tree for the monitor "explorer" left panel. The parent builds
 * the flat node list (one grouping per system, plus a catch-all) and owns
 * selection; this component renders + styles it, plus an optional per-node
 * hover menu and a multi-select footer for bulk actions.
 */
const WebsiteAssetExplorerTree = ({
  nodes,
  selectedKeys,
  onSelectKeys,
  isLoading,
  title = "Asset explorer",
  nodeActions,
}: WebsiteAssetExplorerTreeProps) => {
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

  const selectedNodes = useMemo(
    () =>
      selectedKeys
        .map((key) => nodesByKey.get(key))
        .filter((node): node is WebsiteSystemTreeNodeData => !!node),
    [selectedKeys, nodesByKey],
  );

  return (
    <Flex vertical gap="small" className="h-full overflow-hidden">
      <Title level={3} ellipsis>
        {title}
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
                <TreeNodeTitle nodeData={nodeData} actions={nodeActions} />
              );
            }}
            onSelect={(keys, info) => {
              const native = info.nativeEvent as MouseEvent;
              // Modifier keys → native multi-select (cmd/ctrl toggle, shift
              // range). Plain click → single select, toggling off when the
              // sole selected node is clicked again (reveals all resources).
              if (native.metaKey || native.ctrlKey || native.shiftKey) {
                onSelectKeys(keys.map(String));
                return;
              }
              const clickedKey = info.node.key.toString();
              const isOnlySelected =
                selectedKeys.length === 1 && selectedKeys[0] === clickedKey;
              onSelectKeys(isOnlySelected ? [] : [clickedKey]);
            }}
          />
        </div>
      ) : null}
      {nodeActions?.length && selectedNodes.length > 0 ? (
        <TreeActionFooter selectedNodes={selectedNodes} actions={nodeActions} />
      ) : null}
    </Flex>
  );
};

export default WebsiteAssetExplorerTree;

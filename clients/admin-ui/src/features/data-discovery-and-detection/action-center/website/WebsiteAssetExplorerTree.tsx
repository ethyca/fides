import {
  Empty,
  Flex,
  Icons,
  SparkleIcon,
  Spin,
  Text,
  Title,
  Tree,
} from "fidesui";
import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import styles from "./WebsiteAssetExplorerTree.module.scss";
import {
  isUncategorizedKey,
  WebsiteSystemTreeNodeData,
} from "./websiteTreeUtils";

const NODE_LOGO_SIZE = 18;

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
}: {
  nodeData: WebsiteSystemTreeNodeData;
}) => {
  return (
    <Flex align="center" justify="space-between" gap="small" className="w-full">
      <Flex align="center" gap="small" className="overflow-hidden">
        <TreeNodeLeadingVisual nodeData={nodeData} />
        <Text ellipsis={{ tooltip: nodeData.title }}>{nodeData.title}</Text>
      </Flex>
      <Flex align="center" gap="small" className="flex-none">
        <DiscoveryStatusIcon consentStatus={nodeData.record.consent_status} />
        <Text type="secondary">{nFormatter(nodeData.count)}</Text>
      </Flex>
    </Flex>
  );
};

export interface WebsiteAssetExplorerTreeProps {
  /** Flat tree nodes to render (the parent owns the data + grouping). */
  nodes: WebsiteSystemTreeNodeData[];
  /** Currently-selected node keys (empty = nothing selected → show all). */
  selectedKeys: string[];
  /** Fired when the selection changes (single-select; clears on re-click). */
  onSelectKeys: (keys: string[]) => void;
  isLoading?: boolean;
  /** Panel heading. */
  title?: string;
}

/**
 * Presentational tree for the monitor "explorer" left panel. The parent builds
 * the flat node list (one grouping per system, plus a catch-all); this
 * component renders it and owns single-select navigation/filtering — clicking a
 * node filters the list, clicking it again clears the filter.
 */
const WebsiteAssetExplorerTree = ({
  nodes,
  selectedKeys,
  onSelectKeys,
  isLoading,
  title = "Asset explorer",
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
              return <TreeNodeTitle nodeData={nodeData} />;
            }}
            onSelect={(_keys, info) => {
              // Single-select filter: clicking the already-selected node clears
              // the selection (revealing all resources).
              const clickedKey = info.node.key.toString();
              const isOnlySelected =
                selectedKeys.length === 1 && selectedKeys[0] === clickedKey;
              onSelectKeys(isOnlySelected ? [] : [clickedKey]);
            }}
          />
        </div>
      ) : null}
    </Flex>
  );
};

export default WebsiteAssetExplorerTree;

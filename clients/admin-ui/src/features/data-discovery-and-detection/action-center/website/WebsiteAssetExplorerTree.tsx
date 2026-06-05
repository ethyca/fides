import { Empty, Flex, Icons, Spin, Text, Title, Tree } from "fidesui";
import { Key, useMemo } from "react";

import { nFormatter } from "~/features/common/utils";

import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import styles from "./WebsiteAssetExplorerTree.module.scss";
import {
  isUncategorizedKey,
  WebsiteSystemTreeNodeData,
} from "./websiteTreeUtils";

const TreeNodeTitle = ({
  nodeData,
}: {
  nodeData: WebsiteSystemTreeNodeData;
}) => {
  // Leading visual: the generic carbon system icon for systems, and the
  // tag-group icon for the uncategorized "Resources" grouping.
  const isUncategorized = isUncategorizedKey(nodeData.key);

  return (
    <Flex align="center" justify="space-between" gap="small" className="w-full">
      <Flex align="center" gap="small" className="overflow-hidden">
        {isUncategorized ? (
          <Icons.TagGroup className="flex-none" />
        ) : (
          <Icons.TransformInstructions
            className="flex-none"
            style={{ color: "var(--fidesui-brand-minos)" }}
          />
        )}
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
  /** Currently-selected node key (undefined = nothing selected → show all). */
  selectedKey?: string;
  /** Fired when a node is selected/deselected. */
  onSelectSystem: (systemId: string | undefined) => void;
  isLoading?: boolean;
  /** Panel heading. */
  title?: string;
}

/**
 * Presentational tree for the monitor "explorer" left panel. The parent builds
 * the flat node list (one grouping per system, plus a catch-all) and owns
 * selection; this component renders + styles it.
 */
const WebsiteAssetExplorerTree = ({
  nodes,
  selectedKey,
  onSelectSystem,
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

  const selectedKeys: Key[] = selectedKey ? [selectedKey] : [];

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
              // Plain click toggles the sole selection: clicking the selected
              // node clears it (revealing all resources).
              const clickedKey = info.node.key.toString();
              onSelectSystem(
                selectedKey === clickedKey ? undefined : clickedKey,
              );
            }}
          />
        </div>
      ) : null}
    </Flex>
  );
};

export default WebsiteAssetExplorerTree;

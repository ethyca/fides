import {
  AntButton as Button,
  AntFlex as Flex,
  AntTitle as Title,
  AntTree as Tree,
  AntTreeDataNode as TreeDataNode,
  AntTreeProps as TreeProps,
  Icons,
  SparkleIcon,
} from "fidesui";
import { useRouter } from "next/router";
import { Key, ReactNode, useEffect, useState } from "react";

import { PaginationState } from "~/features/common/pagination";
import { useLazyGetMonitorTreeQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  Page_DatastoreStagedResourceTreeAPIResponse_,
  TreeResourceChangeIndicator,
} from "~/types/api";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_LOAD_MORE_TEXT,
  TREE_NODE_SKELETON_KEY_PREFIX,
  TREE_PAGE_SIZE,
} from "./MonitorFields.const";
import { MonitorTreeDataTitle } from "./MonitorTreeDataTitle";

// Extend TreeDataNode to include the diff_status from the API response and prevent title from being a function
export interface CustomTreeDataNode extends TreeDataNode {
  title?: ReactNode;
  status?: TreeResourceChangeIndicator | null;
  children?: CustomTreeDataNode[];
}

const mapResponseToTreeData = (
  data: Page_DatastoreStagedResourceTreeAPIResponse_,
  key?: string,
): CustomTreeDataNode[] => {
  const dataItems: CustomTreeDataNode[] = data.items.map((treeNode) => ({
    title: treeNode.name,
    key: treeNode.urn,
    selectable: true,
    icon: () => {
      switch (treeNode.resource_type) {
        case "Database":
          return <Icons.Db2Database className="h-full" />;
        case "Table":
          return <Icons.Table className="h-full" />;
        case "Field":
          return <Icons.ShowDataCards className="h-full" />;
        default:
          return null;
      }
    },
    status: treeNode.change_indicator,
    isLeaf: !treeNode.has_grandchildren,
  }));

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

const MonitorTree = ({
  selectedNodeKeys,
  setSelectedNodeKeys,
  onClickClassifyButton,
}: {
  selectedNodeKeys: Key[];
  setSelectedNodeKeys: (keys: Key[]) => void;
  onClickClassifyButton: () => void;
}) => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const [trigger] = useLazyGetMonitorTreeQuery();
  const [nodePagination, setNodePaginationState] = useState<
    Record<string, PaginationState>
  >({});
  const [treeData, setTreeData] = useState<CustomTreeDataNode[]>([]);

  const onLoadData: TreeProps["loadData"] = ({ children, key }) => {
    return new Promise<void>((resolve) => {
      // if already loaded children, state will be used
      if (children) {
        resolve();
        return;
      }

      // First, trigger the fast query without ancestor details
      const queryParams = {
        monitor_config_id: monitorId,
        staged_resource_urn: key.toString(),
        size: TREE_PAGE_SIZE,
      };
      trigger({
        ...queryParams,
        include_descendant_details: false,
      }).then(({ data: fastData }) => {
        if (fastData) {
          setTreeData((origin) =>
            updateTreeData(
              origin,
              key,
              mapResponseToTreeData(fastData, key.toString()),
            ),
          );
          setNodePaginationState({
            ...nodePagination,
            [key.toString()]: { pageSize: TREE_PAGE_SIZE, pageIndex: 1 },
          });
        }

        // Immediately trigger the detailed query in the background
        trigger({
          ...queryParams,
          include_descendant_details: true,
        }).then(({ data: detailedData }) => {
          if (detailedData) {
            setTreeData((origin) =>
              updateTreeData(
                origin,
                key,
                mapResponseToTreeData(detailedData, key.toString()),
              ),
            );
          }
        });
      });

      resolve();
    });
  };

  const onLoadMore = (key: string) => {
    const currentNodePagination = nodePagination?.[key];

    if (currentNodePagination) {
      const newPage = currentNodePagination.pageIndex + 1;
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

      // First, trigger the fast query without ancestor details
      const queryParams = {
        monitor_config_id: monitorId,
        staged_resource_urn: key,
        size: TREE_PAGE_SIZE,
        page: newPage,
      };
      trigger({
        ...queryParams,
        include_descendant_details: false,
      }).then(({ data: fastData }) => {
        if (fastData) {
          setTreeData((origin) =>
            appendTreeNodeData(
              origin,
              key,
              mapResponseToTreeData(fastData, key),
            ),
          );
          setNodePaginationState({
            ...nodePagination,
            [key]: { pageSize: TREE_PAGE_SIZE, pageIndex: newPage },
          });
        }

        // Immediately trigger the detailed query in the background
        trigger({
          ...queryParams,
          include_descendant_details: true,
        }).then(({ data: detailedData }) => {
          if (detailedData) {
            setTreeData((origin) =>
              appendTreeNodeData(
                origin,
                key,
                mapResponseToTreeData(detailedData, key),
              ),
            );
          }
        });
      });
    }
  };

  useEffect(() => {
    const getInitTreeData = async () => {
      // First, trigger the fast query without ancestor details
      const { data: fastData } = await trigger({
        monitor_config_id: monitorId,
        size: TREE_PAGE_SIZE,
        include_descendant_details: false,
      });

      if (fastData && treeData.length <= 0) {
        setTreeData(mapResponseToTreeData(fastData));
      }

      // Immediately trigger the detailed query in the background
      trigger({
        monitor_config_id: monitorId,
        size: TREE_PAGE_SIZE,
        include_descendant_details: true,
      }).then(({ data: detailedData }) => {
        if (detailedData) {
          // Update tree data with the detailed version
          setTreeData(mapResponseToTreeData(detailedData));
        }
      });
    };

    getInitTreeData();
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [setTreeData]);

  return (
    <Flex gap="middle" vertical className="h-full">
      <Title level={3} className="sticky top-0">
        Schema explorer
      </Title>
      <Tree
        loadData={onLoadData}
        treeData={treeData}
        onSelect={(_, info) =>
          setSelectedNodeKeys(info.selectedNodes.map(({ key }) => key))
        }
        showIcon
        showLine
        blockNode
        multiple
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
            aria-label="Classify Selected Nodes"
            icon={<SparkleIcon />}
            size="small"
            onClick={onClickClassifyButton}
          />
        </Flex>
      )}
    </Flex>
  );
};

export default MonitorTree;

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
import { Key, useEffect, useState } from "react";

import { PaginationState } from "~/features/common/pagination";
import { useLazyGetMonitorTreeQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { Page_DatastoreStagedResourceTreeAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceTreeAPIResponse_";

import {
  TREE_NODE_LOAD_MORE_KEY_PREFIX,
  TREE_NODE_LOAD_MORE_TEXT,
  TREE_NODE_SKELETON_KEY_PREFIX,
  TREE_PAGE_SIZE,
} from "./MonitorFields.const";
import { MonitorTreeDataTitle } from "./MonitorTreeDataTitle";

const mapResponseToTreeData = (
  data: Page_DatastoreStagedResourceTreeAPIResponse_,
  key?: string,
): TreeDataNode[] => {
  const dataItems = data.items.map((treeNode) => ({
    title: treeNode.name,
    key: treeNode.urn,
    selectable: treeNode.has_children,
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
    isLeaf: !treeNode.has_children,
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
  list: TreeDataNode[],
  key: React.Key,
  children: TreeDataNode[],
): TreeDataNode[] =>
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
  list: TreeDataNode[],
  key: React.Key,
  children: TreeDataNode[],
): TreeDataNode[] =>
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
}: {
  selectedNodeKeys: Key[];
  setSelectedNodeKeys: (keys: Key[]) => void;
}) => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const [trigger] = useLazyGetMonitorTreeQuery();
  const [nodePagination, setNodePaginationState] = useState<
    Record<string, PaginationState>
  >({});
  const [treeData, setTreeData] = useState<TreeDataNode[]>([]);

  const onLoadData: TreeProps["loadData"] = ({ children, key }) => {
    return new Promise<void>((resolve) => {
      // if already loaded children, state will be used
      if (children) {
        resolve();
        return;
      }

      trigger({
        monitor_config_id: monitorId,
        staged_resource_urn: key.toString(),
        size: TREE_PAGE_SIZE,
      }).then(({ data }) => {
        if (data) {
          setTreeData((origin) =>
            updateTreeData(
              origin,
              key,
              mapResponseToTreeData(data, key.toString()),
            ),
          );
          setNodePaginationState({
            ...nodePagination,
            [key.toString()]: { pageSize: TREE_PAGE_SIZE, pageIndex: 1 },
          });
        }
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

      trigger({
        monitor_config_id: monitorId,
        staged_resource_urn: key,
        size: TREE_PAGE_SIZE,
        page: newPage,
      }).then(({ data }) => {
        if (data) {
          setTreeData((origin) =>
            appendTreeNodeData(origin, key, mapResponseToTreeData(data, key)),
          );
          setNodePaginationState({
            ...nodePagination,
            [key]: { pageSize: TREE_PAGE_SIZE, pageIndex: newPage },
          });
        }
      });
    }
  };

  useEffect(() => {
    const getInitTreeData = async () => {
      const { data } = await trigger({
        monitor_config_id: monitorId,
        size: TREE_PAGE_SIZE,
      });

      if (data && treeData.length <= 0) {
        setTreeData(mapResponseToTreeData(data));
      }
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
            aria-label="Run discovery"
            icon={<SparkleIcon />}
            size="small"
          />
        </Flex>
      )}
    </Flex>
  );
};

export default MonitorTree;

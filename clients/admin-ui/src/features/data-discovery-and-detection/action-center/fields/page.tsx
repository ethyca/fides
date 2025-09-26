import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntForm as Form,
  AntList as List,
  AntPagination as Pagination,
  AntProgress as Progress,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntSpace as Space,
  AntSplitter as Splitter,
  AntTag as Tag,
  AntText as Text,
  antTheme as theme,
  AntTitle as Title,
  AntTree as Tree,
  AntTreeDataNode as TreeDataNode,
  AntTreeProps as TreeProps,
  Icons,
  SparkleIcon,
} from "fidesui";
import { capitalize } from "lodash";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import FixedLayout from "~/features/common/FixedLayout";
import { useSearch } from "~/features/common/hooks";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { PaginationState } from "~/features/common/pagination";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import {
  useGetDatastoreFiltersQuery,
  useGetMonitorConfigQuery,
  useGetMonitorFieldsQuery,
  useLazyGetMonitorTreeQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DiffStatus } from "~/types/api";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";
import { Page_DatastoreStagedResourceTreeAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceTreeAPIResponse_";

import { RESOURCE_STATUS, useMonitorFieldsFilters } from "./useFilters";

const TREE_PAGE_SIZE = 100;
const FIELD_PAGE_SIZE = 25;
const TREE_NODE_LOAD_MORE_TEXT = "Load more...";
const TREE_NODE_LOAD_MORE_KEY_PREFIX = "load_more";
const TREE_NODE_SKELETON_KEY_PREFIX = "skeleton";

const mapResponseToTreeData = (
  data: Page_DatastoreStagedResourceTreeAPIResponse_,
  key?: string,
): TreeDataNode[] => {
  const dataItems = data.items.map((treeNode) => ({
    title: treeNode.name,
    key: treeNode.urn,
    selectable: treeNode.resource_type !== "Field",
    icon: () => {
      switch (treeNode.resource_type) {
        case "Database":
          return <Icons.Db2Database style={{ height: "100%" }} />;
        case "Table":
          return <Icons.Table style={{ height: "100%" }} />;
        case "Field":
          return <Icons.ShowDataCards style={{ height: "100%" }} />;
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

type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];
type ResourceStatusLabelColor = "nectar" | "red" | "orange" | "blue";

const ResourceStatus: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: ResourceStatusLabelColor;
  }
> = {
  classifying: { label: "Classifying", color: "blue" },
  classification_queued: { label: "Classifying", color: "blue" },
  classification_update: { label: "Classifying", color: "nectar" },
  classification_addition: { label: "In Review", color: "blue" },
  addition: { label: "In Review", color: "blue" },
  muted: { label: "Unmonitored", color: "nectar" },
  removal: { label: "Attention Required", color: "red" },
  removing: { label: "In Review", color: "nectar" },
  promoting: { label: "In Review", color: "nectar" },
  monitored: { label: "Approved", color: "nectar" },
} as const;

const intoDiffStatus = (resourceStatusLabel: ResourceStatusLabel) =>
  Object.values(DiffStatus).flatMap((status) =>
    ResourceStatus[status].label === resourceStatusLabel ? [status] : [],
  );

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
const { useToken } = theme;

const findNodeParent = (data: TreeDataNode[], key: string) => {
  return data.find((node) => {
    const { children } = node;
    return children && !!children.find((child) => child.key.toString() === key);
  });
};

const recFindNodeParent = (
  data: TreeDataNode[],
  key: string,
): TreeDataNode | null => {
  return data.reduce(
    (agg, current) => {
      if (current.children) {
        return (
          findNodeParent(current.children, key) ??
          recFindNodeParent(current.children, key)
        );
      }
      return agg;
    },
    null as null | TreeDataNode,
  );
};

const renderTreeDataTitle = (
  node: TreeDataNode,
  treeData: TreeDataNode[],
  onLoadMore: (key: string) => void,
) => {
  if (node.key.toString().startsWith(TREE_NODE_LOAD_MORE_KEY_PREFIX)) {
    const nodeParent = recFindNodeParent(treeData, node.key.toString());
    return (
      <Button
        type="link"
        block
        onClick={() => {
          if (nodeParent?.key) {
            onLoadMore(nodeParent?.key.toString());
          }
        }}
        style={{ padding: 0 }}
      >
        {typeof node.title === "function" ? node.title(node) : node.title}
      </Button>
    );
  }

  if (node.key.toString().startsWith(TREE_NODE_SKELETON_KEY_PREFIX)) {
    return (
      <Skeleton paragraph={false} title={{ width: "80px" }} active>
        {typeof node.title === "function" ? node.title(node) : node.title}
      </Skeleton>
    );
  }

  return (
    <Text
      ellipsis={{
        tooltip:
          typeof node.title === "function" ? node.title(node) : node.title,
      }}
    >
      {typeof node.title === "function" ? node.title(node) : node.title}
    </Text>
  );
};

const PopupFilters = ({
  resourceStatus,
  setResourceStatus,
  confidenceScore,
  setConfidenceScore,
  dataCategory,
  setDataCategory,
  reset,
  monitorId,
}: ReturnType<typeof useMonitorFieldsFilters> & { monitorId: string }) => {
  const { token } = useToken();
  const { data: datastoreFilterResponse } = useGetDatastoreFiltersQuery({
    monitor_config_id: monitorId,
  });

  return (
    <div
      style={{
        backgroundColor: token.colorBgElevated,
        borderRadius: token.borderRadiusLG,
        boxShadow: token.boxShadowSecondary,
      }}
    >
      <Space size="middle" style={{ padding: token.paddingMD }}>
        <Form layout="vertical">
          <Form.Item
            label="Status"
            style={{
              width: "min-content",
              whiteSpace: "nowrap",
            }}
          >
            <Checkbox.Group
              value={resourceStatus || []}
              onChange={(value) =>
                setResourceStatus(value.length > 0 ? value : null)
              }
            >
              <Row>
                {RESOURCE_STATUS.map((label) => {
                  return (
                    <Col span={24} key={label}>
                      <Checkbox value={label}>{label}</Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </Form.Item>
          <Form.Item
            label="Confidence Score"
            style={{
              width: "min-content",
              whiteSpace: "nowrap",
            }}
          >
            <Checkbox.Group
              value={confidenceScore || []}
              onChange={(scores) =>
                setConfidenceScore(scores.length > 0 ? scores : null)
              }
            >
              <Row>
                {Object.values(ConfidenceScoreRange).map((cs) => {
                  return (
                    <Col span={24} key={cs}>
                      <Checkbox value={cs}>{capitalize(cs)}</Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </Form.Item>
          {datastoreFilterResponse?.data_category &&
            datastoreFilterResponse?.data_category?.length > 0 && (
              <Form.Item
                label="Data Category"
                style={{
                  width: "min-content",
                  whiteSpace: "nowrap",
                }}
              >
                <Checkbox.Group
                  value={dataCategory || []}
                  onChange={(values) =>
                    setDataCategory(values.length > 0 ? values : null)
                  }
                >
                  <Row>
                    {datastoreFilterResponse.data_category.map((value) => {
                      return (
                        <Col span={24} key={value}>
                          <Checkbox value={value}>{capitalize(value)}</Checkbox>
                        </Col>
                      );
                    })}
                  </Row>
                </Checkbox.Group>
              </Form.Item>
            )}
          <Button
            onClick={() => {
              reset();
            }}
          >
            Clear
          </Button>
        </Form>
      </Space>
    </div>
  );
};

const ActionCenterFields: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const { paginationProps, pageIndex, pageSize } = useAntPagination({
    defaultPageSize: FIELD_PAGE_SIZE,
  });
  const search = useSearch();
  const { resourceStatus, confidenceScore, ...restMonitorFieldsFilters } =
    useMonitorFieldsFilters();
  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });
  const [trigger] = useLazyGetMonitorTreeQuery();
  const [selectedNodes, setSelectedNodes] = useState<TreeDataNode[]>([]);
  const [nodePagination, setNodePaginationState] = useState<
    Record<string, PaginationState>
  >({});
  const { data: fieldsDataResponse } = useGetMonitorFieldsQuery({
    monitor_config_id: monitorId,
    size: pageSize,
    page: pageIndex,
    staged_resource_urn: selectedNodes.map(({ key }) => key.toString()),
    search: search.searchProps.value,
    diff_status: resourceStatus
      ? resourceStatus.flatMap(intoDiffStatus)
      : undefined,
    confidence_score: confidenceScore || undefined,
  });
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
    <FixedLayout
      title="Action center - Discovered assets by system"
      mainProps={{ overflow: "hidden" }}
    >
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
        isSticky={false}
      />
      <Splitter style={{ height: "calc(100% - 48px)", overflow: "hidden" }}>
        <Splitter.Panel
          defaultSize={250}
          style={{ paddingRight: "var(--ant-padding-md)" }}
        >
          <Flex
            gap="middle"
            vertical
            style={{ height: "-webkit-fill-available", maxHeight: "100%" }}
          >
            <Title
              level={3}
              style={{
                position: "sticky",
                top: "0px",
              }}
            >
              Schema explorer
            </Title>
            <Tree
              loadData={onLoadData}
              treeData={treeData}
              onSelect={(_, info) => setSelectedNodes(info.selectedNodes)}
              showIcon
              showLine
              blockNode
              multiple
              rootStyle={{
                height: "-webkit-fill-available",
                overflowX: "hidden",
              }}
              style={{}}
              titleRender={(node) =>
                renderTreeDataTitle(node, treeData, onLoadMore)
              }
            />
            {selectedNodes.length > 0 && (
              <Flex justify="space-between" align="center">
                <span>{selectedNodes.length} selected</span>
                <Button icon={<SparkleIcon />} size="small" />
              </Flex>
            )}
          </Flex>
        </Splitter.Panel>
        <Splitter.Panel style={{ paddingLeft: "var(--ant-padding-md)" }}>
          <Flex
            vertical
            gap="middle"
            style={{ height: "100%", overflow: "hidden" }}
          >
            <Flex justify="space-between">
              <Title level={2}>Monitor results</Title>
              <Flex align="center">
                {monitorConfigData?.last_monitored && (
                  <Text type="secondary">
                    Last scan:{" "}
                    {new Date(
                      monitorConfigData?.last_monitored,
                    ).toLocaleString()}
                  </Text>
                )}
              </Flex>
            </Flex>

            <Flex justify="space-between">
              <DebouncedSearchInput
                value={search.searchQuery}
                onChange={search.updateSearch}
                placeholder="Search"
              />
              <Flex gap="small">
                <Dropdown
                  trigger={["click"]}
                  /* I don't like disabling linting but this pattern is inherit to ant-d */
                  /* eslint-disable-next-line react/no-unstable-nested-components */
                  popupRender={() => (
                    <PopupFilters
                      resourceStatus={resourceStatus}
                      confidenceScore={confidenceScore}
                      {...restMonitorFieldsFilters}
                      monitorId={monitorId}
                    />
                  )}
                >
                  <Button icon={<Icons.ChevronDown />} iconPosition="end">
                    Filter
                  </Button>
                </Dropdown>
                <Dropdown menu={{ items: [] }}>
                  <Button
                    type="primary"
                    icon={<Icons.ChevronDown />}
                    iconPosition="end"
                  >
                    Actions
                  </Button>
                </Dropdown>
              </Flex>
            </Flex>
            <List
              dataSource={fieldsDataResponse?.items}
              style={{ overflow: "scroll" }}
              renderItem={(item) => (
                <List.Item
                  key={item.urn}
                  actions={[
                    item.classifications && item.classifications.length > 0 && (
                      <Flex
                        gap="small"
                        align="center"
                        style={{ paddingRight: "var(--ant-padding-xl)" }}
                        key="progress"
                      >
                        <Progress
                          percent={
                            item.classifications.find(
                              (classification) =>
                                classification.confidence_score ===
                                ConfidenceScoreRange.HIGH,
                            )
                              ? 100
                              : 25
                          }
                          percentPosition={{
                            align: "start",
                            type: "outer",
                          }}
                          strokeColor={
                            item.classifications.find(
                              (classification) =>
                                classification.confidence_score ===
                                ConfidenceScoreRange.HIGH,
                            )
                              ? "var(--ant-color-success-text)"
                              : "var(--ant-color-warning-text)"
                          }
                          steps={2}
                          showInfo={false}
                          strokeLinecap="round"
                          size={[24, 8]}
                        />
                        <Text
                          size="sm"
                          type="secondary"
                          style={{
                            fontWeight: "normal",
                          }}
                        >
                          {capitalize(
                            item.classifications.find(
                              (classification) =>
                                classification.confidence_score ===
                                ConfidenceScoreRange.HIGH,
                            )
                              ? ConfidenceScoreRange.HIGH
                              : ConfidenceScoreRange.LOW,
                          )}
                        </Text>
                      </Flex>
                    ),
                    item.classifications && item.classifications.length > 0 && (
                      <Button
                        icon={<Icons.Checkmark />}
                        size="small"
                        key="approve"
                      />
                    ),
                    item.classifications && item.classifications.length > 0 && (
                      <Button icon={<Icons.Close />} size="small" key="deny" />
                    ),
                    <Button
                      icon={<SparkleIcon />}
                      size="small"
                      key="reclassify"
                    />,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Checkbox />}
                    title={
                      <Flex justify="space-between">
                        <Flex
                          gap="small"
                          align="center"
                          style={{ width: "100%" }}
                        >
                          {item.name}
                          {item.diff_status && (
                            <Tag
                              bordered={false}
                              color={ResourceStatus[item.diff_status].color}
                              style={{
                                fontWeight: "normal",
                                fontSize: "var(--ant-font-size-sm)",
                              }}
                            >
                              {ResourceStatus[item.diff_status].label}
                            </Tag>
                          )}
                          <Text
                            size="sm"
                            type="secondary"
                            style={{
                              fontWeight: "normal",
                              overflow: "hidden",
                            }}
                            ellipsis={{ tooltip: item.urn }}
                          >
                            {item.urn}
                          </Text>
                        </Flex>
                      </Flex>
                    }
                    description={
                      <>
                        <Button type="text" icon={<Icons.Add />} size="small" />
                        {item.classifications?.map((c) => (
                          <Tag
                            bordered
                            color="white"
                            closable
                            icon={<SparkleIcon />}
                            style={{ color: "var(--ant-color-text)" }}
                            key={c.label}
                          >
                            {c.label}
                          </Tag>
                        ))}
                        {item.user_assigned_data_categories?.map((c) => (
                          <Tag
                            bordered
                            color="white"
                            closable
                            style={{ color: "var(--ant-color-text)" }}
                            key={c}
                          >
                            {c}
                          </Tag>
                        ))}
                      </>
                    }
                  />
                </List.Item>
              )}
            />
            <Pagination
              {...paginationProps}
              showSizeChanger={false}
              total={fieldsDataResponse?.total || 0}
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>
    </FixedLayout>
  );
};

export default ActionCenterFields;

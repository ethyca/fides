import {
  AntAvatar as Avatar,
  AntButton as Button,
  AntDrawer as Drawer,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntList as List,
  AntPagination as Pagination,
  AntSplitter as Splitter,
  AntTag as Tag,
  AntText as Text,
  AntTitle as Title,
  Icons,
  SparkleIcon,
  useToast,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { Key, useEffect, useState } from "react";

import { ClassifierProgress } from "~/features/classifier/ClassifierProgress";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import FixedLayout from "~/features/common/FixedLayout";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert, useSearch } from "~/features/common/hooks";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useClassifyStagedResourcesMutation,
  useGetMonitorConfigQuery,
  useGetMonitorFieldsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useLazyGetStagedResourceDetailsQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  usePromoteResourcesMutation,
  useUpdateResourceCategoryMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { Database, DiffStatus, Field, Schema, Table } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { MonitorFieldFilters } from "./MonitorFieldFilters";
import renderMonitorFieldListItem from "./MonitorFieldListItem";
import {
  FIELD_PAGE_SIZE,
  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL,
  ResourceStatusLabel,
} from "./MonitorFields.const";
import MonitorTree from "./MonitorTree";
import { useMonitorFieldsFilters } from "./useFilters";

const DrawerTitle = ({
  name,
  diff_status,
}: Field | Schema | Database | Table) => {
  return (
    <Flex align="center" gap="small">
      <Icons.ShowDataCards />
      <Flex>{name}</Flex>
      {!!diff_status && (
        <Tag
          bordered={false}
          color={MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].color}
          className="font-normal text-[var(--ant-font-size-sm)]"
        >
          {MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].label}
        </Tag>
      )}
    </Flex>
  );
};

const intoDiffStatus = (resourceStatusLabel: ResourceStatusLabel) =>
  Object.values(DiffStatus).flatMap((status) =>
    MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[status].label ===
    resourceStatusLabel
      ? [status]
      : [],
  );

const ActionCenterFields: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: FIELD_PAGE_SIZE,
    });
  const search = useSearch();
  const {
    resourceStatus,
    confidenceScore,
    dataCategory,
    ...restMonitorFieldsFilters
  } = useMonitorFieldsFilters();
  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });
  const [selectedNodeKeys, setSelectedNodeKeys] = useState<Key[]>([]);
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const { data: fieldsDataResponse } = useGetMonitorFieldsQuery({
    monitor_config_id: monitorId,
    size: pageSize,
    page: pageIndex,
    staged_resource_urn: selectedNodeKeys.map((key) => key.toString()),
    search: search.searchProps.value,
    diff_status: resourceStatus
      ? resourceStatus.flatMap(intoDiffStatus)
      : undefined,
    confidence_score: confidenceScore || undefined,
    data_category: dataCategory || undefined,
  });
  const toast = useToast();
  const [classifyStagedResourcesMutation] =
    useClassifyStagedResourcesMutation();
  const [updateResourceCategoryMutation] = useUpdateResourceCategoryMutation();
  const [ignoreMonitorResultAssetsMutation] =
    useIgnoreMonitorResultAssetsMutation();
  const { errorAlert } = useAlert();
  const [promoteResources] = usePromoteResourcesMutation();
  const [detailsUrn, setDetailsUrn] = useState<string>();
  const [stagedResourceDetailsTrigger, stagedResourceDetailsResult] =
    useLazyGetStagedResourceDetailsQuery();
  const resource = stagedResourceDetailsResult.currentData;

  const handleSetDataCategories = async (
    dataCategories: string[],
    urn: string,
  ) => {
    const mutationResult = await updateResourceCategoryMutation({
      monitor_config_id: monitorId,
      staged_resource_urn: urn,
      user_assigned_data_categories: dataCategories,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handleNavigate = async (urn: string) => {
    setDetailsUrn(urn);
  };

  const handleIgnore = async (urn: string) => {
    const mutationResult = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handlePromote = async (urns: string[]) => {
    const mutationResult = await promoteResources({
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handleClassifyStagedResources = async () => {
    const result = await classifyStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: selectedNodeKeys.flatMap((key) =>
        typeof key !== "bigint" ? [key.toString()] : [],
      ),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    toast(successToastParams(`Classifying initiated`));
  };

  useEffect(() => {
    if (detailsUrn) {
      stagedResourceDetailsTrigger({ stagedResourceUrn: detailsUrn });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detailsUrn]);

  /**
   * @todo: this should be handled on a form/state action level
   */
  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    resourceStatus,
    confidenceScore,
    selectedNodeKeys,
    search.searchQuery,
    dataCategory,
  ]);

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
      <Splitter className="h-[calc(100%-48px)] overflow-hidden">
        <Splitter.Panel
          defaultSize={250}
          /** Note: style attr used here due to specificity of ant css. */
          style={{ paddingRight: "var(--ant-padding-md)" }}
        >
          <MonitorTree
            selectedNodeKeys={selectedNodeKeys}
            setSelectedNodeKeys={setSelectedNodeKeys}
            onClickClassifyButton={handleClassifyStagedResources}
          />
        </Splitter.Panel>
        {/** Note: style attr used here due to specificity of ant css. */}
        <Splitter.Panel style={{ paddingLeft: "var(--ant-padding-md)" }}>
          <Flex vertical gap="middle" className="h-full overflow-hidden">
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
                    <MonitorFieldFilters
                      resourceStatus={resourceStatus}
                      confidenceScore={confidenceScore}
                      dataCategory={dataCategory}
                      {...restMonitorFieldsFilters}
                      monitorId={monitorId}
                    />
                  )}
                >
                  <Button icon={<Icons.ChevronDown />} iconPosition="end">
                    Filter
                  </Button>
                </Dropdown>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: "promote",
                        onClick: () => handlePromote(selectedFields),
                        label: "Promote",
                      },
                    ],
                  }}
                  disabled={selectedFields.length <= 0}
                >
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
              className="overflow-scroll"
              renderItem={(props) =>
                renderMonitorFieldListItem({
                  ...props,
                  selected: selectedFields.includes(props.urn),
                  onSelect: (key, selected) =>
                    selected
                      ? setSelectedFields([...selectedFields, key])
                      : setSelectedFields(
                          selectedFields.filter((val) => val !== key),
                        ),
                  onSetDataCategories: handleSetDataCategories,
                  onNavigate: handleNavigate,
                  onIgnore: handleIgnore,
                })
              }
            />
            <Pagination
              {...paginationProps}
              showSizeChanger={false}
              total={fieldsDataResponse?.total || 0}
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>
      <Drawer
        title={resource ? <DrawerTitle {...resource} /> : null}
        footer={
          <Flex gap="small" justify="flex-end">
            <Button>Reject</Button>
            <Button>Approve</Button>
            <Button type="primary">Confirm</Button>
          </Flex>
        }
        open={!!detailsUrn}
        onClose={() => setDetailsUrn(undefined)}
        size="large"
      >
        {resource ? (
          <>
            <Form layout="vertical">
              <Form.Item label="System">
                <Input value={resource.monitor_config_id ?? ""} disabled />
              </Form.Item>
              <Form.Item label="Path">
                <Input value={resource.urn} disabled />
              </Form.Item>
              <Form.Item label="Data type">
                <Input value={resource.resource_type ?? ""} disabled />
              </Form.Item>
              <Form.Item label="Description">
                <Input.TextArea value={resource.description ?? ""} />
              </Form.Item>
              <Form.Item label="Data categories">
                <DataCategorySelect
                  variant="outlined"
                  mode="tags"
                  maxTagCount="responsive"
                  value={[
                    ...(resource.classifications?.map(({ label }) => label) ??
                      []),
                    ...(resource.user_assigned_data_categories?.map(
                      (value) => value,
                    ) ?? []),
                  ]}
                  autoFocus={false}
                  onChange={(value) =>
                    handleSetDataCategories(value, resource.urn)
                  }
                />
              </Form.Item>
            </Form>
            {resource.classifications &&
              resource.classifications.length > 0 && (
                <List
                  dataSource={resource.classifications}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar style={{backgroundColor: "#FAFAFA"}} icon={<SparkleIcon color="black" />} />}
                        title={
                          <Flex align="center" gap="small">
                            <div>{item.label}</div>
                            <ClassifierProgress percent={item.score} />
                          </Flex>
                        }
                        description={item.rationale}
                      />
                    </List.Item>
                  )}
                />
              )}
          </>
        ) : null}
      </Drawer>
    </FixedLayout>
  );
};

export default ActionCenterFields;

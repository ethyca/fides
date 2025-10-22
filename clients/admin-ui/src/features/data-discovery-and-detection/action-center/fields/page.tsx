import {
  AntAvatar as Avatar,
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDescriptions as Descriptions,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntForm as Form,
  AntList as List,
  AntPagination as Pagination,
  AntSplitter as Splitter,
  AntText as Text,
  AntTitle as Title,
  Icons,
  SparkleIcon,
  useToast,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
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
  useIgnoreMonitorResultAssetsMutation,
  useLazyGetStagedResourceDetailsQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { useUpdateResourceCategoryMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiffStatus } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { DetailsDrawer } from "./DetailsDrawer";
import { DROPDOWN_OPTIONS, FIELD_ACTION_LABEL } from "./FieldActions.const";
import {
  useFieldActionsMutation,
  useGetMonitorFieldsQuery,
} from "./monitor-fields.slice";
import { MonitorFieldFilters } from "./MonitorFieldFilters";
import renderMonitorFieldListItem from "./MonitorFieldListItem";
import {
  FIELD_PAGE_SIZE,
  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL,
} from "./MonitorFields.const";
import MonitorTree from "./MonitorTree";
import { FieldActionTypeValue, ResourceStatusLabel } from "./types";
import { useMonitorFieldsFilters } from "./useFilters";

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
  const [selectAll, setSelectAll] = useState<boolean>(false);
  const { data: fieldsDataResponse } = useGetMonitorFieldsQuery({
    path: {
      monitor_config_id: monitorId,
    },
    query: {
      size: pageSize,
      page: pageIndex,
      staged_resource_urn: selectedNodeKeys.map((key) => key.toString()),
      search: search.searchProps.value,
      diff_status: resourceStatus
        ? resourceStatus.flatMap(intoDiffStatus)
        : undefined,
      confidence_score: confidenceScore || undefined,
      data_category: dataCategory || undefined,
    },
  });
  const toast = useToast();
  const [classifyStagedResourcesMutation] =
    useClassifyStagedResourcesMutation();
  const [updateResourceCategoryMutation] = useUpdateResourceCategoryMutation();
  const [ignoreMonitorResultAssetsMutation] =
    useIgnoreMonitorResultAssetsMutation();
  const { errorAlert } = useAlert();
  const [bulkAction] = useFieldActionsMutation();
  const [detailsUrn, setDetailsUrn] = useState<string>();
  const [stagedResourceDetailsTrigger, stagedResourceDetailsResult] =
    useLazyGetStagedResourceDetailsQuery();
  const resource = stagedResourceDetailsResult.data;

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

  const handleBulkAction = async (actionType: FieldActionTypeValue) => {
    const mutationResult = await bulkAction({
      query: {
        staged_resource_urn: selectedNodeKeys.map((key) => key.toString()),
        search: search.searchProps.value,
        diff_status: resourceStatus
          ? resourceStatus.flatMap(intoDiffStatus)
          : undefined,
        confidence_score: confidenceScore || undefined,
        data_category: dataCategory || undefined,
      },
      path: {
        monitor_config_id: monitorId,
        action_type: actionType,
      },
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    const actionItemCount = mutationResult.data.task_ids?.length ?? 0;
    toast(
      successToastParams(
        `Successful ${FIELD_ACTION_LABEL[actionType]} action for ${actionItemCount} item${actionItemCount !== 1 ? "s" : ""}`,
      ),
    );
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

  const handleOnSelectAll = (nextSelectAll: boolean) => {
    setSelectAll(nextSelectAll);
    setSelectedFields(
      nextSelectAll && fieldsDataResponse
        ? fieldsDataResponse.items.map((item) => item.urn)
        : [],
    );
  };

  const handleOnSelect = (key: string, selected?: boolean) => {
    setSelectAll(false);
    setSelectedFields(
      selected
        ? [...selectedFields, key]
        : selectedFields.filter((val) => val !== key),
    );
  };

  const selectedFieldCount =
    selectAll && fieldsDataResponse?.total
      ? fieldsDataResponse?.total
      : selectedFields.length;
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
      fullHeight
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
                      ...DROPDOWN_OPTIONS.map((actionType) => ({
                        key: actionType,
                        label: FIELD_ACTION_LABEL[actionType],
                        onClick: () => handleBulkAction(actionType),
                      })),
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
            <Flex gap="middle">
              <Checkbox
                checked={selectAll}
                onChange={(e) => handleOnSelectAll(e.target.checked)}
              />
              <Text>Select all</Text>
              {!!selectedFieldCount && (
                <Text strong>
                  {selectedFieldCount.toLocaleString()} selected
                </Text>
              )}
            </Flex>
            <List
              dataSource={fieldsDataResponse?.items}
              className="overflow-scroll"
              renderItem={(props) =>
                renderMonitorFieldListItem({
                  ...props,
                  selected: selectedFields.includes(props.urn),
                  onSelect: handleOnSelect,
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
      <DetailsDrawer
        itemKey={resource?.urn ?? 0}
        title={resource ? resource.name : null}
        titleIcon={<Icons.Column />}
        titleTag={{
          bordered: false,
          color: resource?.diff_status
            ? MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[resource.diff_status]
                .color
            : undefined,
          className: "font-normal text-[var(--ant-font-size-sm)]",
          children: resource?.diff_status
            ? MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[resource.diff_status]
                .label
            : null,
        }}
        actions={{
          reject: {
            label: "Reject",
            callback: () => {},
          },
          approve: {
            label: "Approve",
            callback: () => {},
          },
          confirm: {
            label: "Confirm",
            callback: () => {},
          },
        }}
        open={!!detailsUrn}
        onClose={() => setDetailsUrn(undefined)}
      >
        {resource ? (
          <Flex gap="middle" vertical>
            <Descriptions
              bordered
              column={1}
              items={[
                {
                  key: "system",
                  label: "System",
                  children: resource.system_key,
                },
                {
                  key: "path",
                  label: "Path",
                  children: resource.urn,
                },

                {
                  key: "data-type",
                  label: "Data type",
                  children:
                    resource.resource_type /** data type is not yet returned from the BE for the details query * */,
                },
                {
                  key: "description",
                  label: "Description",
                  children: resource.description,
                },
              ]}
            />
            <Form layout="vertical">
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
                        avatar={
                          <Avatar
                            /* Ant only provides style prop for altering the background color */
                            style={{
                              backgroundColor: palette?.FIDESUI_BG_DEFAULT,
                            }}
                            icon={<SparkleIcon color="black" />}
                          />
                        }
                        title={
                          <Flex align="center" gap="middle">
                            <div>{item.label}</div>
                            <ClassifierProgress percent={item.score * 100} />
                          </Flex>
                        }
                        description={item.rationale}
                      />
                    </List.Item>
                  )}
                />
              )}
          </Flex>
        ) : null}
      </DetailsDrawer>
    </FixedLayout>
  );
};

export default ActionCenterFields;

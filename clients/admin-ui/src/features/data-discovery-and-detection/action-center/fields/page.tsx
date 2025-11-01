import {
  AntAvatar as Avatar,
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDescriptions as Descriptions,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntForm as Form,
  AntList as List,
  AntMessage as message,
  AntModal as modal,
  AntPagination as Pagination,
  AntSplitter as Splitter,
  AntText as Text,
  AntTitle as Title,
  AntTooltip as Tooltip,
  Icons,
  SparkleIcon,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { Key, useEffect, useRef, useState } from "react";

import { ClassifierProgress } from "~/features/classifier/ClassifierProgress";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import FixedLayout from "~/features/common/FixedLayout";
import { useSearch } from "~/features/common/hooks";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import {
  useGetMonitorConfigQuery,
  useLazyGetStagedResourceDetailsQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DiffStatus } from "~/types/api";
import { DatastoreStagedResourceAPIResponse } from "~/types/api/models/DatastoreStagedResourceAPIResponse";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import { DetailsDrawer } from "./DetailsDrawer";
import {
  AVAILABLE_ACTIONS,
  DRAWER_ACTIONS,
  DROPDOWN_ACTIONS,
  DROPDOWN_ACTIONS_DISABLED_TOOLTIP,
  FIELD_ACTION_ICON,
  FIELD_ACTION_LABEL,
  LIST_ITEM_ACTIONS,
} from "./FieldActions.const";
import {
  useGetMonitorFieldsQuery,
  useLazyGetAllowedActionsQuery,
} from "./monitor-fields.slice";
import { MonitorFieldFilters } from "./MonitorFieldFilters";
import renderMonitorFieldListItem from "./MonitorFieldListItem";
import {
  DIFF_TO_RESOURCE_STATUS,
  FIELD_PAGE_SIZE,
  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL,
  ResourceStatusLabel,
} from "./MonitorFields.const";
import MonitorTree, { MonitorTreeRef } from "./MonitorTree";
import { useBulkActions } from "./useBulkActions";
import { extractListItemKeys, useBulkListSelect } from "./useBulkListSelect";
import { getAvailableActions, useFieldActions } from "./useFieldActions";
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
  const monitorTreeRef = useRef<MonitorTreeRef>(null);
  const [messageApi, messageContext] = message.useMessage();
  const [modalApi, modalContext] = modal.useModal();
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
  const baseMonitorFilters = {
    path: {
      monitor_config_id: monitorId,
    },
    query: {
      staged_resource_urn: selectedNodeKeys.map((key) => key.toString()),
      search: search.searchProps.value,
      diff_status: resourceStatus
        ? resourceStatus.flatMap(intoDiffStatus)
        : undefined,
      confidence_score: confidenceScore || undefined,
      data_category: dataCategory || undefined,
    },
  };

  const {
    data: fieldsDataResponse,
    isFetching,
    refetch,
  } = useGetMonitorFieldsQuery({
    ...baseMonitorFilters,
    query: {
      ...baseMonitorFilters.query,
      size: pageSize,
      page: pageIndex,
    },
  });
  const [detailsUrn, setDetailsUrn] = useState<string>();
  const [stagedResourceDetailsTrigger, stagedResourceDetailsResult] =
    useLazyGetStagedResourceDetailsQuery();

  const [
    allowedActionsTrigger,
    { data: allowedActionsResult, isFetching: isFetchingAllowedActions },
  ] = useLazyGetAllowedActionsQuery();
  const resource = stagedResourceDetailsResult.data;
  const bulkActions = useBulkActions(
    monitorId,
    modalApi,
    messageApi,
    async (urns: string[]) => {
      await monitorTreeRef.current?.refreshResourcesAndAncestors(urns);
    },
  );
  const fieldActions = useFieldActions(
    monitorId,
    modalApi,
    messageApi,
    async (urns: string[]) => {
      await monitorTreeRef.current?.refreshResourcesAndAncestors(urns);
    },
  );
  const {
    excludedListItems,
    indeterminate,
    isBulkSelect,
    listSelectMode,
    resetListSelect,
    selectedListItems,
    updateListItems,
    updateListSelectMode,
    updateSelectedListItem,
  } = useBulkListSelect<
    DatastoreStagedResourceAPIResponse & { itemKey: React.Key }
  >();

  const handleNavigate = async (urn: string) => {
    setDetailsUrn(urn);
  };

  const onActionDropdownOpenChange = (open: boolean) => {
    if (open && isBulkSelect) {
      allowedActionsTrigger({
        ...baseMonitorFilters,
        query: {
          ...baseMonitorFilters.query,
        },
        body: {
          excluded_resource_urns: extractListItemKeys(excludedListItems).map(
            (itemKey) => itemKey.toString(),
          ),
        },
      });
    }
  };

  const availableActions = isBulkSelect
    ? allowedActionsResult?.allowed_actions
    : getAvailableActions(
        selectedListItems.flatMap((field) =>
          field.diff_status ? [DIFF_TO_RESOURCE_STATUS[field.diff_status]] : [],
        ),
      );
  const responseCount = fieldsDataResponse?.total ?? 0;
  const selectedListItemCount =
    listSelectMode === "exclusive" && fieldsDataResponse?.total
      ? responseCount - excludedListItems.length
      : selectedListItems.length;

  useEffect(() => {
    if (fieldsDataResponse) {
      updateListItems(
        fieldsDataResponse.items.map(({ urn, ...rest }) => ({
          itemKey: urn,
          urn,
          ...rest,
        })),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fieldsDataResponse?.items]);

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
    resetListSelect();
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
            ref={monitorTreeRef}
            selectedNodeKeys={selectedNodeKeys}
            setSelectedNodeKeys={setSelectedNodeKeys}
            onClickClassifyButton={() => {
              fieldActions.classify(
                selectedNodeKeys.map((key) => key.toString()),
              );
            }}
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
                <MonitorFieldFilters
                  resourceStatus={resourceStatus}
                  confidenceScore={confidenceScore}
                  dataCategory={dataCategory}
                  {...restMonitorFieldsFilters}
                  monitorId={monitorId}
                  stagedResourceUrn={selectedNodeKeys.map((key) =>
                    key.toString(),
                  )}
                />
                <Dropdown
                  onOpenChange={onActionDropdownOpenChange}
                  menu={{
                    items: [
                      ...DROPDOWN_ACTIONS.map((actionType) => ({
                        key: actionType,
                        label:
                          isFetchingAllowedActions ||
                          !availableActions?.includes(actionType) ? (
                            <Tooltip
                              title={
                                DROPDOWN_ACTIONS_DISABLED_TOOLTIP[actionType]
                              }
                            >
                              {FIELD_ACTION_LABEL[actionType]}
                            </Tooltip>
                          ) : (
                            FIELD_ACTION_LABEL[actionType]
                          ),
                        disabled:
                          isFetchingAllowedActions ||
                          !availableActions?.includes(actionType),
                        onClick: () => {
                          if (isBulkSelect) {
                            bulkActions[actionType](
                              baseMonitorFilters,
                              excludedListItems.map((k) =>
                                k.itemKey.toString(),
                              ),
                              selectedListItemCount,
                            );
                          } else {
                            fieldActions[actionType](
                              selectedListItems.map(({ itemKey }) =>
                                itemKey.toString(),
                              ),
                            );
                          }
                        },
                      })),
                    ],
                  }}
                  disabled={selectedListItems.length <= 0}
                >
                  <Button
                    type="primary"
                    icon={<Icons.ChevronDown />}
                    iconPosition="end"
                    loading={isFetchingAllowedActions}
                  >
                    Actions
                  </Button>
                </Dropdown>
                <Tooltip title="Refresh">
                  <Button
                    icon={<Icons.Renew />}
                    onClick={() => refetch()}
                    aria-label="Refresh"
                  />
                </Tooltip>
              </Flex>
            </Flex>
            <Flex gap="middle" align="center">
              <Checkbox
                id="select-all"
                checked={isBulkSelect}
                indeterminate={indeterminate}
                onChange={(e) =>
                  updateListSelectMode(
                    e.target.checked ? "exclusive" : "inclusive",
                  )
                }
              />
              <label htmlFor="select-all">Select all</label>
              {!!selectedListItemCount && (
                <Text strong>
                  {selectedListItemCount.toLocaleString()} selected
                </Text>
              )}
            </Flex>
            <List
              dataSource={fieldsDataResponse?.items}
              enableKeyboardShortcuts
              className="h-full overflow-scroll"
              loading={isFetching}
              renderItem={(props) =>
                renderMonitorFieldListItem({
                  ...props,
                  selected: extractListItemKeys(selectedListItems).includes(
                    props.urn,
                  ),
                  onSelect: updateSelectedListItem,
                  onNavigate: handleNavigate,
                  onSetDataCategories: (urn, values) =>
                    fieldActions["assign-categories"]([urn], {
                      user_assigned_data_categories: values,
                    }),
                  dataCategoriesDisabled: props?.diff_status
                    ? ![
                        ...AVAILABLE_ACTIONS[
                          DIFF_TO_RESOURCE_STATUS[props.diff_status]
                        ],
                      ].includes(FieldActionType.ASSIGN_CATEGORIES)
                    : true,
                  actions: props?.diff_status
                    ? LIST_ITEM_ACTIONS.map((action) => (
                        <Tooltip
                          key={action}
                          title={FIELD_ACTION_LABEL[action]}
                        >
                          <Button
                            aria-label={FIELD_ACTION_LABEL[action]}
                            icon={FIELD_ACTION_ICON[action]}
                            onClick={() => fieldActions[action]([props.urn])}
                            disabled={
                              props?.diff_status
                                ? ![
                                    ...AVAILABLE_ACTIONS[
                                      DIFF_TO_RESOURCE_STATUS[props.diff_status]
                                    ],
                                  ].includes(action)
                                : true
                            }
                            style={{
                              // Hack: because Sparkle is so weird, and Ant is using `inline-block`
                              // for actions, this is needed to get the buttons to align correctly.
                              fontSize:
                                "var(--ant-button-content-font-size-lg)",
                            }}
                          />
                        </Tooltip>
                      ))
                    : [],
                })
              }
            />
            <Pagination
              {...paginationProps}
              showSizeChanger={{
                suffixIcon: <Icons.ChevronDown />,
              }}
              total={fieldsDataResponse?.total || 0}
              hideOnSinglePage={
                // if we're on the smallest page size, and there's only one page, hide the pagination
                paginationProps.pageSize?.toString() ===
                paginationProps.pageSizeOptions?.[0]
              }
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>
      <DetailsDrawer
        itemKey={resource?.urn ?? ""}
        title={resource?.name ?? null}
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
        actions={DRAWER_ACTIONS.map((action) => ({
          label: FIELD_ACTION_LABEL[action],
          callback: (value) => fieldActions[action]([value]),
          disabled: resource?.diff_status
            ? ![
                ...AVAILABLE_ACTIONS[
                  DIFF_TO_RESOURCE_STATUS[resource.diff_status]
                ],
              ].includes(action)
            : false,
        }))}
        open={!!detailsUrn}
        onClose={() => setDetailsUrn(undefined)}
      >
        {resource ? (
          <Flex gap="middle" vertical>
            <Descriptions
              bordered
              size="small"
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
                  mode="multiple"
                  maxTagCount="responsive"
                  value={[
                    ...(resource.classifications?.map(({ label }) => label) ??
                      []),
                    ...(resource.user_assigned_data_categories?.map(
                      (value) => value,
                    ) ?? []),
                  ]}
                  autoFocus={false}
                  disabled={
                    resource?.diff_status
                      ? ![
                          ...AVAILABLE_ACTIONS[
                            DIFF_TO_RESOURCE_STATUS[resource.diff_status]
                          ],
                        ].includes(FieldActionType.ASSIGN_CATEGORIES)
                      : true
                  }
                  onChange={(values) =>
                    fieldActions["assign-categories"]([resource.urn], {
                      user_assigned_data_categories: values,
                    })
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
      {modalContext}
      {messageContext}
    </FixedLayout>
  );
};
export default ActionCenterFields;

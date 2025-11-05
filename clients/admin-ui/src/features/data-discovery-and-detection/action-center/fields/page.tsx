import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntList as List,
  AntMessage as message,
  AntModal as modal,
  AntPagination as Pagination,
  AntSplitter as Splitter,
  AntText as Text,
  AntTitle as Title,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { Key, useCallback, useEffect, useRef, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
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

import {
  ACTION_ALLOWED_STATUSES,
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
  FIELD_PAGE_SIZE,
  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL,
  ResourceStatusLabel,
} from "./MonitorFields.const";
import MonitorTree, { MonitorTreeRef } from "./MonitorTree";
import { ResourceDetailsDrawer } from "./ResourceDetailsDrawer";
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
  const [activeListItem, setActiveListItem] = useState<
    (DatastoreStagedResourceAPIResponse & { itemKey: React.Key }) | null
  >(null);
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
  >({ activeListItem, enableKeyboardShortcuts: true });

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
        selectedListItems.flatMap(({ diff_status }) =>
          diff_status ? [diff_status] : [],
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
          <Flex vertical gap="middle" className="h-full">
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
              className="-ml-3 h-full overflow-y-scroll pl-1" // margin and padding to account for active item left bar styling
              loading={isFetching}
              enableKeyboardShortcuts
              onActiveItemChange={useCallback(
                // useCallback prevents infinite re-renders
                (item: DatastoreStagedResourceAPIResponse | null) => {
                  if (item?.urn) {
                    setActiveListItem({
                      ...item,
                      itemKey: item.urn,
                    });
                  } else {
                    setActiveListItem(null);
                  }
                },
                [],
              )}
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
                    ? !ACTION_ALLOWED_STATUSES["assign-categories"].some(
                        (status) => status === props.diff_status,
                      )
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
                                ? !ACTION_ALLOWED_STATUSES[action].some(
                                    (status) => status === props.diff_status,
                                  )
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
      <ResourceDetailsDrawer
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
            ? !ACTION_ALLOWED_STATUSES[action].some(
                (status) => status === resource.diff_status,
              )
            : true,
        }))}
        open={!!detailsUrn}
        onClose={() => setDetailsUrn(undefined)}
        resource={resource}
        fieldActions={fieldActions}
      />
      {modalContext}
      {messageContext}
    </FixedLayout>
  );
};
export default ActionCenterFields;

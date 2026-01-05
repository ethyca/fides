import {
  Button,
  Checkbox,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Splitter,
  Text,
  Title,
  Tooltip,
} from "fidesui";
import _ from "lodash";
import { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { Key, useEffect, useRef, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import FixedLayout from "~/features/common/FixedLayout";
import { useSearch } from "~/features/common/hooks";
import {
  ACTION_CENTER_ROUTE,
  DATASET_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useGetMonitorConfigQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DiffStatus, TreeResourceChangeIndicator } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import {
  ACTION_ALLOWED_STATUSES,
  ACTIONS_DISABLED_MESSAGE,
  DEFAULT_DRAWER_ACTIONS,
  DRAWER_ACTIONS,
  DROPDOWN_ACTIONS,
  FIELD_ACTION_ICON,
  FIELD_ACTION_LABEL,
  LIST_ITEM_ACTIONS,
  RESOURCE_ACTIONS,
} from "./FieldActions.const";
import { HotkeysHelperModal } from "./HotkeysHelperModal";
import { useLazyGetAllowedActionsQuery } from "./monitor-fields.slice";
import { MonitorFieldFilters } from "./MonitorFieldFilters";
import renderMonitorFieldListItem from "./MonitorFieldListItem";
import {
  EXCLUDED_FILTER_STATUSES,
  FIELD_PAGE_SIZE,
  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL,
  ResourceStatusLabel,
} from "./MonitorFields.const";
import MonitorTree, { MonitorTreeRef } from "./MonitorTree";
import { ResourceDetailsDrawer } from "./ResourceDetailsDrawer";
import { collectNodeUrns } from "./treeUtils";
import type { MonitorResource } from "./types";
import { useBulkActions } from "./useBulkActions";
import { useBulkListSelect } from "./useBulkListSelect";
import { useFieldActionHotkeys } from "./useFieldActionHotkeys";
import { getAvailableActions, useFieldActions } from "./useFieldActions";
import { useMonitorFieldsFilters } from "./useFilters";
import useNormalizedResources from "./useNormalizedResources";

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
  const [hotkeysHelperModalOpen, setHotkeysHelperModalOpen] = useState(false);
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: FIELD_PAGE_SIZE,
    });
  const search = useSearch();
  const {
    resourceStatus,
    confidenceBucket,
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
      confidence_bucket: confidenceBucket || undefined,
      data_category: dataCategory || undefined,
    },
  };

  const [detailsUrn, setDetailsUrn] = useState<string>();
  const [activeListItem, setActiveListItem] = useState<
    MonitorResource & { key: React.Key }
  >();
  const [setActiveListItemIndex, setSetActiveListItemIndex] = useState<
    ((index: number | null) => void) | null
  >(null);

  const [
    allowedActionsTrigger,
    { data: allowedActionsResult, isFetching: isFetchingAllowedActions },
  ] = useLazyGetAllowedActionsQuery();

  const bulkActions = useBulkActions(monitorId, async (urns: string[]) => {
    await monitorTreeRef.current?.refreshResourcesAndAncestors(urns);
  });
  const fieldActions = useFieldActions(monitorId, async (urns: string[]) => {
    await monitorTreeRef.current?.refreshResourcesAndAncestors(urns);
  });
  const {
    listQuery: { nodes: listNodes, ...listQueryMeta },
    detailsQuery: { data: resource },
    nodes: resourceNodes,
  } = useNormalizedResources(
    {
      ...baseMonitorFilters,
      query: {
        ...baseMonitorFilters.query,
        size: pageSize,
        page: pageIndex,
      },
    },
    { stagedResourceUrn: detailsUrn },
  );

  const {
    excludedKeys,
    listSelectMode,
    resetListSelect,
    selectedKeys,
    updateSelectedListItem,
    checkboxProps,
  } = useBulkListSelect(Array.from(listNodes.keys()), {
    activeListItem: activeListItem
      ? {
          ...activeListItem,
          key: activeListItem?.key.toString(),
        }
      : undefined,
    enableKeyboardShortcuts: true,
  });

  const handleNavigate = async (urn: string | undefined) => {
    if (activeListItem?.urn && urn && setActiveListItemIndex) {
      // When navigating via mouse click after using the keyboard,
      // update the active item to match the clicked item
      const itemIndex = [...listNodes.values()].findIndex(
        (item) => item.urn === urn,
      );
      if (itemIndex !== -1) {
        setActiveListItemIndex(itemIndex);
      }
    }
    setDetailsUrn(urn);
  };

  const onActionDropdownOpenChange = (open: boolean) => {
    if (open && listSelectMode === "exclusive") {
      allowedActionsTrigger({
        ...baseMonitorFilters,
        query: {
          ...baseMonitorFilters.query,
        },
        body: {
          excluded_resource_urns: excludedKeys.map((key) => key.toString()),
        },
      });
    }
  };

  useHotkeys(
    "?",
    () => setHotkeysHelperModalOpen(!hotkeysHelperModalOpen),
    { useKey: true },
    [hotkeysHelperModalOpen],
  );

  const availableActions =
    listSelectMode === "exclusive"
      ? allowedActionsResult?.allowed_actions
      : getAvailableActions(
          selectedKeys.flatMap((key) => {
            const node = resourceNodes.get(key);
            return node?.diff_status ? [node.diff_status] : [];
          }),
        );
  const responseCount = listQueryMeta.data?.total ?? 0;
  const selectedListItemCount =
    listSelectMode === "exclusive" && listQueryMeta.data?.total
      ? responseCount - excludedKeys.length
      : selectedKeys.length;

  /**
   * @todo: this should be handled on a form/state action level
   */
  useEffect(() => {
    resetPagination();
    resetListSelect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    resourceStatus,
    confidenceBucket,
    selectedNodeKeys,
    search.searchQuery,
    dataCategory,
  ]);

  // Set up keyboard shortcuts for field actions
  useFieldActionHotkeys(
    activeListItem,
    fieldActions,
    updateSelectedListItem,
    handleNavigate,
    !!detailsUrn,
    () => listQueryMeta.refetch(),
  );

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
            setSelectedNodeKeys={setSelectedNodeKeys}
            selectedNodeKeys={selectedNodeKeys}
            primaryAction={FieldActionType.CLASSIFY}
            nodeActions={Object.fromEntries(
              RESOURCE_ACTIONS.map((action) => [
                action,
                {
                  label: FIELD_ACTION_LABEL[action],
                  /** Logic for this should exist on the BE */
                  disabled: (nodes) =>
                    _(nodes)
                      .map((node) => {
                        if (
                          (action === FieldActionType.PROMOTE_REMOVALS &&
                            node.status ===
                              TreeResourceChangeIndicator.REMOVAL) ||
                          (action === FieldActionType.CLASSIFY &&
                            node.classifyable &&
                            node.diffStatus !== DiffStatus.MUTED) ||
                          (action === FieldActionType.MUTE &&
                            node.diffStatus !== DiffStatus.MUTED) ||
                          (action === FieldActionType.UN_MUTE &&
                            node.diffStatus === DiffStatus.MUTED)
                        ) {
                          return false;
                        }

                        return true;
                      })
                      .some((d) => d === true),
                  callback: (keys, nodes) => {
                    const allUrns = collectNodeUrns(nodes);
                    fieldActions[action](allUrns, false);
                  },
                },
              ]),
            )}
          />
        </Splitter.Panel>
        {/** Note: style attr used here due to specificity of ant css. */}
        <Splitter.Panel style={{ paddingLeft: "var(--ant-padding-md)" }}>
          <Flex vertical gap="middle" className="h-full">
            <Flex justify="space-between">
              <Title level={2} ellipsis>
                Monitor results
              </Title>
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
            <Flex justify="space-between" wrap="wrap" gap="small">
              <Flex gap="small">
                <DebouncedSearchInput
                  value={search.searchQuery}
                  onChange={search.updateSearch}
                  placeholder="Search"
                />
                <Tooltip title="Display keyboard shortcuts">
                  <Button
                    aria-label="Display keyboard shortcuts"
                    icon={<Icons.Keyboard />}
                    onClick={() => setHotkeysHelperModalOpen(true)}
                  />
                </Tooltip>
              </Flex>
              <Flex gap="small">
                <MonitorFieldFilters
                  resourceStatus={resourceStatus}
                  confidenceBucket={confidenceBucket}
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
                              title={ACTIONS_DISABLED_MESSAGE[actionType]}
                            >
                              {FIELD_ACTION_LABEL[actionType]}
                            </Tooltip>
                          ) : (
                            FIELD_ACTION_LABEL[actionType]
                          ),
                        disabled:
                          isFetchingAllowedActions ||
                          !availableActions?.includes(actionType),
                        onClick: async () => {
                          if (listSelectMode === "exclusive") {
                            await bulkActions[actionType](
                              baseMonitorFilters,
                              excludedKeys.map((key) => key.toString()),
                              selectedListItemCount,
                            );
                          } else {
                            await fieldActions[actionType](
                              selectedKeys.map((key) => key.toString()),
                            );
                          }

                          resetListSelect();
                        },
                      })),
                    ],
                  }}
                  disabled={selectedKeys.length <= 0}
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
                    onClick={() => listQueryMeta.refetch()}
                    aria-label="Refresh"
                  />
                </Tooltip>
              </Flex>
            </Flex>
            <Flex gap="middle" align="center">
              <Checkbox id="select-all" {...checkboxProps} />
              <label htmlFor="select-all">Select all</label>
              {!!selectedListItemCount && (
                <Text strong>
                  {selectedListItemCount.toLocaleString()} selected
                </Text>
              )}
            </Flex>
            <List
              dataSource={[...listNodes.values()]}
              className="-ml-3 h-full overflow-y-scroll pl-1" // margin and padding to account for active item left bar styling
              loading={listQueryMeta.isFetching}
              enableKeyboardShortcuts
              locale={
                !search.searchProps.value &&
                _(resourceStatus)
                  .intersection(EXCLUDED_FILTER_STATUSES)
                  .isEmpty()
                  ? {
                      emptyText: (
                        <Empty
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                          description={
                            <>
                              <div>All resources have been approved.</div>
                              <div>
                                {`You'll now find this data in Managed Datasets
                                view.`}
                              </div>
                              <div>
                                {`To see approved or ignored resources, adjust
                                your filters`}
                              </div>
                            </>
                          }
                        >
                          <Flex gap="middle" justify="center">
                            <NextLink
                              href={DATASET_ROUTE}
                              passHref
                              legacyBehavior
                            >
                              <Button>Manage datasets view</Button>
                            </NextLink>
                            <Button
                              type="primary"
                              aria-label="Refresh page"
                              onClick={() => {
                                restMonitorFieldsFilters.resetToInitialState();
                                router.reload();
                              }}
                            >
                              Refresh page
                            </Button>
                          </Flex>
                        </Empty>
                      ),
                    }
                  : undefined
              }
              onActiveItemChange={(
                item,
                _activeListItemIndex,
                setActiveIndexFn,
              ) => {
                // Store the setter function so handleNavigate can use it
                setSetActiveListItemIndex(() => setActiveIndexFn);

                if (item?.urn) {
                  setActiveListItem({
                    ...item,
                    key: item.urn,
                  });
                  if (detailsUrn && item.urn !== detailsUrn) {
                    setDetailsUrn(item.urn);
                  }
                } else {
                  setActiveListItem(undefined);
                }
              }}
              renderItem={(props) =>
                renderMonitorFieldListItem({
                  ...props,
                  selected: selectedKeys.includes(props.urn),
                  onSelect: updateSelectedListItem,
                  onNavigate: handleNavigate,
                  onSetDataCategories: (urn, values) =>
                    fieldActions["assign-categories"]([urn], true, {
                      user_assigned_data_categories: values,
                    }),
                  dataCategoriesDisabled: props?.diff_status
                    ? !ACTION_ALLOWED_STATUSES["assign-categories"].some(
                        (status) => status === props.diff_status,
                      )
                    : true,
                  actions: props?.diff_status
                    ? LIST_ITEM_ACTIONS[props.diff_status].map((action) => (
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
              total={listQueryMeta.data?.total || 0}
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
        actions={(resource?.diff_status
          ? DRAWER_ACTIONS[resource.diff_status]
          : DEFAULT_DRAWER_ACTIONS
        ).map((action) => ({
          label: FIELD_ACTION_LABEL[action],
          callback: (key) => fieldActions[action]([key]),
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
        mask={!activeListItem}
      />
      <HotkeysHelperModal
        open={hotkeysHelperModalOpen}
        onCancel={() => setHotkeysHelperModalOpen(false)}
      />
    </FixedLayout>
  );
};
export default ActionCenterFields;

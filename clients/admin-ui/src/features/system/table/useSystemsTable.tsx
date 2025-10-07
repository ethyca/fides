import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntFlex as Flex,
  AntMessage as message,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { ListExpandableCell } from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { convertToAntFilters } from "~/features/common/utils";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  useDeleteSystemMutation,
  useGetSystemsQuery,
} from "~/features/system/system.slice";
import {
  useCreateSystemGroupMutation,
  useGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
} from "~/features/system/system-groups.slice";
import { SystemColumnKeys } from "~/features/system/table/SystemColumnKeys";
import SystemDataUseCell from "~/features/system/table/SystemDataUseCell";
import SystemGroupCell from "~/features/system/table/SystemGroupCell";
import { useGetAllUsersQuery } from "~/features/user-management";
import {
  BasicSystemResponseExtended,
  PrivacyDeclaration,
  ScopeRegistryEnum,
  SystemGroup,
  SystemGroupCreate,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const useSystemsTable = () => {
  // ancillary data
  const { data: allSystemGroups } = useGetAllSystemGroupsQuery();

  const systemGroupMap = useMemo(() => {
    return allSystemGroups
      ? allSystemGroups.reduce(
          (acc, group) => ({
            ...acc,
            [group.fides_key]: group,
          }),
          {} as Record<string, SystemGroup>,
        )
      : {};
  }, [allSystemGroups]);

  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  // mutations
  const [deleteSystem] = useDeleteSystemMutation();
  const [updateSystemGroup] = useUpdateSystemGroupMutation();
  const [createSystemGroup] = useCreateSystemGroupMutation();

  // UI state
  const [isGroupsExpanded, setIsGroupsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);

  const [createModalIsOpen, setCreateModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);
  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    useState<BasicSystemResponseExtended | null>(null);

  // main table state
  const tableState = useTableState<SystemColumnKeys>({
    pagination: { defaultPageSize: 25, pageSizeOptions: [25, 50, 100] },
    search: { defaultSearchQuery: "" },
    sorting: {
      defaultSortKey: SystemColumnKeys.NAME,
      defaultSortOrder: "ascend",
      validColumns: [SystemColumnKeys.NAME],
    },
  });

  const {
    columnFilters,
    pageIndex,
    pageSize,
    searchQuery,
    updateSearch,
    sortKey,
    sortOrder,
  } = tableState;

  const {
    data: systemsResponse,
    isLoading,
    isFetching,
  } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    sort_by: sortKey,
    sort_asc: sortOrder === "ascend",
    show_deleted: true,
    ...columnFilters,
  });

  const antTableConfig = useMemo(
    () => ({
      enableSelection: true,
      dataSource: systemsResponse?.items ?? [],
      totalRows: systemsResponse?.total ?? 0,
      isLoading,
      isFetching,
      getRowKey: (record: BasicSystemResponseExtended) => record.fides_key,
      customTableProps: {
        locale: {
          emptyText: <div>No systems found</div>,
        },
      },
    }),
    [systemsResponse, isLoading, isFetching],
  );

  const { tableProps, selectionProps } = useAntTable(
    tableState,
    antTableConfig,
  );

  const { selectedRowKeys } = selectionProps ?? {};

  // utils
  const [messageApi, messageContext] = message.useMessage();
  const { plus: plusIsEnabled } = useFeatures();
  const router = useRouter();

  const showDeleteOption: boolean = useHasPermission([
    ScopeRegistryEnum.SYSTEM_DELETE,
  ]);

  const handleDelete = async (system: BasicSystemResponseExtended) => {
    const result = await deleteSystem(system.fides_key);
    if (isErrorResult(result)) {
      messageApi.error(
        getErrorMessage(result.error, "Failed to delete system"),
      );
    } else {
      messageApi.success("Successfully deleted system");
    }
    setDeleteModalIsOpen(false);
  };

  const handleCreateSystemGroup = async (systemGroup: SystemGroupCreate) => {
    const payload = {
      ...systemGroup,
      fides_key: formatKey(systemGroup.name),
      active: true,
    };
    const result = await createSystemGroup(payload);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      let successMessage = `System group '${result.data.name}' created`;
      if (result.data.systems?.length === 1) {
        successMessage += ` with system '${result.data.systems[0]}'`;
      } else if (result.data.systems?.length) {
        successMessage += ` with ${result.data.systems.length} systems`;
      }
      messageApi.success(successMessage);
    }
    setCreateModalIsOpen(false);
  };

  const handleBulkAddToGroup = useCallback(
    async (groupKey: string) => {
      if (!selectedRowKeys) {
        return;
      }
      const currentGroup = systemGroupMap[groupKey];
      const result = await updateSystemGroup({
        ...currentGroup,
        systems: uniq([
          ...(currentGroup.systems ?? []),
          ...selectedRowKeys.map((key) => key.toString()),
        ]),
      });
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
      } else {
        messageApi.success(
          `${selectedRowKeys?.length} systems added to group '${groupKey}'`,
        );
      }
    },
    [systemGroupMap, updateSystemGroup, selectedRowKeys, messageApi],
  );

  const groupMenuItems = useMemo(() => {
    return (
      allSystemGroups?.map((group) => ({
        key: group.fides_key,
        label: group.name,
        onClick: () => handleBulkAddToGroup(group.fides_key),
      })) ?? []
    );
  }, [allSystemGroups, handleBulkAddToGroup]);

  const columns: ColumnsType<BasicSystemResponseExtended> = useMemo(() => {
    return [
      {
        title: "Name",
        dataIndex: "name",
        key: SystemColumnKeys.NAME,
        render: (name: string | null, record: BasicSystemResponseExtended) => (
          <LinkCell
            href={`/systems/configure/${record.fides_key}`}
            data-testid={`system-link-${record.fides_key}`}
          >
            {name || record.fides_key}
          </LinkCell>
        ),
        ellipsis: true,
        fixed: "left",
        sorter: true,
        sortOrder: sortKey === SystemColumnKeys.NAME ? sortOrder : null,
      },
      {
        dataIndex: "system_groups",
        key: SystemColumnKeys.SYSTEM_GROUPS,
        render: (
          systemGroups: string[] | undefined,
          record: BasicSystemResponseExtended,
        ) => (
          <SystemGroupCell
            selectedGroups={
              systemGroups
                ?.map((key) => systemGroupMap?.[key])
                .filter((group) => !!group) ?? []
            }
            allGroups={allSystemGroups!}
            system={{ ...record, system_groups: systemGroups ?? [] }}
            columnState={{
              isWrapped: true,
              isExpanded: isGroupsExpanded,
            }}
            className="w-96"
          />
        ),
        title: "Groups",
        hidden: !plusIsEnabled,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsGroupsExpanded(true);
            } else if (e.key === "collapse-all") {
              setIsGroupsExpanded(false);
            }
          },
        },
        filters: convertToAntFilters(
          allSystemGroups?.map((group) => group.fides_key),
          (group) => systemGroupMap[group]?.name ?? group,
        ),
        filteredValue: columnFilters?.system_groups || null,
      },
      {
        title: "Data uses",
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsDataUsesExpanded(true);
            } else if (e.key === "collapse-all") {
              setIsDataUsesExpanded(false);
            }
          },
        },
        dataIndex: "privacy_declarations",
        key: SystemColumnKeys.DATA_USES,
        render: (privacyDeclarations: PrivacyDeclaration[]) => (
          <SystemDataUseCell
            privacyDeclarations={privacyDeclarations}
            columnState={{
              isWrapped: true,
              isExpanded: isDataUsesExpanded,
            }}
          />
        ),
      },
      {
        title: "Data stewards",
        dataIndex: "data_stewards",
        key: SystemColumnKeys.DATA_STEWARDS,
        render: (dataStewards: string[] | null) => (
          <ListExpandableCell values={dataStewards ?? []} valueSuffix="users" />
        ),
        filters: convertToAntFilters(
          allUsers?.items?.map((user) => user.username),
        ),
        filteredValue: columnFilters?.data_stewards || null,
      },
      {
        title: "Description",
        dataIndex: "description",
        key: SystemColumnKeys.DESCRIPTION,
        render: (description: string | null) => (
          <div className="max-w-96">
            <Typography.Text ellipsis={{ tooltip: description }}>
              {description}
            </Typography.Text>
          </div>
        ),
        ellipsis: true,
      },
      {
        title: "Actions",
        key: SystemColumnKeys.ACTIONS,
        render: (_: undefined, record: BasicSystemResponseExtended) => (
          <Flex gap="small">
            <Button
              size="small"
              onClick={() =>
                router.push(`/systems/configure/${record.fides_key}`)
              }
              icon={<Icons.Edit />}
              data-testid="edit-btn"
            >
              Edit
            </Button>
            {showDeleteOption && (
              <Button
                size="small"
                onClick={() => {
                  setSelectedSystemForDelete(record);
                  setDeleteModalIsOpen(true);
                }}
                icon={<Icons.TrashCan />}
                data-testid="delete-btn"
              >
                Delete
              </Button>
            )}
          </Flex>
        ),
        fixed: "right",
      },
    ];
  }, [
    sortKey,
    sortOrder,
    plusIsEnabled,
    allSystemGroups,
    columnFilters?.system_groups,
    columnFilters?.data_stewards,
    allUsers?.items,
    isGroupsExpanded,
    systemGroupMap,
    isDataUsesExpanded,
    showDeleteOption,
    router,
  ]);

  return {
    // table
    tableProps,
    selectionProps,
    columns,
    // search
    searchQuery,
    updateSearch,
    // filters
    columnFilters,
    // pagination
    pageIndex,
    pageSize,
    // modals
    createModalIsOpen,
    setCreateModalIsOpen,
    deleteModalIsOpen,
    setDeleteModalIsOpen,
    setSelectedSystemForDelete,
    // actions
    handleCreateSystemGroup,
    handleDelete,
    handleBulkAddToGroup,
    // utils
    messageContext,
    groupMenuItems,
    selectedSystemForDelete,
  };
};

export default useSystemsTable;

/* eslint-disable react/no-unstable-nested-components */
import {
  AntButton,
  AntButton as Button,
  AntColumnsType,
  AntDropdown,
  AntFlex,
  AntMessage as message,
  AntModal,
  AntTable as Table,
  Icons,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures, useFlags } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import {
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { convertToAntFilters } from "~/features/common/utils";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useDeleteSystemMutation, useGetSystemsQuery } from "~/features/system";
import CreateSystemGroupForm from "~/features/system/system-groups/components/CreateSystemGroupForm";
import SystemDataUseCell from "~/features/system/system-groups/components/SystemDataUseCell";
import SystemGroupCell from "~/features/system/system-groups/components/SystemGroupCell";
import {
  useCreateSystemGroupMutation,
  useGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
} from "~/features/system/system-groups/system-groups.slice";
import SystemActionsMenu from "~/features/system/SystemActionsMenu";
import { useGetAllUsersQuery } from "~/features/user-management";
import {
  BasicSystemResponseExtended,
  PrivacyDeclaration,
  SystemGroup,
  SystemGroupCreate,
  UserResponse,
} from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const SystemsTable = () => {
  const { data: allSystemGroups } = useGetAllSystemGroupsQuery();
  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });
  const [createSystemGroup] = useCreateSystemGroupMutation();
  const [deleteSystem] = useDeleteSystemMutation();
  const [updateSystemGroup] = useUpdateSystemGroupMutation();

  const [messageApi, messageContext] = message.useMessage();

  const {
    flags: { alphaSystemGroups: isAlphaSystemGroupsEnabled },
  } = useFlags();

  const { plus: plusIsEnabled } = useFeatures();

  const router = useRouter();

  const [createModalIsOpen, setCreateModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const [isGroupsExpanded, setIsGroupsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);

  const [dataStewardFilter, setDataStewardFilter] = useState<string>();
  const [systemGroupFilter, setSystemGroupFilter] = useState<string>();

  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    useState<BasicSystemResponseExtended | null>(null);

  const [globalFilter, setGlobalFilter] = useState<string>();

  const { pageSize, pageIndex } = useServerSidePagination();

  const { data: systemsResponse, isLoading } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
    data_steward: dataStewardFilter,
    system_group: systemGroupFilter,
  });

  const { items: data } = useMemo(
    () => systemsResponse ?? EMPTY_RESPONSE,
    [systemsResponse],
  );

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

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  const handleBulkAddToGroup = useCallback(
    async (groupKey: string) => {
      const currentGroup = systemGroupMap[groupKey];
      const result = await updateSystemGroup({
        ...currentGroup,
        systems: [
          ...(currentGroup.systems ?? []),
          ...selectedRowKeys.map((key) => key.toString()),
        ],
      });
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
      } else {
        messageApi.success(
          `${selectedRowKeys.length} systems added to group '${groupKey}'`,
        );
      }
    },
    [updateSystemGroup, messageApi, selectedRowKeys, systemGroupMap],
  );

  const handleCreateSystemGroup = async (systemGroup: SystemGroupCreate) => {
    const payload = {
      ...systemGroup,
      // TODO: add input for handling fides_key
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

  const handleFilterChange = (filters: Record<string, any>) => {
    if (filters.data_steward) {
      setDataStewardFilter(filters.data_steward[0]);
    }
    if (filters.system_groups) {
      setSystemGroupFilter(filters.system_groups[0]);
    }
  };

  const columns: AntColumnsType<BasicSystemResponseExtended> = useMemo(() => {
    return [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (name: string | null, record: BasicSystemResponseExtended) => (
          <LinkCell href={`/systems/configure/${record.fides_key}`}>
            {name || record.fides_key}
          </LinkCell>
        ),
        width: 300,
        ellipsis: true,
        fixed: "left",
      },
      {
        dataIndex: "system_groups",
        key: "system_groups",
        render: (
          systemGroups: string[] | undefined,
          record: BasicSystemResponseExtended,
        ) => (
          <SystemGroupCell
            // @ts-ignore - TS doesn't know we filter out undefined
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
          />
        ),
        width: 400,
        title: "Groups",
        hidden: !plusIsEnabled || !isAlphaSystemGroupsEnabled,
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
          (groupKey) => systemGroupMap[groupKey]?.name ?? groupKey,
        ),
        filterMultiple: false,
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
        key: "privacy_declarations",
        render: (privacyDeclarations: PrivacyDeclaration[]) => (
          <SystemDataUseCell
            privacyDeclarations={privacyDeclarations}
            columnState={{
              isWrapped: true,
              isExpanded: isDataUsesExpanded,
            }}
          />
        ),
        width: 500,
      },
      {
        title: "Data steward",
        dataIndex: "data_steward",
        key: "data_steward",
        render: (dataSteward: string | null) => dataSteward,
        width: 200,
        filters: convertToAntFilters(
          allUsers?.items?.map((user: UserResponse) => user.username) ?? [],
          (username) => username,
        ),
        filterMultiple: false,
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        render: (description: string | null) => description,
        width: 200,
        ellipsis: true,
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: undefined, record: BasicSystemResponseExtended) => (
          <AntFlex justify="end">
            <AntDropdown
              trigger={["click"]}
              menu={{
                items: [
                  {
                    key: "edit",
                    label: "Edit",
                    icon: <Icons.Edit />,
                    onClick: () =>
                      router.push(`/systems/configure/${record.fides_key}`),
                  },
                  {
                    key: "delete",
                    label: "Delete",
                    icon: <Icons.TrashCan />,
                    onClick: () => {
                      setSelectedSystemForDelete(record);
                      setDeleteModalIsOpen(true);
                    },
                  },
                ],
              }}
            >
              <Button
                size="small"
                icon={<Icons.OverflowMenuVertical />}
                aria-label="More actions"
                type="text"
              />
            </AntDropdown>
          </AntFlex>
        ),
        width: 10,
        fixed: "right",
      },
    ];
  }, [
    plusIsEnabled,
    isAlphaSystemGroupsEnabled,
    allSystemGroups,
    allUsers?.items,
    isGroupsExpanded,
    systemGroupMap,
    isDataUsesExpanded,
    router,
  ]);

  const groupMenuItems = useMemo(() => {
    return (
      allSystemGroups?.map((group) => ({
        key: group.fides_key,
        label: group.name,
        onClick: () => handleBulkAddToGroup(group.fides_key),
      })) ?? []
    );
  }, [allSystemGroups, handleBulkAddToGroup]);

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <>
      {messageContext}
      <AntFlex justify="space-between" className="mb-4">
        <DebouncedSearchInput value={globalFilter} onChange={setGlobalFilter} />
        <AntFlex gap="small">
          {isAlphaSystemGroupsEnabled && (
            <>
              <AntDropdown
                trigger={["click"]}
                menu={{
                  items: [
                    {
                      key: "new-group",
                      label: "Create new group +",
                      onClick: () => setCreateModalIsOpen(true),
                    },
                    {
                      type: "divider",
                    },
                    ...groupMenuItems,
                  ],
                }}
              >
                <AntButton
                  disabled={selectedRowKeys.length === 0}
                  icon={<Icons.ChevronDown />}
                >
                  Add to group
                </AntButton>
              </AntDropdown>
              <AntModal
                open={createModalIsOpen}
                destroyOnHidden
                onCancel={() => setCreateModalIsOpen(false)}
                centered
                width={768}
                footer={null}
              >
                <CreateSystemGroupForm
                  selectedSystemKeys={selectedRowKeys.map((key) =>
                    key.toString(),
                  )}
                  onSubmit={handleCreateSystemGroup}
                  onCancel={() => setCreateModalIsOpen(false)}
                />
              </AntModal>
            </>
          )}
          <SystemActionsMenu selectedRowKeys={selectedRowKeys} />
          <AntModal
            open={deleteModalIsOpen}
            onCancel={() => setDeleteModalIsOpen(false)}
            onOk={() => handleDelete(selectedSystemForDelete!)}
            okText="Delete"
            okType="danger"
            cancelText="Cancel"
            centered
          >
            <CustomTypography.Paragraph>
              Are you sure you want to delete{" "}
              {selectedSystemForDelete?.name ??
                selectedSystemForDelete?.fides_key}
              ? This action cannot be undone.
            </CustomTypography.Paragraph>
          </AntModal>
        </AntFlex>
      </AntFlex>
      <Table
        dataSource={data}
        columns={columns}
        loading={isLoading}
        rowKey="fides_key"
        size="small"
        rowSelection={rowSelection}
        tableLayout="fixed"
        pagination={{
          pageSize,
          total: systemsResponse?.total ?? 0,
        }}
        onChange={(_, filters) => {
          handleFilterChange(filters);
        }}
      />
    </>
  );
};

export default SystemsTable;

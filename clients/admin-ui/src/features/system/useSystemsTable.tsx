import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntDropdown as Dropdown,
  AntFilterValue as FilterValue,
  AntMessage as message,
  Flex,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { convertToAntFilters } from "~/features/common/utils";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useDeleteSystemMutation } from "~/features/system/system.slice";
import SystemDataUseCell from "~/features/system/system-groups/components/SystemDataUseCell";
import SystemGroupCell from "~/features/system/system-groups/components/SystemGroupCell";
import {
  useCreateSystemGroupMutation,
  useGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
} from "~/features/system/system-groups/system-groups.slice";
import { useGetAllUsersQuery } from "~/features/user-management";
import {
  BasicSystemResponseExtended,
  PrivacyDeclaration,
  SystemGroup,
  SystemGroupCreate,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface UseSystemsTableParams {
  isAlphaSystemGroupsEnabled?: boolean;
  selectedRowKeys: React.Key[];
  columnFilters: Record<string, FilterValue | null>;
}

const useSystemsTable = ({
  selectedRowKeys,
  isAlphaSystemGroupsEnabled,
  columnFilters,
}: UseSystemsTableParams) => {
  // data
  const { data: allSystemGroups } = useGetAllSystemGroupsQuery();
  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  // mutations
  const [deleteSystem] = useDeleteSystemMutation();
  const [updateSystemGroup] = useUpdateSystemGroupMutation();
  const [createSystemGroup] = useCreateSystemGroupMutation();

  // state
  const [isGroupsExpanded, setIsGroupsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);

  const [createModalIsOpen, setCreateModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);
  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    useState<BasicSystemResponseExtended | null>(null);

  // utils
  const [messageApi, messageContext] = message.useMessage();
  const { plus: plusIsEnabled } = useFeatures();
  const router = useRouter();

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
        key: "name",
        render: (name: string | null, record: BasicSystemResponseExtended) => (
          <LinkCell
            href={`/systems/configure/${record.fides_key}`}
            data-testid={`system-link-${record.fides_key}`}
          >
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
          allUsers?.items?.map((user) => user.username),
        ),
        filteredValue: columnFilters?.data_steward || null,
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
          <Flex justify="end">
            <Dropdown
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
            </Dropdown>
          </Flex>
        ),
        width: 10,
        fixed: "right",
      },
    ];
  }, [
    allUsers,
    plusIsEnabled,
    isAlphaSystemGroupsEnabled,
    allSystemGroups,
    isGroupsExpanded,
    systemGroupMap,
    isDataUsesExpanded,
    router,
    setSelectedSystemForDelete,
    setDeleteModalIsOpen,
    columnFilters,
  ]);

  return {
    columns,
    createModalIsOpen,
    setCreateModalIsOpen,
    deleteModalIsOpen,
    setDeleteModalIsOpen,
    selectedSystemForDelete,
    setSelectedSystemForDelete,
    groupMenuItems,
    handleCreateSystemGroup,
    handleDelete,
    handleBulkAddToGroup,
    messageContext,
  };
};

export default useSystemsTable;

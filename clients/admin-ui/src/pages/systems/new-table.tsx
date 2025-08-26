/* eslint-disable react/no-unstable-nested-components */
import {
  AntButton,
  AntButton as Button,
  AntDropdown,
  AntFlex,
  AntMessage as message,
  AntModal,
  AntTable as Table,
  Icons,
  AntMenuProps,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import {
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useDeleteSystemMutation, useGetSystemsQuery } from "~/features/system";
import CreateSystemGroupForm from "~/features/system/system-groups/components/CreateSystemGroupForm";
import SystemDataUseCell from "~/features/system/system-groups/components/SystemDataUseCell";
import SystemGroupCell from "~/features/system/system-groups/components/SystemGroupCell";
import {
  useCreateSystemGroupMutation,
  useGetAllSystemGroupsQuery,
} from "~/features/system/system-groups/system-groups.slice";
import SystemActionsMenu from "~/features/system/SystemActionsMenu";
import { useMockBulkUpdateSystemWithGroupsMutation } from "~/mocks/TEMP-system-groups/endpoints/systems";
import {
  BasicSystemResponseExtended,
  PrivacyDeclaration,
  SystemGroup,
  SystemGroupCreate,
} from "~/types/api";

interface NewTableProps {
  loading?: boolean;
}

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const NewTable = ({ loading = false }: NewTableProps) => {
  const { data: allSystemGroups } = useGetAllSystemGroupsQuery();
  const [createSystemGroup] = useCreateSystemGroupMutation();
  const [deleteSystem] = useDeleteSystemMutation();
  const [bulkUpdate] = useMockBulkUpdateSystemWithGroupsMutation();

  const [messageApi, messageContext] = message.useMessage();

  const router = useRouter();

  const [createModalIsOpen, setCreateModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const [isGroupsExpanded, setIsGroupsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);

  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    useState<BasicSystemResponseExtended | null>(null);

  const [globalFilter, setGlobalFilter] = useState<string>();

  const { pageSize, pageIndex } = useServerSidePagination();

  const { data: systemsResponse, isLoading } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
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
      const result = await bulkUpdate({
        system_keys: selectedRowKeys.map((key) => key.toString()),
        group_key: groupKey,
      });
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
      } else {
        messageApi.success(
          `${selectedRowKeys.length} systems added to group '${groupKey}'`,
        );
      }
    },
    [bulkUpdate, messageApi, selectedRowKeys],
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

  const columns = useMemo(() => {
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
      },
    ];
  }, [
    isGroupsExpanded,
    isDataUsesExpanded,
    systemGroupMap,
    allSystemGroups,
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
          <SystemActionsMenu selectedRowKeys={selectedRowKeys} />
        </AntFlex>
      </AntFlex>
      <AntModal
        open={createModalIsOpen}
        destroyOnHidden
        onCancel={() => setCreateModalIsOpen(false)}
        centered
        width={768}
        footer={null}
      >
        <CreateSystemGroupForm
          selectedSystems={selectedRowKeys.map((key) => key.toString())}
          onSubmit={handleCreateSystemGroup}
          onCancel={() => setCreateModalIsOpen(false)}
        />
      </AntModal>
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
          {selectedSystemForDelete?.name ?? selectedSystemForDelete?.fides_key}?
          This action cannot be undone.
        </CustomTypography.Paragraph>
      </AntModal>
      <Table
        dataSource={data}
        columns={columns}
        loading={loading}
        rowKey="fides_key"
        size="small"
        rowSelection={rowSelection}
        tableLayout="fixed"
        pagination={{
          pageSize: 25,
          total: data.length,
        }}
      />
    </>
  );
};

export default NewTable;

import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFilterValue as FilterValue,
  AntFlex as Flex,
  AntModal as Modal,
  AntTable as Table,
  AntTypography,
  Icons,
} from "fidesui";
import { useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFlags } from "~/features/common/features";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { useGetSystemsQuery } from "~/features/system";
import CreateSystemGroupForm from "~/features/system/system-groups/components/CreateSystemGroupForm";
import SystemActionsMenu from "~/features/system/SystemActionsMenu";
import useSystemsTable from "~/features/system/useSystemsTable";

const SystemsTable = () => {
  const {
    flags: { alphaSystemGroups: isAlphaSystemGroupsEnabled },
  } = useFlags();

  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [25, 50, 100] },
    sorting: { defaultSortKey: "name", defaultSortOrder: "ascend" },
    search: { defaultSearchQuery: "" },
  });

  const dataStewardFilter = useMemo(() => {
    const filters = tableState.columnFilters ?? {};
    const value = filters.data_steward as FilterValue;
    return Array.isArray(value) ? value[0]?.toString() : undefined;
  }, [tableState.columnFilters]);

  const groupFilter = useMemo(() => {
    const filters = tableState.columnFilters ?? {};
    const value = filters.system_groups as FilterValue;
    return Array.isArray(value) ? value[0]?.toString() : undefined;
  }, [tableState.columnFilters]);

  const { data: systemsResponse, isLoading } = useGetSystemsQuery({
    page: tableState.pageIndex,
    size: tableState.pageSize,
    search: tableState.searchQuery,
    data_steward: dataStewardFilter,
    system_group: groupFilter,
  });

  const { tableProps, selectionProps } = useAntTable(tableState, {
    enableSelection: true,
    dataSource: systemsResponse?.items,
    totalRows: systemsResponse?.total ?? 0,
    isLoading,
    getRowKey: (record) => record.fides_key,
  });

  const {
    columns,

    // modals
    createModalIsOpen,
    setCreateModalIsOpen,
    deleteModalIsOpen,
    setDeleteModalIsOpen,

    // actions
    handleCreateSystemGroup,
    handleDelete,

    // utils
    groupMenuItems,
    messageContext,
    selectedSystemForDelete,
  } = useSystemsTable({
    selectedRowKeys: selectionProps?.selectedRowKeys ?? [],
    isAlphaSystemGroupsEnabled,
    columnFilters: tableState.columnFilters ?? {},
  });

  return (
    <>
      {messageContext}
      <Flex justify="space-between" className="mb-4">
        <DebouncedSearchInput
          value={tableState.searchQuery}
          onChange={tableState.updateSearch}
        />
        <Flex gap="small">
          {isAlphaSystemGroupsEnabled && (
            <>
              <Dropdown
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
                <Button
                  disabled={selectionProps?.selectedRowKeys.length === 0}
                  icon={<Icons.ChevronDown />}
                >
                  Add to group
                </Button>
              </Dropdown>
              <Modal
                open={createModalIsOpen}
                destroyOnHidden
                onCancel={() => setCreateModalIsOpen(false)}
                centered
                width={768}
                footer={null}
              >
                <CreateSystemGroupForm
                  selectedSystemKeys={selectionProps?.selectedRowKeys.map(
                    (key) => key.toString(),
                  )}
                  onSubmit={handleCreateSystemGroup}
                  onCancel={() => setCreateModalIsOpen(false)}
                />
              </Modal>
            </>
          )}
          <SystemActionsMenu
            selectedRowKeys={selectionProps?.selectedRowKeys ?? []}
          />
          <Modal
            open={deleteModalIsOpen}
            onCancel={() => setDeleteModalIsOpen(false)}
            onOk={() => handleDelete(selectedSystemForDelete!)}
            okText="Delete"
            okType="danger"
            cancelText="Cancel"
            centered
          >
            <AntTypography.Paragraph>
              Are you sure you want to delete{" "}
              {selectedSystemForDelete?.name ??
                selectedSystemForDelete?.fides_key}
              ? This action cannot be undone.
            </AntTypography.Paragraph>
          </Modal>
        </Flex>
      </Flex>
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};

export default SystemsTable;

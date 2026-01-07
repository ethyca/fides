import { Flex, Modal, Table, Typography } from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import SystemActionsMenu from "~/features/system/SystemActionsMenu";
import useSystemsTable from "~/features/system/table/useSystemsTable";

const SystemsTable = () => {
  const {
    // table
    tableProps,
    selectionProps,
    columns,

    // search
    searchQuery,
    updateSearch,

    // modals
    createModalIsOpen,
    setCreateModalIsOpen,
    deleteModalIsOpen,
    setDeleteModalIsOpen,

    // actions
    handleDelete,
    handleCreateSystemGroup,
    handleBulkAddToGroup,

    // utils
    groupMenuItems,
    selectedSystemForDelete,
  } = useSystemsTable();

  return (
    <>
      <Flex
        gap="small"
        justify="space-between"
        className="sticky -top-6 z-10 bg-white py-4"
      >
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          data-testid="system-search"
        />
        <SystemActionsMenu
          selectedRowKeys={selectionProps?.selectedRowKeys ?? []}
          createModalIsOpen={createModalIsOpen}
          setCreateModalIsOpen={setCreateModalIsOpen}
          handleCreateSystemGroup={handleCreateSystemGroup}
          handleBulkAddToGroup={handleBulkAddToGroup}
          groupMenuItems={groupMenuItems}
        />
        <Modal
          open={deleteModalIsOpen}
          onCancel={() => setDeleteModalIsOpen(false)}
          onOk={() =>
            !!selectedSystemForDelete && handleDelete(selectedSystemForDelete)
          }
          okText="Delete"
          okType="danger"
          cancelText="Cancel"
          centered
        >
          <Typography.Paragraph>
            Are you sure you want to delete{" "}
            {selectedSystemForDelete?.name ??
              selectedSystemForDelete?.fides_key}
            ? This action cannot be undone.
          </Typography.Paragraph>
        </Modal>
      </Flex>
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};

export default SystemsTable;

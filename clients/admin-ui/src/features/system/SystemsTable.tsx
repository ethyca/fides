import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntModal as Modal,
  AntTable as Table,
  AntTypography as Typography,
  Icons,
} from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features";
import CreateSystemGroupForm from "~/features/system/system-groups/components/CreateSystemGroupForm";
import SystemActionsMenu from "~/features/system/SystemActionsMenu";
import useSystemsTable from "~/features/system/useSystemsTable";

const SystemsTable = () => {
  const { plus: isPlusEnabled } = useFeatures();

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
    handleCreateSystemGroup,
    handleDelete,

    // utils
    groupMenuItems,
    messageContext,
    selectedSystemForDelete,
  } = useSystemsTable();

  return (
    <>
      {messageContext}
      <Flex justify="space-between" className="mb-4">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          data-testid="system-search"
        />
        <Flex gap="small">
          {isPlusEnabled && (
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
                    ...(groupMenuItems.length > 0
                      ? [
                          {
                            type: "divider" as const,
                          },
                          ...groupMenuItems,
                        ]
                      : []),
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
      </Flex>
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};

export default SystemsTable;

import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMessage as message,
  AntModal as Modal,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import {
  useBulkAssignStewardMutation,
  useBulkDeleteSystemsMutation,
} from "~/features/system/system.slice";
import CreateSystemGroupForm from "~/features/system/system-groups/components/CreateSystemGroupForm";
import useSystemsTable from "~/features/system/useSystemsTable";
import { useGetAllUsersQuery } from "~/features/user-management";
import { isErrorResult } from "~/types/errors";

interface SystemActionsMenuProps {
  selectedRowKeys: React.Key[];
}

const SystemActionsMenu = ({ selectedRowKeys }: SystemActionsMenuProps) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);
  const [bulkAssignSteward] = useBulkAssignStewardMutation();

  const { plus: isPlusEnabled } = useFeatures();

  const {
    createModalIsOpen,
    setCreateModalIsOpen,
    handleCreateSystemGroup,
    groupMenuItems,
    handleBulkAddToGroup,
  } = useSystemsTable();

  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  const [bulkDeleteSystems] = useBulkDeleteSystemsMutation();

  const handleAssignSteward = useCallback(
    async (data_steward: string) => {
      const result = await bulkAssignSteward({
        data_steward,
        system_keys: selectedRowKeys as string[],
      });

      if (isErrorResult(result)) {
        messageApi.error(
          getErrorMessage(
            result.error,
            "A problem occurred assigning stewards",
          ),
        );
      } else {
        messageApi.success(
          `${selectedRowKeys.length} systems assigned to ${data_steward} successfully`,
        );
      }
    },
    [bulkAssignSteward, selectedRowKeys, messageApi],
  );

  const handleDelete = async () => {
    const result = await bulkDeleteSystems(selectedRowKeys as string[]);
    if (isErrorResult(result)) {
      messageApi.error(
        getErrorMessage(result.error, "A problem occurred deleting systems"),
      );
    } else {
      messageApi.success(
        `${selectedRowKeys.length} systems deleted successfully`,
      );
    }
  };

  const menuItems = useMemo(() => {
    const items = [];
    if (groupMenuItems.length && isPlusEnabled) {
      items.push(
        selectedRowKeys.length
          ? {
              key: "add-to-system-group",
              label: "Add to system group",
              children: [
                {
                  key: "new-group",
                  label: "Create new group +",
                  onClick: () => setCreateModalIsOpen(true),
                },
                {
                  type: "divider" as const,
                },
                ...groupMenuItems.map((group) => ({
                  key: group.key,
                  label: group.label,
                  onClick: () => handleBulkAddToGroup(group.key),
                })),
              ],
            }
          : {
              key: "new-group",
              label: "Create system group +",
              onClick: () => setCreateModalIsOpen(true),
            },
      );
    }
    if (allUsers?.items.length) {
      items.push(
        {
          key: "assign-data-steward",
          label: "Assign data steward",
          disabled: !selectedRowKeys.length,
          children: allUsers.items.map((user) => ({
            key: user.username,
            label: user.username,
            onClick: () => handleAssignSteward(user.username),
          })),
        },
        {
          type: "divider" as const,
        },
      );
    }
    items.push({
      key: "delete",
      label: "Delete",
      disabled: !selectedRowKeys.length,
      onClick: () => {
        setDeleteModalIsOpen(true);
      },
    });
    return items;
  }, [
    groupMenuItems,
    isPlusEnabled,
    allUsers?.items,
    selectedRowKeys.length,
    setCreateModalIsOpen,
    handleBulkAddToGroup,
    handleAssignSteward,
  ]);

  return (
    <>
      {contextHolder}
      <Modal
        open={deleteModalIsOpen}
        onCancel={() => setDeleteModalIsOpen(false)}
        onOk={handleDelete}
        okText="Delete"
        okType="danger"
        centered
      >
        <Typography.Paragraph>
          Delete {selectedRowKeys.length} systems? This action cannot be undone.
        </Typography.Paragraph>
      </Modal>
      <Modal
        open={createModalIsOpen}
        destroyOnHidden
        onCancel={() => setCreateModalIsOpen(false)}
        centered
        width={768}
        footer={null}
      >
        <CreateSystemGroupForm
          selectedSystemKeys={selectedRowKeys.map((key) => key.toString())}
          onSubmit={handleCreateSystemGroup}
          onCancel={() => setCreateModalIsOpen(false)}
        />
      </Modal>
      <Dropdown
        trigger={["click"]}
        menu={{
          items: menuItems,
        }}
      >
        <Button icon={<Icons.ChevronDown />}>Actions</Button>
      </Dropdown>
    </>
  );
};

export default SystemActionsMenu;

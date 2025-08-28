import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMessage as message,
  AntModal as Modal,
  Icons,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  useBulkAssignStewardMutation,
  useBulkDeleteSystemsMutation,
} from "~/features/system/system.slice";
import { useGetAllUsersQuery } from "~/features/user-management";
import { isErrorResult } from "~/types/errors";

interface SystemActionsMenuProps {
  selectedRowKeys: React.Key[];
}

const SystemActionsMenu = ({ selectedRowKeys }: SystemActionsMenuProps) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [deleteModal, deleteModalIsOpen] = useState(false);
  const [bulkAssignSteward] = useBulkAssignStewardMutation();

  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  const [bulkDeleteSystems] = useBulkDeleteSystemsMutation();

  const handleAssignSteward = async (data_steward: string) => {
    const result = await bulkAssignSteward({
      data_steward,
      system_keys: selectedRowKeys as string[],
    });

    if (isErrorResult(result)) {
      messageApi.error(
        getErrorMessage(result.error, "A problem occurred assigning stewards"),
      );
    } else {
      messageApi.success(
        `${selectedRowKeys.length} systems assigned to ${data_steward} successfully`,
      );
    }
  };

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

  return (
    <>
      {contextHolder}
      <Modal
        open={deleteModal}
        onCancel={() => deleteModalIsOpen(false)}
        onOk={handleDelete}
        okText="Delete"
        okType="danger"
        centered
      >
        <p>
          Delete {selectedRowKeys.length} systems? This action cannot be undone.
        </p>
      </Modal>
      <Dropdown
        trigger={["click"]}
        menu={{
          items: [
            {
              key: "assign-data-steward",
              label: "Assign data steward",
              children: allUsers?.items?.map((user) => ({
                key: user.username,
                label: user.username,
                onClick: () => handleAssignSteward(user.username),
              })),
            },
            {
              key: "delete",
              label: "Delete",
              onClick: () => {
                deleteModalIsOpen(true);
              },
            },
          ],
        }}
      >
        <Button
          disabled={selectedRowKeys.length === 0}
          icon={<Icons.ChevronDown />}
        >
          Actions
        </Button>
      </Dropdown>
    </>
  );
};

export default SystemActionsMenu;

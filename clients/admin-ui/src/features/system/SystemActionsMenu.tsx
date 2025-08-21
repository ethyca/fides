import { AntButton, AntDropdown, AntMessage, AntModal, Icons } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useBulkDeleteSystemsMutation } from "~/features/system/system.slice";
import { useGetAllUsersQuery } from "~/features/user-management";
import { isErrorResult } from "~/types/errors";

interface SystemActionsMenuProps {
  selectedRowKeys: React.Key[];
}

const SystemActionsMenu = ({ selectedRowKeys }: SystemActionsMenuProps) => {
  const [messageApi, contextHolder] = AntMessage.useMessage();
  const [deleteModal, deleteModalIsOpen] = useState(false);

  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  const [bulkDeleteSystems] = useBulkDeleteSystemsMutation();

  const handleAssignSteward = (stewardId: string) => {
    console.log("assign steward", stewardId, selectedRowKeys);
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
      <AntModal
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
      </AntModal>
      <AntDropdown
        trigger={["click"]}
        menu={{
          items: [
            {
              key: "assign-data-steward",
              label: "Assign data steward",
              children: allUsers?.items?.map((user) => ({
                key: user.id,
                label: user.username,
                onClick: () => handleAssignSteward(user.id),
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
        <AntButton
          disabled={selectedRowKeys.length === 0}
          icon={<Icons.ChevronDown />}
        >
          Actions
        </AntButton>
      </AntDropdown>
    </>
  );
};

export default SystemActionsMenu;

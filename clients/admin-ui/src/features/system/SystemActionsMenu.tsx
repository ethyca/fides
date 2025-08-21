import { AntButton, AntDropdown, Icons } from "fidesui";

import { useGetAllUsersQuery } from "~/features/user-management";

interface SystemActionsMenuProps {
  selectedRowKeys: React.Key[];
}

const SystemActionsMenu = ({ selectedRowKeys }: SystemActionsMenuProps) => {
  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  const handleAssignSteward = (stewardId: string) => {
    console.log("assign steward", stewardId, selectedRowKeys);
  };

  return (
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
              console.log("delete");
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
  );
};

export default SystemActionsMenu;

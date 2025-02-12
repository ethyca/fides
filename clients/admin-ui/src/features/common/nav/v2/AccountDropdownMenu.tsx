import { AntButton as Button, AntDropdown as Dropdown, Icons } from "fidesui";

interface AccountDropdownMenuProps {
  username: string;
  onLogout: () => void;
}

const AccountDropdownMenu = ({
  username,
  onLogout,
}: AccountDropdownMenuProps) => {
  return (
    <Dropdown
      menu={{
        items: [
          {
            key: "1",
            label: <span data-testid="header-menu-button">{username}</span>,
            type: "group",
          },
          { type: "divider" },
          {
            key: "2",
            label: <span data-testid="header-menu-sign-out">Sign out</span>,
            onClick: onLogout,
          },
        ],
      }}
      overlayStyle={{ width: "200px" }}
      trigger={["click", "hover"]}
    >
      <Button
        tabIndex={0}
        className="border-none bg-transparent hover:!bg-gray-700 focus:!bg-gray-700"
        icon={<Icons.User color="white" />}
      />
    </Dropdown>
  );
};
export default AccountDropdownMenu;

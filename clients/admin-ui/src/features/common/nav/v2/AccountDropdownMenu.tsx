import { AntButton as Button, AntDropdown as Dropdown, Icons } from "fidesui";

import styles from "./AccountDropdownMenu.module.scss";

interface AccountDropdownMenuProps {
  username: string;
  onLogout: () => void;
}

const AccountDropdownMenu = ({
  username,
  onLogout,
}: AccountDropdownMenuProps) => {
  return (
    <div className={styles.container}>
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
      >
        <Button
          className="border-none bg-transparent  hover:!bg-gray-700"
          icon={<Icons.User color="white" />}
        />
      </Dropdown>
    </div>
  );
};
export default AccountDropdownMenu;

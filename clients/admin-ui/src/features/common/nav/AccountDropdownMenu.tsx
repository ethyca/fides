import { AntButton as Button, AntDropdown as Dropdown, Icons } from "fidesui";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth/auth.slice";

import { USER_DETAIL_ROUTE } from "./routes";

interface AccountDropdownMenuProps {
  onLogout: () => void;
}

const AccountDropdownMenu = ({ onLogout }: AccountDropdownMenuProps) => {
  const user = useAppSelector(selectUser);
  const userId = user?.id;
  const username = user?.username;
  const isRootUser = user?.isRootUser;

  return (
    <Dropdown
      menu={{
        items: [
          {
            key: "1",
            label: isRootUser ? (
              <span data-testid="header-menu-username">{username}</span>
            ) : (
              <NextLink href={USER_DETAIL_ROUTE.replace("[id]", userId!)}>
                <span data-testid="header-menu-username">{username}</span>
              </NextLink>
            ),
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
        type="primary"
        className="border-none bg-transparent hover:!bg-gray-700 focus:!bg-gray-700"
        icon={<Icons.User />}
        data-testid="header-menu-button"
      />
    </Dropdown>
  );
};
export default AccountDropdownMenu;

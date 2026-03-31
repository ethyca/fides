import { Button, Dropdown, Icons, Typography } from "fidesui";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth/auth.slice";

import { USER_DETAIL_ROUTE } from "./routes";

interface AccountDropdownMenuProps {
  onLogout: () => void;
  className?: string;
}

const AccountDropdownMenu = ({
  onLogout,
  className,
}: AccountDropdownMenuProps) => {
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
              <Typography.Text data-testid="header-menu-username">
                {username}
              </Typography.Text>
            ) : (
              <NextLink href={USER_DETAIL_ROUTE.replace("[id]", userId!)}>
                <Typography.Link data-testid="header-menu-username">
                  {username}
                </Typography.Link>
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
      styles={{ root: { width: "200px" } }}
      trigger={["click", "hover"]}
    >
      <Button
        tabIndex={0}
        type="primary"
        className={className}
        icon={<Icons.User />}
        aria-label="User menu"
        data-testid="header-menu-button"
      />
    </Dropdown>
  );
};
export default AccountDropdownMenu;

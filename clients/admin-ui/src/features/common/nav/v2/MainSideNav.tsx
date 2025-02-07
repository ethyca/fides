import {
  AntButton,
  AntMenuProps as MenuProps,
  Box,
  Icons,
  Link,
  VStack,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useRouter } from "next/router";

import logoImage from "~/../public/logo-white.svg";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { LOGIN_ROUTE } from "~/constants";
import { logout, selectUser, useLogoutMutation } from "~/features/auth";
import Image from "~/features/common/Image";
import { useGetHealthQuery } from "~/features/plus/plus.slice";

import AccountDropdownMenu from "./AccountDropdownMenu";
import { useNav } from "./hooks";
import { ActiveNav, NavGroup } from "./nav-config";
import { NavMenu } from "./NavMenu";
import { INDEX_ROUTE } from "./routes";

const NAV_BACKGROUND_COLOR = palette.FIDESUI_MINOS;
const NAV_WIDTH = "240px";

/** Inner component which we export for component testing */
export const UnconnectedMainSideNav = ({
  groups,
  active,
  handleLogout,
  username,
}: {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  handleLogout: any;
  username: string;
}) => {
  const router = useRouter();

  const navMenuItems = groups.map((group) => ({
    key: group.title,
    icon: group.icon,
    label: <span data-testid={`${group.title}-nav-group`}>{group.title}</span>,
    children: group.children.map((child) => ({
      key: child.path,
      // child label needs left margin/padding to align with group title
      label: (
        <span data-testid={`${child.title}-nav-link`} className="ml-4 pl-0.5">
          {child.title}
        </span>
      ),
    })),
  }));

  const getActiveKeyFromUrl = () => {
    if (!active) {
      return null;
    }

    const activeItem = groups
      .flatMap((group) => group.children)
      .find((child) => {
        if (child.exact) {
          return active?.path === child.path;
        }
        return active?.path ? active?.path.startsWith(child.path) : false;
      });

    return activeItem?.path || null;
  };

  const activeKey = getActiveKeyFromUrl();

  const handleMenuItemClick: MenuProps["onClick"] = ({ key: path }) => {
    router.push(path);
  };

  return (
    <Box
      px={2}
      pb={0}
      pt={4}
      minWidth={NAV_WIDTH}
      maxWidth={NAV_WIDTH}
      backgroundColor={NAV_BACKGROUND_COLOR}
      height="100%"
      overflow="auto"
    >
      <VStack
        as="nav"
        alignItems="start"
        color="white"
        height="100%"
        justifyContent="space-between"
      >
        <Box width="100%">
          <Box pb={6}>
            <Box px={2}>
              <Link as={NextLink} href={INDEX_ROUTE} display="flex">
                <Image src={logoImage} alt="Fides Logo" width={116} />
              </Link>
            </Box>
          </Box>
          <NavMenu
            onClick={handleMenuItemClick}
            items={navMenuItems}
            selectedKeys={activeKey ? [activeKey] : []}
          />
        </Box>
        <Box alignItems="center" pb={4}>
          <AntButton
            href="https://docs.ethyca.com"
            target="_blank"
            className="border-none bg-transparent  hover:!bg-gray-700"
            icon={<Icons.Help color="white" />}
          />
          {username && (
            <AccountDropdownMenu username={username} onLogout={handleLogout} />
          )}
        </Box>
      </VStack>
    </Box>
  );
};

const MainSideNav = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });
  const [logoutMutation] = useLogoutMutation();
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);
  const plusQuery = useGetHealthQuery();
  const username = user ? user.username : "";

  const handleLogout = async () => {
    await logoutMutation({});
    // Go to Login page first, then dispatch logout so that ProtectedRoute does not
    // tack on a redirect URL. We don't need a redirect URL if we are just logging out!
    router.push(LOGIN_ROUTE).then(() => {
      dispatch(logout());
    });
  };

  // While we are loading if we have plus, the nav isn't ready to display yet
  // since otherwise new items can suddenly pop in. So instead, we render an empty
  // version of the nav during load, so that when the nav does load, it is fully featured.
  if (plusQuery.isLoading) {
    return (
      <Box
        minWidth={NAV_WIDTH}
        maxWidth={NAV_WIDTH}
        backgroundColor={NAV_BACKGROUND_COLOR}
        height="100%"
      />
    );
  }

  return (
    <UnconnectedMainSideNav
      {...nav}
      handleLogout={handleLogout}
      username={username}
    />
  );
};

export default MainSideNav;

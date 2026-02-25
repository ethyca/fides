import {
  Button,
  ChakraBox as Box,
  ChakraVStack as VStack,
  Icons,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React from "react";

import logoCollapsed from "~/../public/logo-collapsed.svg";
import logoExpanded from "~/../public/logo-expanded.svg";
import { useAppDispatch } from "~/app/hooks";
import { LOGIN_ROUTE } from "~/constants";
import { logout, useLogoutMutation } from "~/features/auth";
import Image from "~/features/common/Image";
import { useGetHealthQuery } from "~/features/plus/plus.slice";

import AccountDropdownMenu from "./AccountDropdownMenu";
import { useNav } from "./hooks";
import { ActiveNav, NavGroup } from "./nav-config";
import { NavMenu } from "./NavMenu";
import navStyles from "./NavMenu.module.scss";

const NAV_BACKGROUND_COLOR = palette.FIDESUI_MINOS;
const NAV_WIDTH = "240px";
const COLLAPSED_WIDTH = "80px";
const OPENED_TOGGLES_LOCAL_STORAGE_KEY = "mainSideNavOpenKeys";
const COLLAPSED_LOCAL_STORAGE_KEY = "mainSideNavCollapsed";

const LOGO_FULL_WIDTH = 107;
const LOGO_HEIGHT = 24;
const LOGO_ICON_SIZE = 24;

/** Inner component which we export for component testing */
export const UnconnectedMainSideNav = ({
  groups,
  active,
  handleLogout,
  collapsed = false,
  onCollapseToggle,
}: {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  handleLogout: any;
  collapsed?: boolean;
  onCollapseToggle?: () => void;
}) => {
  const navMenuItems = groups
    .filter((group) => group.children.some((child) => !child.hidden)) // Only include groups with visible children
    .map((group) => ({
      key: group.title,
      icon: group.icon,
      popupClassName: navStyles.flyout,
      popupOffset: [12, 0],
      label: (
        <span data-testid={`${group.title}-nav-group`}>{group.title}</span>
      ),
      children: group.children
        .filter((child) => !child.hidden) // Filter out hidden routes from UI
        .map((child) => ({
          key: child.path,
          // child label needs left margin/padding to align with group title
          label: (
            <NextLink
              href={child.path}
              data-testid={`${child.title}-nav-link`}
              className="ml-4 pl-0.5"
            >
              {child.title}
            </NextLink>
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

  // When the nav is first loaded, we want to open the toggles that were open when the user last visited
  // the page. This is stored in local storage so that it persists across refreshes.
  const getStartupOpenKeys = () => {
    const openedKeysString = localStorage.getItem(
      OPENED_TOGGLES_LOCAL_STORAGE_KEY,
    );
    let openedKeys = [];
    if (openedKeysString) {
      try {
        openedKeys = JSON.parse(openedKeysString);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error("Error parsing local storage key", e);
      }
    }

    // If the active key is not in the opened keys, add it
    const activeParentKey = active?.title;
    if (activeParentKey && !openedKeys.includes(activeParentKey)) {
      openedKeys.push(activeParentKey);
    }

    return openedKeys;
  };

  const handleOpenChange = (keys: string[]) => {
    localStorage.setItem(
      OPENED_TOGGLES_LOCAL_STORAGE_KEY,
      JSON.stringify(keys),
    );
  };

  const navWidth = collapsed ? COLLAPSED_WIDTH : NAV_WIDTH;

  return (
    <Box
      px={collapsed ? 0 : 2}
      pb={0}
      pt={4}
      minWidth={navWidth}
      maxWidth={navWidth}
      backgroundColor={NAV_BACKGROUND_COLOR}
      height="100%"
      overflowX="hidden"
      overflowY="auto"
      sx={{
        transition:
          "min-width 0.35s ease, max-width 0.35s ease, padding 0.35s ease",
      }}
    >
      <VStack
        as="nav"
        alignItems="stretch"
        color="white"
        height="100%"
        justifyContent="space-between"
      >
        <Box width="100%">
          <Box
            pb={6}
            px={4}
            display="flex"
            justifyContent={collapsed ? "center" : "flex-start"}
          >
            <button
              type="button"
              className="inline-flex cursor-pointer rounded border-none bg-transparent p-0 hover:bg-gray-700"
              onClick={onCollapseToggle}
              aria-label={
                collapsed
                  ? "Expand navigation menu"
                  : "Collapse navigation menu"
              }
              data-testid="nav-collapse-toggle"
            >
              <Box
                position="relative"
                width={
                  collapsed ? `${LOGO_ICON_SIZE}px` : `${LOGO_FULL_WIDTH}px`
                }
                height={`${LOGO_HEIGHT}px`}
                sx={{
                  transition: "width 0.35s ease",
                }}
              >
                <Box
                  position="absolute"
                  inset={0}
                  opacity={collapsed ? 0 : 1}
                  sx={{
                    transition: "opacity 0.35s ease",
                    pointerEvents: collapsed ? "none" : "auto",
                  }}
                >
                  <Image
                    src={logoExpanded}
                    alt="Fides Logo"
                    width={LOGO_FULL_WIDTH}
                    height={LOGO_HEIGHT}
                    priority
                  />
                </Box>
                <Box
                  position="absolute"
                  inset={0}
                  opacity={collapsed ? 1 : 0}
                  sx={{
                    transition: "opacity 0.35s ease",
                    pointerEvents: collapsed ? "auto" : "none",
                  }}
                >
                  <Image
                    src={logoCollapsed}
                    alt="Fides Logo"
                    width={LOGO_ICON_SIZE}
                    height={LOGO_ICON_SIZE}
                    priority
                  />
                </Box>
              </Box>
            </button>
          </Box>
          <NavMenu
            items={navMenuItems}
            selectedKeys={activeKey ? [activeKey] : []}
            onOpenChange={handleOpenChange}
            defaultOpenKeys={getStartupOpenKeys()}
            inlineCollapsed={collapsed}
          />
        </Box>
        <Box
          alignItems="center"
          justifyContent={collapsed ? "center" : "flex-start"}
          pb={4}
          px={4}
          width="100%"
          display="flex"
          flexDirection={collapsed ? "column" : "row"}
          gap={collapsed ? 2 : 0}
        >
          <Button
            type="primary"
            href="https://docs.ethyca.com"
            target="_blank"
            className="border-none bg-transparent  hover:!bg-gray-700"
            icon={<Icons.Help />}
            aria-label="Help"
          />
          <div className="inline-block">
            <AccountDropdownMenu onLogout={handleLogout} />
          </div>
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
  const plusQuery = useGetHealthQuery();

  const [collapsed, setCollapsed] = React.useState(false);

  React.useEffect(() => {
    const stored = localStorage.getItem(COLLAPSED_LOCAL_STORAGE_KEY);
    if (stored === "true") {
      setCollapsed(true);
    }
  }, []);

  const toggleCollapsed = React.useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem(COLLAPSED_LOCAL_STORAGE_KEY, String(next));
      }
      return next;
    });
  }, []);

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
      collapsed={collapsed}
      onCollapseToggle={toggleCollapsed}
    />
  );
};

export default MainSideNav;

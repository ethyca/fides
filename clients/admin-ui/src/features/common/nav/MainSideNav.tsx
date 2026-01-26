import {
  Button,
  ChakraBox as Box,
  ChakraVStack as VStack,
  Icons,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import logoImage from "~/../public/logo-white.svg";
import logoIconImage from "~/../public/logo-icon-white.svg";
import { useAppDispatch } from "~/app/hooks";
import { LOGIN_ROUTE } from "~/constants";
import { logout, useLogoutMutation } from "~/features/auth";
import Image from "~/features/common/Image";
import { useGetHealthQuery } from "~/features/plus/plus.slice";

import AccountDropdownMenu from "./AccountDropdownMenu";
import { useNav } from "./hooks";
import { ActiveNav, NavGroup } from "./nav-config";
import { NavMenu } from "./NavMenu";
import { INDEX_ROUTE } from "./routes";
import styles from "./MainSideNav.module.scss";

const NAV_BACKGROUND_COLOR = palette.FIDESUI_MINOS;
const NAV_WIDTH_EXPANDED = "240px";
const NAV_WIDTH_COLLAPSED = "64px";
const OPENED_TOGGLES_LOCAL_STORAGE_KEY = "mainSideNavOpenKeys";
const NAV_COLLAPSED_LOCAL_STORAGE_KEY = "mainSideNavCollapsed";

/** Inner component which we export for component testing */
export const UnconnectedMainSideNav = ({
  groups,
  active,
  handleLogout,
}: {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  handleLogout: any;
}) => {
  // Collapsed state with localStorage persistence
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize collapsed state from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(NAV_COLLAPSED_LOCAL_STORAGE_KEY);
    if (stored !== null) {
      setIsCollapsed(stored === "true");
    }
    setIsInitialized(true);
  }, []);

  // Persist collapsed state
  const toggleCollapsed = useCallback(() => {
    setIsCollapsed((prev) => {
      const newValue = !prev;
      localStorage.setItem(NAV_COLLAPSED_LOCAL_STORAGE_KEY, String(newValue));
      return newValue;
    });
  }, []);

  const navMenuItems = groups
    .filter((group) => group.children.some((child) => !child.hidden)) // Only include groups with visible children
    .map((group) => ({
      key: group.title,
      icon: group.icon,
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

  const currentNavWidth = isCollapsed ? NAV_WIDTH_COLLAPSED : NAV_WIDTH_EXPANDED;

  return (
    <Box
      className={`${styles.navContainer} ${isCollapsed ? styles.collapsed : ""}`}
      style={{
        minWidth: currentNavWidth,
        maxWidth: currentNavWidth,
        backgroundColor: NAV_BACKGROUND_COLOR,
        // Don't animate on initial render
        transition: isInitialized ? "min-width 0.2s ease, max-width 0.2s ease" : "none",
      }}
    >
      <VStack
        as="nav"
        alignItems="start"
        color="white"
        height="100%"
        justifyContent="space-between"
        className={styles.navContent}
      >
        <Box width="100%">
          <Box pb={6} className={styles.logoContainer}>
            <button
              type="button"
              onClick={toggleCollapsed}
              className={styles.logoButton}
              aria-label={isCollapsed ? "Expand navigation" : "Collapse navigation"}
              title={isCollapsed ? "Expand navigation" : "Collapse navigation"}
            >
              {isCollapsed ? (
                <Image
                  src={logoIconImage}
                  alt="Fides Logo"
                  width={32}
                  height={32}
                  priority
                  className={styles.logoIcon}
                />
              ) : (
                <Image
                  src={logoImage}
                  alt="Fides Logo"
                  width={116}
                  priority
                  className={styles.logoFull}
                />
              )}
            </button>
          </Box>
          <NavMenu
            items={navMenuItems}
            selectedKeys={activeKey ? [activeKey] : []}
            onOpenChange={handleOpenChange}
            defaultOpenKeys={isCollapsed ? [] : getStartupOpenKeys()}
            inlineCollapsed={isCollapsed}
          />
        </Box>
        <Box
          alignItems="center"
          pb={4}
          className={`${styles.bottomSection} ${isCollapsed ? styles.collapsed : ""}`}
        >
          <Button
            type="primary"
            href="https://docs.ethyca.com"
            target="_blank"
            className="border-none bg-transparent hover:!bg-gray-700"
            icon={<Icons.Help />}
            aria-label="Help"
          />
          {!isCollapsed && (
            <div className="inline-block">
              <AccountDropdownMenu onLogout={handleLogout} />
            </div>
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
  const plusQuery = useGetHealthQuery();

  // Get initial collapsed state for loading skeleton
  const [initialWidth, setInitialWidth] = useState(NAV_WIDTH_EXPANDED);

  useEffect(() => {
    const stored = localStorage.getItem(NAV_COLLAPSED_LOCAL_STORAGE_KEY);
    if (stored === "true") {
      setInitialWidth(NAV_WIDTH_COLLAPSED);
    }
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
        minWidth={initialWidth}
        maxWidth={initialWidth}
        backgroundColor={NAV_BACKGROUND_COLOR}
        height="100%"
        style={{ transition: "min-width 0.2s ease, max-width 0.2s ease" }}
      />
    );
  }

  return <UnconnectedMainSideNav {...nav} handleLogout={handleLogout} />;
};

export default MainSideNav;

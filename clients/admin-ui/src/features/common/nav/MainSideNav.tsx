import {
  Button,
  ChakraBox as Box,
  ChakraVStack as VStack,
  Icons,
} from "fidesui";
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
import styles from "./NavMenu.module.scss";
import NavSearch from "./NavSearch";
import { RouterLink } from "./RouterLink";

const NAV_BACKGROUND_COLOR = "var(--fidesui-minos)";
const NAV_WIDTH = "240px";
const COLLAPSED_WIDTH = "80px";
const OPENED_TOGGLES_LOCAL_STORAGE_KEY = "mainSideNavOpenKeys";
const COLLAPSED_LOCAL_STORAGE_KEY = "mainSideNavCollapsed";

const LOGO_FULL_WIDTH = 107;
const LOGO_HEIGHT = 24;
const LOGO_ICON_SIZE = 24;

interface UnconnectedMainSideNavProps {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  handleLogout: () => Promise<void>;
  collapsed?: boolean;
  onCollapseToggle?: () => void;
}

/** Inner component which we export for component testing */
export const UnconnectedMainSideNav = ({
  groups,
  active,
  handleLogout,
  collapsed = false,
  onCollapseToggle,
}: UnconnectedMainSideNavProps) => {
  const navMenuItems = groups
    .filter((group) => group.children.some((child) => !child.hidden)) // Only include groups with visible children
    .map((group) => ({
      key: group.title,
      icon: group.icon,
      popupClassName: styles.flyout,
      popupOffset: [12, 0],
      label: (
        <span data-testid={`${group.title}-nav-group`}>{group.title}</span>
      ),
      children: [
        ...(collapsed
          ? [
              {
                key: `${group.title}-header`,
                label: (
                  <span className={styles.flyoutHeader}>{group.title}</span>
                ),
                disabled: true,
              },
            ]
          : []),
        ...group.children
          .filter((child) => !child.hidden)
          .map((child) => ({
            key: child.path,
            label: (
              <RouterLink
                unstyled
                href={child.path}
                data-testid={`${child.title}-nav-link`}
                className="ml-4 pl-0.5"
              >
                {child.title}
              </RouterLink>
            ),
          })),
      ],
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
    <div
      className={`${styles.navContainer} ${collapsed ? styles.navContainerCollapsed : styles.navContainerExpanded}`}
      style={{
        minWidth: navWidth,
        maxWidth: navWidth,
        backgroundColor: NAV_BACKGROUND_COLOR,
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
          <div
            className={`${styles.logoWrapper} ${collapsed ? styles.logoWrapperCollapsed : styles.logoWrapperExpanded}`}
          >
            <button
              type="button"
              className={styles.logoToggle}
              onClick={onCollapseToggle}
              aria-label={
                collapsed
                  ? "Expand navigation menu"
                  : "Collapse navigation menu"
              }
            >
              <div
                className={styles.logoContainer}
                style={{
                  width: collapsed
                    ? `${LOGO_ICON_SIZE}px`
                    : `${LOGO_FULL_WIDTH}px`,
                  height: `${LOGO_HEIGHT}px`,
                }}
              >
                <div
                  className={`${styles.logoImage} ${collapsed ? styles.logoImageHidden : styles.logoImageVisible}`}
                >
                  <Image
                    src={logoExpanded}
                    alt="Fides Logo"
                    width={LOGO_FULL_WIDTH}
                    height={LOGO_HEIGHT}
                    priority
                  />
                </div>
                <div
                  className={`${styles.logoImage} ${collapsed ? styles.logoImageVisible : styles.logoImageHidden}`}
                >
                  <Image
                    src={logoCollapsed}
                    alt="Fides Logo"
                    width={LOGO_ICON_SIZE}
                    height={LOGO_ICON_SIZE}
                    priority
                  />
                </div>
              </div>
            </button>
          </div>
          <NavSearch groups={groups} collapsed={collapsed} />
          <NavMenu
            items={navMenuItems}
            selectedKeys={activeKey ? [activeKey] : []}
            onOpenChange={handleOpenChange}
            defaultOpenKeys={getStartupOpenKeys()}
            inlineCollapsed={collapsed}
          />
        </Box>
        <div
          className={`${styles.bottomBar} ${collapsed ? styles.bottomBarCollapsed : styles.bottomBarExpanded}`}
        >
          <div className={styles.bottomBarLeft}>
            <Button
              type="primary"
              href="https://docs.ethyca.com"
              target="_blank"
              className={styles.navBottomButton}
              icon={<Icons.Help />}
              aria-label="Help"
            />
            <div className="inline-block">
              <AccountDropdownMenu
                onLogout={handleLogout}
                className={styles.navBottomButton}
              />
            </div>
          </div>
          <button
            type="button"
            className={styles.collapseToggle}
            onClick={onCollapseToggle}
            aria-label={
              collapsed ? "Expand navigation menu" : "Collapse navigation menu"
            }
            data-testid="nav-collapse-toggle"
          >
            {collapsed ? (
              <Icons.SidePanelOpen size={20} />
            ) : (
              <Icons.SidePanelClose size={20} />
            )}
          </button>
        </div>
      </VStack>
    </div>
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
      <div
        style={{
          minWidth: NAV_WIDTH,
          maxWidth: NAV_WIDTH,
          backgroundColor: NAV_BACKGROUND_COLOR,
          height: "100%",
        }}
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

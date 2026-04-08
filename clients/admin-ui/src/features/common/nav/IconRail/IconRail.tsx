import { Button, Icons } from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useCallback, useRef, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { LOGIN_ROUTE } from "~/constants";
import { logout, useLogoutMutation } from "~/features/auth";
import Image from "~/features/common/Image";
import { useGetHealthQuery } from "~/features/plus/plus.slice";

import logoCollapsed from "../../../../../public/logo-collapsed.svg";
import AccountDropdownMenu from "../AccountDropdownMenu";
import { useNav } from "../hooks";
import { NavGroup } from "../nav-config";
import NavSearch from "../NavSearch";
import ExpandedNav from "./ExpandedNav";
import styles from "./IconRail.module.scss";
import IconRailItem from "./IconRailItem";

const LOGO_ICON_SIZE = 24;
const LAST_VISITED_KEY = "fides-last-visited-pillar";

const IconRail: React.FC = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });
  const [logoutMutation] = useLogoutMutation();
  const dispatch = useAppDispatch();
  const plusQuery = useGetHealthQuery();

  const [expanded, setExpanded] = useState(false);
  const [highlightedGroup, setHighlightedGroup] = useState<string | null>(null);
  const collapseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    if (collapseTimerRef.current) {
      clearTimeout(collapseTimerRef.current);
      collapseTimerRef.current = null;
    }
    setExpanded(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    collapseTimerRef.current = setTimeout(() => {
      setExpanded(false);
      setHighlightedGroup(null);
    }, 150);
  }, []);

  const handleLogout = useCallback(async () => {
    await logoutMutation({});
    router.push(LOGIN_ROUTE).then(() => {
      dispatch(logout());
    });
  }, [logoutMutation, router, dispatch]);

  const handleNavigate = useCallback(() => {
    setExpanded(false);
    setHighlightedGroup(null);
  }, []);

  const getLastVisitedPath = useCallback((groupTitle: string): string | null => {
    try {
      const stored = localStorage.getItem(LAST_VISITED_KEY);
      if (stored) {
        const map = JSON.parse(stored) as Record<string, string>;
        return map[groupTitle] ?? null;
      }
    } catch {
      // ignore
    }
    return null;
  }, []);

  const saveLastVisitedPath = useCallback((groupTitle: string, path: string) => {
    try {
      const stored = localStorage.getItem(LAST_VISITED_KEY);
      const map = stored ? (JSON.parse(stored) as Record<string, string>) : {};
      map[groupTitle] = path;
      localStorage.setItem(LAST_VISITED_KEY, JSON.stringify(map));
    } catch {
      // ignore
    }
  }, []);

  // Save current page per pillar on route change
  React.useEffect(() => {
    if (nav.active?.title) {
      const activePath = nav.active.path;
      if (activePath) {
        saveLastVisitedPath(nav.active.title, activePath);
      }
    }
  }, [nav.active, saveLastVisitedPath]);

  const navigateToGroup = useCallback(
    (group: NavGroup) => {
      const lastVisited = getLastVisitedPath(group.title);
      if (lastVisited) {
        router.push(lastVisited);
        handleNavigate();
        return;
      }
      const firstChild = group.children.find((child) => !child.hidden);
      if (firstChild) {
        router.push(firstChild.path);
        handleNavigate();
      }
    },
    [router, handleNavigate, getLastVisitedPath],
  );

  // Show loading placeholder while Plus status is loading
  if (plusQuery.isLoading) {
    return (
      <div className={styles.railWrapper}>
        <div className={styles.loadingPlaceholder} />
      </div>
    );
  }

  // Separate Settings from other groups for bottom placement
  const settingsGroup = nav.groups.find((g) => g.title === "Settings");
  const mainGroups = nav.groups.filter((g) => g.title !== "Settings");

  return (
    <div className={styles.railWrapper}>
      <div
        className={`${styles.rail} ${expanded ? styles.railExpanded : ""}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div
          className={`${styles.railTop} ${expanded ? styles.railExpandedTop : ""}`}
        >
          {/* Logo */}
          <NextLink
            href="/"
            className={`${styles.logo} ${expanded ? styles.logoExpanded : ""}`}
            aria-label="Home"
          >
            <Image
              src={logoCollapsed}
              alt="Fides"
              width={LOGO_ICON_SIZE}
              height={LOGO_ICON_SIZE}
              priority
            />
          </NextLink>

          {expanded ? (
            <>
              <ExpandedNav
                groups={mainGroups}
                active={nav.active}
                highlightedGroup={highlightedGroup}
                onNavigate={handleNavigate}
              />
              {settingsGroup && (
                <>
                  <div className={styles.separator} />
                  <ExpandedNav
                    groups={[settingsGroup]}
                    active={nav.active}
                    highlightedGroup={highlightedGroup}
                    onNavigate={handleNavigate}
                  />
                </>
              )}
            </>
          ) : (
            <>
              {mainGroups.map((group) => (
                <IconRailItem
                  key={group.title}
                  icon={group.icon}
                  title={group.title}
                  isActive={nav.active?.title === group.title}
                  onClick={() => navigateToGroup(group)}
                  onMouseEnter={() => setHighlightedGroup(group.title)}
                />
              ))}
            </>
          )}
        </div>

        {/* Bottom section */}
        <div
          className={`${styles.railBottom} ${expanded ? styles.railExpandedBottom : ""}`}
        >
          {settingsGroup && !expanded && (
            <IconRailItem
              icon={<Icons.Settings />}
              title="Settings"
              isActive={nav.active?.title === "Settings"}
              onClick={() => navigateToGroup(settingsGroup)}
              onMouseEnter={() => setHighlightedGroup("Settings")}
            />
          )}
          <Button
            type="primary"
            href="https://docs.ethyca.com"
            target="_blank"
            className={
              expanded
                ? `${styles.bottomButton} ${styles.bottomButtonExpanded}`
                : styles.bottomButton
            }
            icon={<Icons.Help />}
            aria-label="Help"
          >
            {expanded && <span className={styles.bottomLabel}>Help</span>}
          </Button>
          <AccountDropdownMenu
            onLogout={handleLogout}
            className={
              expanded
                ? `${styles.bottomButton} ${styles.bottomButtonExpanded}`
                : styles.bottomButton
            }
          />
        </div>

        {/* NavSearch - renders Cmd+K listener and modal only */}
        <NavSearch groups={nav.groups} collapsed />
      </div>
    </div>
  );
};

export default IconRail;

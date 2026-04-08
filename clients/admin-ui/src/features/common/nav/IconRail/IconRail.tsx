import { Icons } from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useCallback, useRef, useState } from "react";

import Image from "~/features/common/Image";
import { useGetHealthQuery } from "~/features/plus/plus.slice";

import logoCollapsed from "../../../../../public/logo-collapsed.svg";
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

  // Separate bottom groups (Settings + Integrations) from pillar groups
  // Dashboard is accessible via logo, not shown as a rail icon
  const settingsGroup = nav.groups.find((g) => g.title === "Settings");
  const integrationsGroup = nav.groups.find((g) => g.title === "Integrations");
  const bottomGroupTitles = new Set(["Settings", "Integrations", "Dashboard"]);
  const mainGroups = nav.groups.filter((g) => !bottomGroupTitles.has(g.title));

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
            <ExpandedNav
              groups={mainGroups}
              active={nav.active}
              highlightedGroup={highlightedGroup}
              onNavigate={handleNavigate}
            />
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

        {/* Bottom section: Integrations + Settings */}
        <div
          className={`${styles.railBottom} ${expanded ? styles.railExpandedBottom : ""}`}
        >
          {expanded ? (
            <>
              {integrationsGroup && (
                <ExpandedNav
                  groups={[integrationsGroup]}
                  active={nav.active}
                  highlightedGroup={highlightedGroup}
                  onNavigate={handleNavigate}
                />
              )}
              {settingsGroup && (
                <ExpandedNav
                  groups={[settingsGroup]}
                  active={nav.active}
                  highlightedGroup={highlightedGroup}
                  onNavigate={handleNavigate}
                />
              )}
            </>
          ) : (
            <>
              {integrationsGroup && (
                <IconRailItem
                  icon={integrationsGroup.icon}
                  title="Integrations"
                  isActive={nav.active?.title === "Integrations"}
                  onClick={() => navigateToGroup(integrationsGroup)}
                  onMouseEnter={() => setHighlightedGroup("Integrations")}
                  className={styles.integrationsIcon}
                />
              )}
              {settingsGroup && (
                <IconRailItem
                  icon={<Icons.Settings />}
                  title="Settings"
                  isActive={nav.active?.title === "Settings"}
                  onClick={() => navigateToGroup(settingsGroup)}
                  onMouseEnter={() => setHighlightedGroup("Settings")}
                />
              )}
            </>
          )}
        </div>

        {/* NavSearch - renders Cmd+K listener and modal only */}
        <NavSearch groups={nav.groups} collapsed />
      </div>
    </div>
  );
};

export default IconRail;

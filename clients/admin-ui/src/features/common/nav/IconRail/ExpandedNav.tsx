import NextLink from "next/link";
import React, { useEffect, useRef } from "react";

import { ActiveNav, NavGroup, NavGroupChild } from "../nav-config";
import styles from "./IconRail.module.scss";

interface ExpandedNavProps {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  highlightedGroup: string | null;
  onNavigate?: () => void;
}

const ExpandedNav: React.FC<ExpandedNavProps> = ({
  groups,
  active,
  highlightedGroup,
  onNavigate,
}) => {
  const sectionRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  useEffect(() => {
    if (highlightedGroup) {
      const el = sectionRefs.current.get(highlightedGroup);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }, [highlightedGroup]);

  const isActivePage = (child: NavGroupChild): boolean => {
    if (!active?.path) return false;
    if (child.exact) return active.path === child.path;
    return active.path === child.path;
  };

  const isActiveGroup = (group: NavGroup): boolean => {
    return active?.title === group.title;
  };

  const getFirstVisibleRoute = (group: NavGroup): string => {
    const firstChild = group.children.find((child) => !child.hidden);
    return firstChild?.path ?? "/";
  };

  return (
    <div className={styles.expandedNav}>
      {groups.map((group) => {
        const visibleChildren = group.children.filter(
          (child) => !child.hidden,
        );
        if (!visibleChildren.length) return null;

        const isHighlighted = highlightedGroup === group.title;
        const isGroupActive = isActiveGroup(group);

        return (
          <div
            key={group.title}
            className={`${styles.sectionGroup} ${isGroupActive ? styles.sectionGroupActive : ""}`}
            ref={(el) => {
              if (el) sectionRefs.current.set(group.title, el);
            }}
          >
            <NextLink
              href={getFirstVisibleRoute(group)}
              className={`${styles.sectionHeader} ${isGroupActive ? styles.sectionHeaderActive : ""} ${isHighlighted && !isGroupActive ? styles.sectionHeaderHighlighted : ""}`}
              onClick={onNavigate}
            >
              <span className={styles.sectionIcon}>{group.icon}</span>
              <span className={styles.sectionTitle}>{group.title}</span>
            </NextLink>
            <ul className={styles.subPageList}>
              {visibleChildren.map((child) => (
                <li key={child.path} className={styles.subPageItem}>
                  <NextLink
                    href={child.path}
                    className={`${styles.subPageLink} ${isGroupActive ? styles.subPageLinkInActiveGroup : ""} ${isActivePage(child) ? styles.subPageLinkActive : ""}`}
                    onClick={onNavigate}
                  >
                    <span>{child.title}</span>
                    {isActivePage(child) && (
                      <span className={styles.activeDot} />
                    )}
                  </NextLink>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
};

export default ExpandedNav;

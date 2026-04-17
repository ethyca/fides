import { AutoComplete, Icons, Input, InputRef } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

import { NavGroup } from "./nav-config";
import styles from "./NavSearch.module.scss";
import NavSearchModal from "./NavSearchModal";
import useNavSearchItems, {
  filterAndRankNavItems,
  FlatNavItem,
} from "./useNavSearchItems";

const isMac =
  typeof navigator !== "undefined" &&
  /Mac|iPod|iPhone|iPad/.test(navigator.userAgent);

const SHORTCUT_LABEL = isMac ? "⌘K" : "Ctrl+K";

const SEARCH_ICON_STYLE = {
  color: palette.FIDESUI_NEUTRAL_400,
  fontSize: 14,
};
const DEBOUNCE_MS = 200;

/** Create a unique key for an item to avoid collisions when multiple items share the same path. */
const itemKey = (item: FlatNavItem): string =>
  item.parentTitle ? `${item.path}::${item.title}` : item.path;

const NavSearchExpanded = ({ groups }: { groups: NavGroup[] }) => {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const inputRef = useRef<InputRef>(null);
  const justSelectedRef = useRef(false);

  // Debounce the search value for server-side queries (systems, integrations)
  const [debouncedQuery, setDebouncedQuery] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchValue), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchValue]);

  const flatItems: FlatNavItem[] = useNavSearchItems(groups, debouncedQuery);

  const filteredOptions = useMemo(() => {
    const query = searchValue.trim();
    // When no query, only show top-level pages (not tabs/dynamic items).
    // Sub-items only appear when the search text matches them.
    const items = query
      ? filterAndRankNavItems(flatItems, query)
      : flatItems.filter((item) => !item.parentTitle);

    // Group by nav group
    const grouped = items.reduce<Map<string, FlatNavItem[]>>((acc, item) => {
      const existing = acc.get(item.groupTitle) ?? [];
      acc.set(item.groupTitle, [...existing, item]);
      return acc;
    }, new Map());

    return Array.from(grouped.entries()).map(([groupTitle, groupItems]) => ({
      label: <span className={styles.groupLabel}>{groupTitle}</span>,
      options: groupItems.map((item) => ({
        value: itemKey(item),
        label: item.parentTitle ? (
          <div className={styles.optionTwoLine}>
            <span className={styles.optionLabel}>{item.title}</span>
            <span className={styles.optionParent}>{item.parentTitle}</span>
          </div>
        ) : (
          <span className={styles.optionLabel}>{item.title}</span>
        ),
      })),
    }));
  }, [flatItems, searchValue]);

  // Build a lookup from unique key back to path for navigation
  const keyToPath = useMemo(
    () => new Map(flatItems.map((item) => [itemKey(item), item.path])),
    [flatItems],
  );

  const handleSelect = useCallback(
    (key: string) => {
      const path = keyToPath.get(key) ?? key;
      justSelectedRef.current = true;
      router.push(path);
      setOpen(false);
      setSearchValue("");
      inputRef.current?.blur();
      // Reset the guard after the event loop settles
      setTimeout(() => {
        justSelectedRef.current = false;
      }, 0);
    },
    [router, keyToPath],
  );

  const handleOpenChange = useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setSearchValue("");
    }
  }, []);

  // Cmd+K on Mac, Ctrl+K elsewhere
  useHotkeys(
    isMac ? "meta+k" : "ctrl+k",
    () => {
      setOpen(true);
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    },
    { enableOnFormTags: true, preventDefault: true },
  );

  const handleEscapeKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      setSearchValue("");
      inputRef.current?.blur();
    }
  }, []);

  return (
    <div className="px-2 pb-3">
      <AutoComplete
        open={open}
        options={filteredOptions}
        onSelect={handleSelect}
        onOpenChange={handleOpenChange}
        defaultActiveFirstOption
        className={styles.expandedAutoComplete}
        classNames={{ popup: { root: styles.searchDropdown } }}
        value={searchValue}
        onSearch={setSearchValue}
      >
        <Input
          ref={inputRef}
          className={styles.expandedInput}
          placeholder="Search pages..."
          aria-label="Search pages"
          prefix={<Icons.Search style={SEARCH_ICON_STYLE} />}
          suffix={
            <span className={styles.shortcutHint} aria-hidden="true">
              {SHORTCUT_LABEL}
            </span>
          }
          allowClear
          onFocus={() => {
            if (!justSelectedRef.current) {
              setOpen(true);
            }
          }}
          onKeyDown={handleEscapeKey}
          data-testid="nav-search-input"
        />
      </AutoComplete>
    </div>
  );
};

interface NavSearchProps {
  groups: NavGroup[];
  collapsed?: boolean;
}

const NavSearch = ({ groups, collapsed = false }: NavSearchProps) => {
  if (collapsed) {
    return <NavSearchModal groups={groups} />;
  }

  return <NavSearchExpanded groups={groups} />;
};

export default NavSearch;

import { AutoComplete, Icons, Input, InputRef, Modal } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { NavGroup } from "./nav-config";
import styles from "./NavSearch.module.scss";
import useNavSearchItems, { FlatNavItem } from "./useNavSearchItems";

const isMac =
  typeof navigator !== "undefined" &&
  /Mac|iPod|iPhone|iPad/.test(navigator.userAgent);

const SHORTCUT_LABEL = isMac ? "⌘K" : "Ctrl+K";

const SEARCH_ICON_STYLE_SM = {
  color: palette.FIDESUI_NEUTRAL_400,
  fontSize: 14,
};
const SEARCH_ICON_STYLE_LG = {
  color: palette.FIDESUI_NEUTRAL_400,
  fontSize: 16,
};
const COLLAPSED_ICON_STYLE = {
  fontSize: 16,
  color: palette.FIDESUI_CORINTH,
};
const MODAL_POSITION = { top: "calc(33vh - 24px)" };
const DEBOUNCE_MS = 200;

/** Create a unique key for an item to avoid collisions when multiple items share the same path. */
const itemKey = (item: FlatNavItem): string =>
  item.parentTitle ? `${item.path}::${item.title}` : item.path;

interface NavSearchProps {
  groups: NavGroup[];
  collapsed?: boolean;
}

const NavSearch = ({ groups, collapsed = false }: NavSearchProps) => {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const inputRef = useRef<InputRef>(null);
  const modalInputRef = useRef<InputRef>(null);
  const justSelectedRef = useRef(false);

  // Debounce the search value for server-side queries (systems, integrations)
  const [debouncedQuery, setDebouncedQuery] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchValue), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchValue]);

  const flatItems: FlatNavItem[] = useNavSearchItems(groups, debouncedQuery);

  const filteredOptions = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    // When no query, only show top-level pages (not tabs/dynamic items).
    // Sub-items only appear when the search text matches them.
    const items = query
      ? flatItems.filter((item) => item.title.toLowerCase().includes(query))
      : flatItems.filter((item) => !item.parentTitle);

    // Group by nav group
    const grouped = new Map<string, FlatNavItem[]>();
    items.forEach((item) => {
      const list = grouped.get(item.groupTitle) ?? [];
      list.push(item);
      grouped.set(item.groupTitle, list);
    });

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
  const keyToPath = useMemo(() => {
    const map = new Map<string, string>();
    flatItems.forEach((item) => {
      map.set(itemKey(item), item.path);
    });
    return map;
  }, [flatItems]);

  const handleSelect = useCallback(
    (key: string) => {
      const path = keyToPath.get(key) ?? key;
      justSelectedRef.current = true;
      router.push(path);
      setOpen(false);
      setSearchValue("");
      inputRef.current?.blur();
      modalInputRef.current?.blur();
      // Reset the guard after the event loop settles
      setTimeout(() => {
        justSelectedRef.current = false;
      }, 0);
    },
    [router, keyToPath],
  );

  const handleClose = useCallback(() => {
    setOpen(false);
    setSearchValue("");
  }, []);

  const handleOpenChange = useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setSearchValue("");
    }
  }, []);

  // Cmd+K / Ctrl+K global shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        // In expanded mode, focus immediately; in collapsed mode,
        // the Modal's afterOpenChange callback handles focus.
        if (!collapsed) {
          requestAnimationFrame(() => {
            inputRef.current?.focus();
          });
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [collapsed]);

  // Focus input when opened in expanded mode
  useEffect(() => {
    if (open && !collapsed) {
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    }
  }, [open, collapsed]);

  const handleEscapeKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      setSearchValue("");
      inputRef.current?.blur();
      modalInputRef.current?.blur();
    }
  }, []);

  // Keyboard navigation for inline results in the modal
  const [activeIndex, setActiveIndex] = useState(-1);

  const visibleItems = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    return query
      ? flatItems.filter((item) => item.title.toLowerCase().includes(query))
      : [];
  }, [flatItems, searchValue]);

  // Reset active index when results change
  useEffect(() => {
    setActiveIndex(visibleItems.length > 0 ? 0 : -1);
  }, [visibleItems]);

  const handleModalKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        handleClose();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((prev) =>
          prev < visibleItems.length - 1 ? prev + 1 : 0,
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((prev) =>
          prev > 0 ? prev - 1 : visibleItems.length - 1,
        );
      } else if (
        e.key === "Enter" &&
        activeIndex >= 0 &&
        visibleItems[activeIndex]
      ) {
        e.preventDefault();
        handleSelect(visibleItems[activeIndex].path);
      }
    },
    [visibleItems, activeIndex, handleSelect, handleClose],
  );

  // Pre-compute flat indexed items for the modal to avoid mutable counter in render
  const indexedModalItems = useMemo(() => {
    const grouped = new Map<string, FlatNavItem[]>();
    visibleItems.forEach((item) => {
      const list = grouped.get(item.groupTitle) ?? [];
      list.push(item);
      grouped.set(item.groupTitle, list);
    });

    let idx = 0;
    return Array.from(grouped.entries()).map(([groupTitle, items]) => ({
      groupTitle,
      items: items.map((item) => {
        const currentIdx = idx;
        idx += 1;
        return { ...item, idx: currentIdx };
      }),
    }));
  }, [visibleItems]);

  if (collapsed) {
    return (
      <div className={styles.collapsedWrapper}>
        <button
          type="button"
          className={styles.collapsedButton}
          onClick={() => setOpen(true)}
          aria-label="Search navigation"
          data-testid="nav-search-toggle"
        >
          <Icons.Search style={COLLAPSED_ICON_STYLE} />
        </button>
        <Modal
          open={open}
          onCancel={handleClose}
          footer={null}
          closable={false}
          width={480}
          style={MODAL_POSITION}
          className={styles.searchModal}
          destroyOnClose
          afterOpenChange={(isOpen) => {
            if (isOpen) {
              modalInputRef.current?.focus();
            }
          }}
        >
          <Input
            ref={modalInputRef}
            autoFocus
            className={styles.modalInput}
            placeholder="Search pages..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            prefix={<Icons.Search style={SEARCH_ICON_STYLE_LG} />}
            allowClear
            onKeyDown={handleModalKeyDown}
            role="combobox"
            aria-label="Search pages"
            aria-expanded={indexedModalItems.length > 0}
            aria-controls={
              indexedModalItems.length > 0
                ? "nav-search-results-list"
                : undefined
            }
            aria-activedescendant={
              activeIndex >= 0 ? `nav-search-result-${activeIndex}` : undefined
            }
            data-testid="nav-search-modal-input"
          />
          <div className="sr-only" aria-live="polite" aria-atomic="true">
            {visibleItems.length > 0 &&
              `${visibleItems.length} result${visibleItems.length === 1 ? "" : "s"} available`}
            {visibleItems.length === 0 &&
              searchValue.trim() &&
              "No results found"}
          </div>
          {indexedModalItems.length > 0 && (
            <ul
              className={styles.resultsList}
              id="nav-search-results-list"
              role="listbox"
              data-testid="nav-search-results"
            >
              {indexedModalItems.map(({ groupTitle, items }) => (
                <li
                  key={groupTitle}
                  role="group"
                  aria-label={groupTitle}
                  className={styles.resultsGroup}
                >
                  <span className={styles.resultsGroupLabel} aria-hidden="true">
                    {groupTitle}
                  </span>
                  {items.map((item) => (
                    <button
                      key={itemKey(item)}
                      id={`nav-search-result-${item.idx}`}
                      type="button"
                      role="option"
                      aria-selected={item.idx === activeIndex}
                      className={`${styles.resultItem} ${item.idx === activeIndex ? styles.resultItemActive : ""}`}
                      onClick={() => handleSelect(item.path)}
                      onMouseEnter={() => setActiveIndex(item.idx)}
                      data-testid={`result-${item.path}`}
                    >
                      <span>{item.title}</span>
                      {item.parentTitle && (
                        <span className={styles.resultItemParent}>
                          {item.parentTitle}
                        </span>
                      )}
                    </button>
                  ))}
                </li>
              ))}
            </ul>
          )}
        </Modal>
      </div>
    );
  }

  return (
    <div className={styles.expandedWrapper}>
      <AutoComplete
        open={open}
        options={filteredOptions}
        onSelect={handleSelect}
        onOpenChange={handleOpenChange}
        defaultActiveFirstOption
        className={styles.expandedAutoComplete}
        popupClassName={styles.searchDropdown}
        value={searchValue}
        onSearch={setSearchValue}
      >
        <Input
          ref={inputRef}
          className={styles.expandedInput}
          placeholder="Search pages..."
          aria-label="Search pages"
          prefix={<Icons.Search style={SEARCH_ICON_STYLE_SM} />}
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

export default NavSearch;

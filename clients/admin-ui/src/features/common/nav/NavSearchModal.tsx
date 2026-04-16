import { Icons, Input, InputRef, Modal } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

import { pluralize } from "~/features/common/utils";

import { NavGroup } from "./nav-config";
import styles from "./NavSearch.module.scss";
import { RouterLink } from "./RouterLink";
import useNavSearchItems, { FlatNavItem } from "./useNavSearchItems";

const SEARCH_ICON_STYLE = {
  color: palette.FIDESUI_NEUTRAL_400,
  fontSize: 16,
};
const COLLAPSED_ICON_STYLE = {
  fontSize: 16,
  color: palette.FIDESUI_CORINTH,
};
const isMac =
  typeof navigator !== "undefined" &&
  /Mac|iPod|iPhone|iPad/.test(navigator.userAgent);

const DEBOUNCE_MS = 200;

/** Unique key for a nav item, handling duplicate paths via title suffix. */
const itemKey = (item: FlatNavItem): string =>
  item.parentTitle ? `${item.path}::${item.title}` : item.path;

/** Group items by groupTitle, preserving insertion order. */
const groupByTitle = (items: FlatNavItem[]) =>
  items.reduce<Map<string, FlatNavItem[]>>((acc, item) => {
    const existing = acc.get(item.groupTitle) ?? [];
    acc.set(item.groupTitle, [...existing, item]);
    return acc;
  }, new Map());

interface NavSearchResultItemProps {
  item: FlatNavItem & { idx: number };
  isActive: boolean;
  onClose: () => void;
  onMouseEnter: () => void;
}

const NavSearchResultItem = ({
  item,
  isActive,
  onClose,
  onMouseEnter,
}: NavSearchResultItemProps) => (
  <RouterLink
    unstyled
    href={item.path}
    id={`nav-search-result-${item.idx}`}
    role="option"
    aria-selected={isActive}
    className={`${styles.resultItem} ${isActive ? styles.resultItemActive : ""}`}
    onClick={onClose}
    onMouseEnter={onMouseEnter}
    data-testid={`result-${item.path}`}
  >
    <span>{item.title}</span>
    {item.parentTitle && (
      <span className={styles.resultItemParent}>{item.parentTitle}</span>
    )}
  </RouterLink>
);

interface NavSearchModalProps {
  groups: NavGroup[];
}

const NavSearchModal = ({ groups }: NavSearchModalProps) => {
  const [open, setOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const modalInputRef = useRef<InputRef>(null);

  const [debouncedQuery, setDebouncedQuery] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchValue), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchValue]);

  const flatItems = useNavSearchItems(groups, debouncedQuery);

  const handleClose = useCallback(() => {
    setOpen(false);
    setSearchValue("");
  }, []);

  // Cmd+K on Mac, Ctrl+K elsewhere
  useHotkeys(isMac ? "meta+k" : "ctrl+k", () => setOpen(true), {
    enableOnFormTags: true,
    preventDefault: true,
  });

  // Keyboard navigation
  const [activeIndex, setActiveIndex] = useState(-1);

  const visibleItems = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    return query
      ? flatItems.filter((item) => item.title.toLowerCase().includes(query))
      : [];
  }, [flatItems, searchValue]);

  useEffect(() => {
    setActiveIndex(visibleItems.length > 0 ? 0 : -1);
  }, [visibleItems]);

  const handleKeyDown = useCallback(
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
        // Delegate to the active link element so NextLink handles navigation
        document.getElementById(`nav-search-result-${activeIndex}`)?.click();
      }
    },
    [visibleItems, activeIndex, handleClose],
  );

  const indexedGroups = useMemo(() => {
    const grouped = groupByTitle(visibleItems);
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

  const hasResults = indexedGroups.length > 0;

  return (
    <div className="flex flex-col items-center pb-3">
      <button
        type="button"
        className="flex size-9 cursor-pointer items-center justify-center rounded-md border-none bg-transparent transition-colors hover:bg-[var(--fidesui-neutral-700)]"
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
        style={{ top: "calc(33vh - 24px)" }}
        className={styles.searchModal}
        destroyOnHidden
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
          prefix={<Icons.Search style={SEARCH_ICON_STYLE} />}
          allowClear
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-label="Search pages"
          aria-expanded={hasResults}
          aria-controls="nav-search-results-list"
          aria-activedescendant={
            activeIndex >= 0 ? `nav-search-result-${activeIndex}` : undefined
          }
          data-testid="nav-search-modal-input"
        />
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {visibleItems.length > 0 &&
            `${visibleItems.length} ${pluralize(visibleItems.length, "result", "results")} available`}
          {visibleItems.length === 0 &&
            searchValue.trim() &&
            "No results found"}
        </div>
        {hasResults && (
          <ul
            className={styles.resultsList}
            id="nav-search-results-list"
            role="listbox"
            data-testid="nav-search-results"
          >
            {indexedGroups.map(({ groupTitle, items }) => (
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
                  <NavSearchResultItem
                    key={itemKey(item)}
                    item={item}
                    isActive={item.idx === activeIndex}
                    onClose={handleClose}
                    onMouseEnter={() => setActiveIndex(item.idx)}
                  />
                ))}
              </li>
            ))}
          </ul>
        )}
      </Modal>
    </div>
  );
};

export default NavSearchModal;

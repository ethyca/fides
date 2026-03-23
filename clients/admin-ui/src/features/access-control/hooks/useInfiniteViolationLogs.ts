import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useGetViolationLogsQuery } from "../access-control.slice";
import type { PolicyViolationLog } from "../types";
import type { RequestLogFilters } from "./useRequestLogFilters";

const HIGHLIGHT_DURATION_MS = 1500;
const LIVE_TAIL_POLL_MS = 5000;
const PAGE_SIZE = 25;

interface UseInfiniteViolationLogsOptions {
  filters: RequestLogFilters;
  liveTail: boolean;
}

export const useInfiniteViolationLogs = ({
  filters,
  liveTail,
}: UseInfiniteViolationLogsOptions) => {
  const [cursor, setCursor] = useState<string | null>(null);
  const [allItems, setAllItems] = useState<PolicyViolationLog[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());
  const knownIdsRef = useRef<Set<string>>(new Set());

  const queryParams = useMemo(
    () => ({
      ...(cursor ? { cursor } : {}),
      size: PAGE_SIZE,
      ...filters,
    }),
    [cursor, filters],
  );

  const { data, isFetching } = useGetViolationLogsQuery(queryParams, {
    pollingInterval: liveTail ? LIVE_TAIL_POLL_MS : 0,
  });

  // Accumulate fetched pages into allItems
  useEffect(() => {
    if (!data) {
      return;
    }

    const newItems = data.items;

    if (!cursor) {
      // First page or filter reset — detect new items for live-tail highlighting
      const newIds = new Set<string>();
      newItems.forEach((item) => {
        if (!knownIdsRef.current.has(item.id)) {
          newIds.add(item.id);
        }
      });

      // Update known IDs
      knownIdsRef.current = new Set(newItems.map((item) => item.id));
      setAllItems(newItems);

      // Highlight new items during live tail
      if (newIds.size > 0 && liveTail) {
        setHighlightedIds(newIds);
        setTimeout(() => setHighlightedIds(new Set()), HIGHLIGHT_DURATION_MS);
      }
    } else {
      // Subsequent page — append and deduplicate
      setAllItems((prev) => {
        const existingIds = new Set(prev.map((item) => item.id));
        const deduped = newItems.filter((item) => !existingIds.has(item.id));
        const merged = [...prev, ...deduped];
        knownIdsRef.current = new Set(merged.map((item) => item.id));
        return merged;
      });
    }

    setHasMore(!!data.next_cursor);
  }, [data, cursor, liveTail]);

  // Reset when filters change
  useEffect(() => {
    setCursor(null);
    setAllItems([]);
    setHasMore(true);
    knownIdsRef.current = new Set();
  }, [filters]);

  const loadMore = useCallback(() => {
    if (!isFetching && hasMore && data?.next_cursor) {
      setCursor(data.next_cursor);
    }
  }, [isFetching, hasMore, data?.next_cursor]);

  return {
    items: allItems,
    isFetching,
    hasMore,
    highlightedIds,
    loadMore,
  };
};

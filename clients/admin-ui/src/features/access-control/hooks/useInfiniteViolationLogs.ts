import { useCallback, useEffect, useMemo, useState } from "react";

import { useGetViolationLogsQuery } from "../access-control.slice";
import type { PolicyViolationLog } from "../types";
import type { RequestLogFilters } from "./useRequestLogFilters";

const PAGE_SIZE = 25;

interface UseInfiniteViolationLogsOptions {
  filters: RequestLogFilters;
}

export const useInfiniteViolationLogs = ({
  filters,
}: UseInfiniteViolationLogsOptions) => {
  const [cursor, setCursor] = useState<string | null>(null);
  const [allItems, setAllItems] = useState<PolicyViolationLog[]>([]);
  const [hasMore, setHasMore] = useState(true);

  const queryParams = useMemo(
    () => ({
      ...(cursor ? { cursor } : {}),
      size: PAGE_SIZE,
      ...filters,
    }),
    [cursor, filters],
  );

  const { data, isFetching } = useGetViolationLogsQuery(queryParams);

  // Accumulate fetched pages into allItems
  useEffect(() => {
    if (!data) {
      return;
    }

    const newItems = data.items;

    if (!cursor) {
      setAllItems(newItems);
    } else {
      // Subsequent page — append and deduplicate
      setAllItems((prev) => {
        const existingIds = new Set(prev.map((item) => item.id));
        const deduped = newItems.filter((item) => !existingIds.has(item.id));
        return [...prev, ...deduped];
      });
    }

    setHasMore(!!data.next_cursor);
  }, [data, cursor]);

  // Reset when filters change
  useEffect(() => {
    setCursor(null);
    setAllItems([]);
    setHasMore(true);
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
    loadMore,
  };
};

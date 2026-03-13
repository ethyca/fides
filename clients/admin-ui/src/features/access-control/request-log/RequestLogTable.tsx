import { Flex, Spin, Table } from "fidesui";
import { useCallback, useEffect, useRef, useState, useMemo } from "react";

import { useGetPolicyViolationLogsQuery } from "../access-control.slice";
import type { PolicyViolationLog } from "../types";
import { getRequestLogColumns } from "./requestLogColumns";

const columns = getRequestLogColumns();

interface RequestLogTableProps {
  filters: Record<string, string | undefined>;
  onRowClick?: (record: PolicyViolationLog) => void;
}

const PAGE_SIZE = 25;

export const RequestLogTable = ({
  filters,
  onRowClick,
}: RequestLogTableProps) => {
  const [page, setPage] = useState(1);
  const [allItems, setAllItems] = useState<PolicyViolationLog[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const queryParams = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      ...filters,
    }),
    [page, filters],
  );

  const { data, isFetching } = useGetPolicyViolationLogsQuery(queryParams);

  useEffect(() => {
    setPage(1);
    setAllItems([]);
    setHasMore(true);
  }, [filters]);

  useEffect(() => {
    if (!data) {
      return;
    }

    if (page === 1) {
      setAllItems(data.items);
    } else {
      setAllItems((prev) => {
        const existingKeys = new Set(
          prev.map((item) => item.timestamp + item.consumer),
        );
        const newItems = data.items.filter(
          (item) => !existingKeys.has(item.timestamp + item.consumer),
        );
        return [...prev, ...newItems];
      });
    }
    setHasMore(page < data.pages);
  }, [data, page]);

  const loadMore = useCallback(() => {
    if (!isFetching && hasMore) {
      setPage((prev) => prev + 1);
    }
  }, [isFetching, hasMore]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  return (
    <div className="sticky top-0 z-10 flex max-h-[calc(100vh-48px)] flex-col overflow-auto">
      <Table
        dataSource={allItems}
        columns={columns}
        pagination={false}
        bordered={false}
        rowKey={(record) =>
          `${record.timestamp}-${record.consumer}-${record.dataset}`
        }
        onRow={(record) => ({
          onClick: () => onRowClick?.(record),
          style: { cursor: onRowClick ? "pointer" : undefined },
        })}
        size="small"
        sticky
      />
      <div ref={sentinelRef} className="h-px shrink-0" />
      {isFetching && (
        <Flex justify="center" className="py-4">
          <Spin size="small" />
        </Flex>
      )}
    </div>
  );
};

import { Flex, Spin, Table } from "fidesui";
import { useEffect, useRef } from "react";

import { useInfiniteViolationLogs } from "./hooks/useInfiniteViolationLogs";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { getRequestLogColumns } from "./requestLogColumns";
import type { PolicyViolationLog } from "./types";

const columns = getRequestLogColumns();

const getRowKey = (record: PolicyViolationLog) => record.id;

interface RequestLogTableProps {
  onRowClick?: (record: PolicyViolationLog) => void;
}

export const RequestLogTable = ({ onRowClick }: RequestLogTableProps) => {
  const { filters, liveTail } = useRequestLogFilterContext();
  const { items, isFetching, hasMore, loadMore } = useInfiniteViolationLogs({
    filters,
    liveTail,
  });

  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && items.length > 0) {
          loadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore, items.length]);

  return (
    <Flex vertical className="max-h-[calc(100vh-48px)] overflow-auto">
      <Table
        dataSource={items}
        columns={columns}
        pagination={false}
        bordered={false}
        rowKey={getRowKey}
        onRow={(record) => ({
          onClick: () => onRowClick?.(record),
          className: onRowClick ? "cursor-pointer" : undefined,
        })}
        size="small"
        sticky
      />
      {hasMore && <div ref={sentinelRef} className="h-px shrink-0" />}
      {isFetching && (
        <Flex justify="center" className="py-4">
          <Spin size="small" />
        </Flex>
      )}
    </Flex>
  );
};

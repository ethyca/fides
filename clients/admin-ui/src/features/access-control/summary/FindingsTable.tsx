import { Table, Typography } from "fidesui";
import { useCallback, useMemo } from "react";

import { useGetPolicyViolationsQuery } from "~/features/access-control/access-control.slice";
import type { PolicyViolationAggregate } from "~/features/access-control/types";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";

import { getViolationsColumns } from "./violationsColumns";

interface FindingsTableProps {
  onRowClick?: (record: PolicyViolationAggregate) => void;
  startDate?: string;
  endDate?: string;
}

export const FindingsTable = ({
  onRowClick,
  startDate,
  endDate,
}: FindingsTableProps) => {
  const { pageIndex, pageSize } = useAntPagination({
    pageQueryKey: "findings_page",
    sizeQueryKey: "findings_size",
  });

  const { data, isLoading } = useGetPolicyViolationsQuery({
    page: pageIndex,
    size: pageSize,
    ...(startDate ? { start_date: startDate } : {}),
    ...(endDate ? { end_date: endDate } : {}),
  });

  const columns = useMemo(() => getViolationsColumns(), []);

  const handleRowClick = useCallback(
    (record: PolicyViolationAggregate) => {
      onRowClick?.(record);
    },
    [onRowClick],
  );

  return (
    // <div className="mt-6">
    <Table
      columns={columns}
      dataSource={data?.items}
      loading={isLoading}
      rowKey={(record) => `${record.policy}-${record.control}`}
      size="small"
      bordered={false}
      onRow={(record) => ({
        className: onRowClick ? "cursor-pointer" : undefined,
        onClick: onRowClick ? () => handleRowClick(record) : undefined,
      })}
    />
    // </div>
  );
};

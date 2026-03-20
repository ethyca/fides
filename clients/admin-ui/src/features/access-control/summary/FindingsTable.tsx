import { Flex, Pagination, Table, Typography } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import { useGetPolicyViolationsQuery } from "~/features/access-control/access-control.slice";
import type { PolicyViolationAggregate } from "~/features/access-control/types";
import { ACCESS_CONTROL_REQUEST_LOG_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";

import { getViolationsColumns } from "./violationsColumns";

export const FindingsTable = () => {
  const router = useRouter();
  const { paginationProps, pageIndex, pageSize } = useAntPagination({
    pageQueryKey: "findings_page",
    sizeQueryKey: "findings_size",
  });

  const { data, isLoading } = useGetPolicyViolationsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const columns = useMemo(() => getViolationsColumns(), []);

  const handleRowClick = useCallback(
    (record: PolicyViolationAggregate) => {
      router.push({
        pathname: ACCESS_CONTROL_REQUEST_LOG_ROUTE,
        query: { policy: record.policy, control: record.control },
      });
    },
    [router],
  );

  return (
    <div className="mt-6">
      <Typography.Title level={5} className="!mb-4 !mt-0">
        Findings
      </Typography.Title>
      <Table
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        rowKey={(record) => `${record.policy}-${record.control}`}
        size="small"
        bordered={false}
        onRow={(record) => ({
          className: "cursor-pointer",
          onClick: () => handleRowClick(record),
        })}
      />
    </div>
  );
};

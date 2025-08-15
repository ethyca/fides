import { Box } from "fidesui";
import type { NextPage } from "next";
import React, { useEffect, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetSystemsQuery } from "~/features/system";
import { DEFAULT_SYSTEMS_WITH_GROUPS } from "~/mocks/TEMP-system-groups/endpoints/systems-with-groups-response";
import NewTable from "~/pages/systems/new-table";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const Systems: NextPage = () => {
  const { pageSize, pageIndex, setTotalPages } = useServerSidePagination();

  const [globalFilter, setGlobalFilter] = useState<string>();
  const systemsResponse = DEFAULT_SYSTEMS_WITH_GROUPS;

  const {
    // data: systemsResponse,
    isLoading,
  } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
  });

  // const { data: systemsResponse, isLoading } = usMockGetSystemsWithGroupsQuery({
  //   page: pageIndex,
  //   size: pageSize,
  //   search: globalFilter,
  //   groupFilters: [],
  // });

  const { items: data, pages: totalPages } = useMemo(
    () => systemsResponse ?? EMPTY_RESPONSE,
    [systemsResponse],
  );

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  return (
    <Layout title="System inventory">
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        />
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={15} />
        ) : (
          <NewTable data={data} loading={isLoading} />
        )}
      </Box>
    </Layout>
  );
};

export default Systems;

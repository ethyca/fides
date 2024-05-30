/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Spinner, Text } from "fidesui";
import { useEffect, useMemo } from "react";

import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { EnableCell } from "~/features/common/table/v2/cells";
import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { ConnectionConfigurationResponse, MonitorConfig } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [] as MonitorConfig[],
  total: 0,
  page: 1,
  size: 50,
  pages: 0,
};

const columnHelper = createColumnHelper<MonitorConfig>();

const MonitorConfigTab = ({
  integration,
}: {
  integration: ConnectionConfigurationResponse;
}) => {
  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const {
    isLoading,
    isFetching,
    data: monitorResult,
  } = useGetMonitorsByIntegrationQuery({
    page: pageIndex,
    size: pageSize,
    connection_config_key: integration.key,
  });

  const response = monitorResult ?? EMPTY_RESPONSE;

  const {
    items: monitors,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => response, [response]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<MonitorConfig, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.databases, {
        id: "projects",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Location" {...props} />,
      }),
      // insert "last monitored" row
      // insert "data steward" row
      columnHelper.display({
        id: "toggle",
        cell: () => (
          <EnableCell
            value
            onToggle={() => console.log("toggled!")}
            title="title"
            message="message"
          />
        ),
        header: "Status",
      }),
      columnHelper.display({
        id: "action",
        cell: () => <DefaultCell value="actions here" />,
        header: "Actions",
      }),
    ],
    []
  );

  const tableInstance = useReactTable<MonitorConfig>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.name,
    manualPagination: true,
    data: monitors,
    columns,
  });

  if (isLoading) {
    return <Spinner />;
  }

  return (
    <>
      <Text maxW="720px" mb={6}>
        Data discovery monitors observe configured systems for data model
        changes to proactively discovery and classify data risks. You can create
        multiple monitors to observe part or all of a project, dataset, table or
        API for changes and assign these to different data stewards. Read the
        Data discovery monitor guide now.
      </Text>
      <FidesTableV2 tableInstance={tableInstance} />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};

export default MonitorConfigTab;

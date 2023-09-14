import { Box, HStack, Table } from "@fidesui/react";
import { useMemo } from "react";
import {
  Column,
  useFlexLayout,
  useGlobalFilter,
  useGroupBy,
  useResizeColumns,
  useTable,
} from "react-table";

import { useAppSelector } from "~/app/hooks";
import { PaddedCell } from "~/features/common/table";
import GroupedTableBody from "~/features/common/table/grouped/GroupedTableBody";
import GroupedTableHeader from "~/features/common/table/grouped/GroupedTableHeader";
import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";
import { selectAllSystems } from "~/features/system";

import AddButtons from "./AddButtons";
import { DataUseCell } from "./cells";
import { CookieBySystem, transformSystemsToCookies } from "./vendor-transform";

const VendorCookieTable = () => {
  const systems = useAppSelector(selectAllSystems);
  const cookiesBySystem = useMemo(
    () => transformSystemsToCookies(systems),
    [systems]
  );

  const columns: Column<CookieBySystem>[] = useMemo(
    () => [
      {
        Header: "Vendor",
        accessor: "name",
        Cell: PaddedCell,
        aggregate: (names) => names[0],
      },
      {
        Header: "Id",
        accessor: "id",
      },
      {
        Header: "Cookie name",
        accessor: (d) => (d.cookie ? d.cookie.name : "N/A"),
        Cell: PaddedCell,
      },
      {
        Header: "Data use",
        accessor: (d) => d.dataUse ?? "N/A",
        Cell: DataUseCell,
      },
    ],
    []
  );

  const tableInstance = useTable(
    {
      columns,
      data: cookiesBySystem,
      initialState: {
        groupBy: ["id"],
        hiddenColumns: ["id"],
      },
    },
    useGlobalFilter,
    useGroupBy,
    useFlexLayout,
    useResizeColumns
  );
  const { getTableProps, getTableBodyProps, headerGroups, prepareRow, rows } =
    tableInstance;

  return (
    <Box boxSize="100%" overflow="auto">
      <HStack mt={2} mb={4} justifyContent="space-between">
        <GlobalFilter
          globalFilter={tableInstance.state.globalFilter}
          setGlobalFilter={tableInstance.setGlobalFilter}
          placeholder="Search"
        />
        <AddButtons includeCookies />
      </HStack>
      <Table {...getTableProps()} size="sm" data-testid="datamap-table">
        <GroupedTableHeader<CookieBySystem> headerGroups={headerGroups} />
        <GroupedTableBody<CookieBySystem>
          rows={rows}
          renderRowSubheading={(row) => row.values.name}
          prepareRow={prepareRow}
          getTableBodyProps={getTableBodyProps}
        />
      </Table>
    </Box>
  );
};

export default VendorCookieTable;

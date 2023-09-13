import {
  Box,
  HStack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
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
import {
  GRAY_BACKGROUND,
  HeaderSpacer,
  PaddedCell,
} from "~/features/common/table";
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
        aggregate: (uses) => uses.join(", "),
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
        <Thead
          position="sticky"
          top="0px"
          height="36px"
          zIndex={10}
          backgroundColor={GRAY_BACKGROUND}
        >
          {headerGroups.map((headerGroup) => {
            const { key, ...headerProps } = headerGroup.getHeaderGroupProps();
            return (
              <Tr key={key} {...headerProps} height="inherit">
                <HeaderSpacer />
                {headerGroup.headers.map((column, index) => {
                  const { key: columnKey, ...columnHeaderProps } =
                    column.getHeaderProps();
                  return (
                    <Th
                      key={columnKey}
                      {...columnHeaderProps}
                      title={`${column.Header}`}
                      textTransform="none"
                      px={2}
                      display="flex"
                      alignItems="center"
                      borderLeftWidth={index === 0 ? "1px" : ""}
                      borderRightWidth="1px"
                      borderColor="gray.200"
                    >
                      <Text
                        whiteSpace="nowrap"
                        textOverflow="ellipsis"
                        overflow="hidden"
                        mr={1}
                      >
                        {column.render("Header")}
                      </Text>
                      {column.canResize && (
                        <Box
                          {...column.getResizerProps()}
                          position="absolute"
                          top={0}
                          right={0}
                          width={2}
                          height="100%"
                          css={{
                            touchAction: ":none",
                          }}
                        />
                      )}
                    </Th>
                  );
                })}
                <HeaderSpacer />
              </Tr>
            );
          })}
        </Thead>
        <Tbody backgroundColor={GRAY_BACKGROUND} {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);

            const groupHeader = (
              <Tr
                {...row.getRowProps()}
                borderTopLeftRadius="6px"
                borderTopRightRadius="6px"
                height="70px"
                backgroundColor="gray.50"
                borderWidth="1px"
                borderBottom="none"
                mt={4}
                ml={4}
                mr={4}
                key={row.groupByVal}
              >
                <Td
                  colSpan={row.cells.length}
                  {...row.cells[0].getCellProps()}
                  width="auto"
                  paddingX={2}
                >
                  <Text
                    fontSize="sm"
                    lineHeight={5}
                    fontWeight="bold"
                    color="gray.600"
                  >
                    {row.values.name}
                  </Text>
                </Td>
              </Tr>
            );

            const groupedRows = row.subRows.map((subRow, index) => {
              prepareRow(subRow);
              const { key, ...rowProps } = subRow.getRowProps();
              return (
                <Tr
                  key={key}
                  minHeight={9}
                  paddingX={2}
                  borderWidth="1px"
                  borderColor="gray.200"
                  borderTop="none"
                  borderBottomLeftRadius={
                    index === row.subRows.length - 1 ? "6px" : ""
                  }
                  borderBottomRightRadius={
                    index === row.subRows.length - 1 ? "6px" : ""
                  }
                  {...rowProps}
                  backgroundColor="white"
                  ml={4}
                  mr={4}
                >
                  {subRow.cells.map((cell, cellIndex) => {
                    const { key: cellKey, ...cellProps } = cell.getCellProps();
                    return (
                      <Td
                        key={cellKey}
                        {...cellProps}
                        borderRightWidth={
                          cellIndex === subRow.cells.length - 1 ? "" : "1px"
                        }
                        borderBottom="none"
                        borderColor="gray.200"
                        padding={0}
                      >
                        {cell.render("Cell")}
                      </Td>
                    );
                  })}
                </Tr>
              );
            });

            return [groupHeader, groupedRows];
          })}
        </Tbody>
      </Table>
    </Box>
  );
};

export default VendorCookieTable;

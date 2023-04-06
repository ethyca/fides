import {
  ArrowDownIcon,
  ArrowUpIcon,
  Box,
  Button,
  Switch,
  Table,
  TableContainer,
  Tag,
  Tbody,
  Td,
  Text,
  Tfoot,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { ReactNode } from "react";
import { CellProps, Column, useSortBy, useTable } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { PrivacyNoticeResponse } from "~/types/api";

import { MECHANISM_MAP } from "./constants";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
} from "./privacy-notices.slice";

const DateCell = ({ value }: CellProps<PrivacyNoticeResponse, string>) =>
  new Date(value).toDateString();

const MechanismCell = ({ value }: CellProps<PrivacyNoticeResponse, string>) => (
  <Tag size="sm" backgroundColor="primary.400" color="white">
    {MECHANISM_MAP.get(value) ?? value}
  </Tag>
);

const MultiTagCell = ({
  value,
}: CellProps<PrivacyNoticeResponse, string[]>) => (
  <Box>
    {value.map((v, idx) => (
      <Tag
        key={v}
        size="sm"
        backgroundColor="primary.400"
        color="white"
        mr={idx === value.length - 1 ? 0 : 3}
        textTransform="uppercase"
      >
        {v}
      </Tag>
    ))}
  </Box>
);

const ToggleCell = ({ value }: CellProps<PrivacyNoticeResponse, boolean>) => (
  <Switch colorScheme="complimentary" isChecked={!value} />
);

const COLUMNS: Column<PrivacyNoticeResponse>[] = [
  {
    Header: "Title",
    accessor: "name",
    Cell: ({ value }) => (
      <Text fontWeight="semibold" color="gray.600">
        {value}
      </Text>
    ),
  },
  {
    Header: "Description",
    accessor: "description",
    Cell: ({ value }) => <Text whiteSpace="normal">{value}</Text>,
  },
  { Header: "Mechanism", accessor: "consent_mechanism", Cell: MechanismCell },
  { Header: "Locations", accessor: "regions", Cell: MultiTagCell },
  { Header: "Created", accessor: "created_at", Cell: DateCell },
  { Header: "Last update", accessor: "updated_at", Cell: DateCell },
  { Header: "Enable", accessor: "disabled", Cell: ToggleCell },
];

const PrivacyNoticesTable = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);

  const tableInstance = useTable(
    { columns: COLUMNS, data: privacyNotices },
    useSortBy
  );

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    tableInstance;

  if (privacyNotices.length === 0) {
    return <Text>No privacy notices found.</Text>;
  }

  return (
    <TableContainer>
      <Table
        {...getTableProps()}
        borderRadius="6px 6px 0px 0px"
        border="1px solid"
        borderColor="gray.200"
        fontSize="sm"
      >
        <Thead backgroundColor="gray.50">
          {headerGroups.map((headerGroup) => {
            const { key: headerRowKey, ...headerGroupProps } =
              headerGroup.getHeaderGroupProps();
            return (
              <Tr key={headerRowKey} {...headerGroupProps}>
                {headerGroup.headers.map((column) => {
                  const { key: columnKey, ...headerProps } =
                    column.getHeaderProps(column.getSortByToggleProps());
                  let sortIcon: ReactNode = null;
                  if (column.isSorted) {
                    sortIcon = column.isSortedDesc ? (
                      <ArrowDownIcon color="gray.500" />
                    ) : (
                      <ArrowUpIcon color="gray.500" />
                    );
                  }

                  return (
                    <Th
                      key={columnKey}
                      {...headerProps}
                      textTransform="none"
                      fontSize="sm"
                      p={5}
                    >
                      {column.render("Header")}
                      {sortIcon}
                    </Th>
                  );
                })}
              </Tr>
            );
          })}
        </Thead>
        <Tbody {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);
            const { key: rowKey, ...rowProps } = row.getRowProps();
            return (
              <Tr
                key={rowKey}
                {...rowProps}
                _hover={{ backgroundColor: "gray.50", cursor: "pointer" }}
                backgroundColor={row.values.disabled ? "gray.50" : undefined}
              >
                {row.cells.map((cell) => {
                  const { key: cellKey, ...cellProps } = cell.getCellProps();
                  return (
                    <Td
                      key={cellKey}
                      {...cellProps}
                      p={5}
                      verticalAlign="baseline"
                    >
                      {cell.render("Cell")}
                    </Td>
                  );
                })}
              </Tr>
            );
          })}
        </Tbody>
        <Tfoot backgroundColor="gray.50">
          <Tr>
            <Td colSpan={COLUMNS.length} px={4} py={3.5}>
              <Button size="xs" colorScheme="primary">
                Add a privacy notice +
              </Button>
            </Td>
          </Tr>
        </Tfoot>
      </Table>
    </TableContainer>
  );
};

export default PrivacyNoticesTable;

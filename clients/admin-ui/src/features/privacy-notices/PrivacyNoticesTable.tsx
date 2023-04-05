import {
  Box,
  Table,
  TableContainer,
  Tag,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { CellProps, Column, useTable } from "react-table";

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
    {value.map((v) => (
      <Tag key={v} size="sm" backgroundColor="primary.400" color="white">
        {v}
      </Tag>
    ))}
  </Box>
);

const COLUMNS: Column<PrivacyNoticeResponse>[] = [
  { Header: "Title", accessor: "name" },
  { Header: "Description", accessor: "description" },
  { Header: "Mechanism", accessor: "consent_mechanism", Cell: MechanismCell },
  { Header: "Locations", accessor: "regions", Cell: MultiTagCell },
  { Header: "Created", accessor: "created_at", Cell: DateCell },
  { Header: "Last update", accessor: "updated_at", Cell: DateCell },
  { Header: "Enable", accessor: "disabled" },
];

const PrivacyNoticesTable = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);

  const tableInstance = useTable({ columns: COLUMNS, data: privacyNotices });

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
                    column.getHeaderProps();
                  return (
                    <Th
                      key={columnKey}
                      {...headerProps}
                      textTransform="none"
                      fontSize="sm"
                    >
                      {column.render("Header")}
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
              <Tr key={rowKey} {...rowProps}>
                {row.cells.map((cell) => {
                  const { key: cellKey, ...cellProps } = cell.getCellProps();
                  return (
                    <Td key={cellKey} {...cellProps}>
                      {cell.render("Cell")}
                    </Td>
                  );
                })}
              </Tr>
            );
          })}
        </Tbody>
      </Table>
    </TableContainer>
  );
};

export default PrivacyNoticesTable;

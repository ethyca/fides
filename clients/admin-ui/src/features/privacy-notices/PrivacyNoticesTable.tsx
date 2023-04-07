import {
  ArrowDownIcon,
  ArrowUpIcon,
  Button,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Tfoot,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { useRouter } from "next/router";
import { ReactNode, useMemo } from "react";
import { Column, useSortBy, useTable } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";

import {
  DateCell,
  EnablePrivacyNoticeCell,
  MechanismCell,
  MultiTagCell,
  TitleCell,
  WrappedCell,
} from "./cells";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
} from "./privacy-notices.slice";

const PrivacyNoticesTable = () => {
  const router = useRouter();
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  const columns: Column<PrivacyNoticeResponse>[] = useMemo(
    () => [
      {
        Header: "Title",
        accessor: "name",
        Cell: TitleCell,
      },
      {
        Header: "Description",
        accessor: "description",
        Cell: WrappedCell,
      },
      {
        Header: "Mechanism",
        accessor: "consent_mechanism",
        Cell: MechanismCell,
      },
      { Header: "Locations", accessor: "regions", Cell: MultiTagCell },
      { Header: "Created", accessor: "created_at", Cell: DateCell },
      { Header: "Last update", accessor: "updated_at", Cell: DateCell },
      {
        Header: "Enable",
        accessor: "disabled",
        disabled: !userCanUpdate,
        Cell: EnablePrivacyNoticeCell,
      },
    ],
    [userCanUpdate]
  );

  const tableInstance = useTable({ columns, data: privacyNotices }, useSortBy);

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
                      p={4}
                      data-testid={`column-${column.Header}`}
                    >
                      <Text
                        _hover={{ backgroundColor: "gray.100" }}
                        p={1}
                        borderRadius="4px"
                        pr={sortIcon ? 0 : 3.5}
                      >
                        {column.render("Header")}
                        {sortIcon}
                      </Text>
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
            const onClick = () => {
              if (userCanUpdate) {
                router.push(`${PRIVACY_NOTICES_ROUTE}/${row.original.id}`);
              }
            };
            return (
              <Tr
                key={rowKey}
                {...rowProps}
                _hover={
                  userCanUpdate
                    ? { backgroundColor: "gray.50", cursor: "pointer" }
                    : undefined
                }
                data-testid={`row-${row.original.name}`}
              >
                {row.cells.map((cell) => {
                  const { key: cellKey, ...cellProps } = cell.getCellProps();
                  return (
                    <Td
                      key={cellKey}
                      {...cellProps}
                      p={5}
                      verticalAlign="baseline"
                      onClick={
                        cell.column.Header !== "Enable" ? onClick : undefined
                      }
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
            <Td colSpan={columns.length} px={4} py={3.5}>
              <Restrict scopes={[ScopeRegistryEnum.PRIVACY_NOTICE_CREATE]}>
                <Button
                  size="xs"
                  colorScheme="primary"
                  data-testid="add-privacy-notice-btn"
                >
                  Add a privacy notice +
                </Button>
              </Restrict>
            </Td>
          </Tr>
        </Tfoot>
      </Table>
    </TableContainer>
  );
};

export default PrivacyNoticesTable;

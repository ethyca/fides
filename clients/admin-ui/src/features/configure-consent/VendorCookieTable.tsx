import {
  Box,
  Flex,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Table,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { useMemo, useState } from "react";
import {
  Column,
  Row,
  useFlexLayout,
  useGlobalFilter,
  useGroupBy,
  useResizeColumns,
  useTable,
} from "react-table";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { PaddedCell } from "~/features/common/table";
import GroupedTableBody from "~/features/common/table/grouped/GroupedTableBody";
import GroupedTableHeader from "~/features/common/table/grouped/GroupedTableHeader";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";
import { selectAllSystems, useDeleteSystemMutation } from "~/features/system";
import { System } from "~/types/api";

import { DataUseCell } from "./cells";
import { CookieBySystem, transformSystemsToCookies } from "./vendor-transform";

const VendorCookieTable = () => {
  const systems = useAppSelector(selectAllSystems);
  const cookiesBySystem = useMemo(
    () => transformSystemsToCookies(systems),
    [systems]
  );

  // const [systemToEdit, setSystemToEdit] = useState<System | undefined>(
  //   undefined
  // );
  const [systemToDelete, setSystemToDelete] = useState<System | undefined>(
    undefined
  );

  const {
    isOpen: isDeleteModalOpen,
    onOpen: onDeleteModalOpen,
    onClose: onDeleteModalClose,
  } = useDisclosure();

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

  const [deleteSystem] = useDeleteSystemMutation();
  const toast = useToast();

  const handleDelete = async (systemFidesKey: string) => {
    const result = await deleteSystem(systemFidesKey);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully deleted vendor"));
    }
    onDeleteModalClose();
  };

  const handleOpenDeleteModal = (systemFidesKey: string) => {
    const system = systems.find((s) => systemFidesKey === s.fides_key);
    setSystemToDelete(system);
    onDeleteModalOpen();
  };

  // const handleEdit = (systemFidesKey: string) => {
  // const system = systems.find((s) => systemFidesKey === s.fides_key);
  // setSystemToEdit(system);
  // };

  const renderOverflowMenu = (row: Row<CookieBySystem>) => (
    <Menu>
      <MenuButton
        as={IconButton}
        aria-label="Show vendor options"
        icon={<MoreIcon />}
        size="xs"
        variant="outline"
        data-testid={`configure-${row.values.id}`}
      />
      <MenuList>
        <MenuItem data-testid={`edit-${row.values.id}`}>
          Manage cookies
        </MenuItem>
        <MenuItem
          data-testid={`delete-${row.values.id}`}
          onClick={() => handleOpenDeleteModal(row.values.id)}
        >
          Delete
        </MenuItem>
      </MenuList>
    </Menu>
  );

  return (
    <Box boxSize="100%" overflow="auto">
      <HStack mt={2} mb={4} justifyContent="space-between">
        <GlobalFilter
          globalFilter={tableInstance.state.globalFilter}
          setGlobalFilter={tableInstance.setGlobalFilter}
          placeholder="Search"
        />
        <Flex>
          <Flex width="10px" />
          {
            // <AddVendor
            //   passedInSystem={systemToEdit}
            //   onCloseModal={() => setSystemToEdit(undefined)}
            // />
          }
        </Flex>
        <ConfirmationModal
          isOpen={isDeleteModalOpen}
          onClose={onDeleteModalClose}
          onConfirm={() => handleDelete(systemToDelete!.fides_key)}
          title={`Delete ${systemToDelete?.name ?? systemToDelete?.fides_key}`}
          message={
            <>
              <Text>
                This will delete the vendor{" "}
                <Text color="complimentary.500" as="span" fontWeight="bold">
                  {systemToDelete?.name ?? systemToDelete?.fides_key}
                </Text>{" "}
                and all its cookies.
              </Text>
              <Text>Are you sure you want to continue?</Text>
            </>
          }
        />
      </HStack>
      <Table {...getTableProps()} size="sm" data-testid="datamap-table">
        <GroupedTableHeader<CookieBySystem> headerGroups={headerGroups} />
        <GroupedTableBody<CookieBySystem>
          rows={rows}
          renderRowSubheading={(row) => row.values.name}
          prepareRow={prepareRow}
          getTableBodyProps={getTableBodyProps}
          renderOverflowMenu={renderOverflowMenu}
        />
      </Table>
    </Box>
  );
};

export default VendorCookieTable;

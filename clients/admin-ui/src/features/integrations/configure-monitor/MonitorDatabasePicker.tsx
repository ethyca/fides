/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Flex } from "fidesui";
import { useMemo, useState } from "react";

import SearchBar from "~/features/common/SearchBar";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  IndeterminateCheckboxCell,
  TableActionBar,
} from "~/features/common/table/v2";

interface DatabaseTableItem {
  id: string;
  selected: boolean;
  allSelected: boolean;
}

const columnHelper = createColumnHelper<DatabaseTableItem>();

const MonitorDatabasePicker = ({
  items,
  selected,
  allSelected,
  someSelected,
  handleToggleSelection,
  handleToggleAll,
}: {
  items: { name: string; id: string }[];
  selected: string[];
  allSelected: boolean;
  someSelected: boolean;
  handleToggleSelection: (item: string) => void;
  handleToggleAll: () => void;
}) => {
  const [searchParam, setSearchParam] = useState<string>("");

  const data: DatabaseTableItem[] = items.map((item) => ({
    allSelected,
    id: item.id,
    selected: selected.includes(item.id) || allSelected,
  }));

  const columns: ColumnDef<DatabaseTableItem, any>[] = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={row.original.selected}
            isDisabled={allSelected}
            onChange={() => handleToggleSelection(row.original.id)}
          />
        ),
        header: () => (
          <IndeterminateCheckboxCell
            isChecked={allSelected}
            isIndeterminate={!allSelected && someSelected}
            onChange={handleToggleAll}
          />
        ),
        size: 1,
        meta: {
          disableRowClick: allSelected,
        },
      }),
      columnHelper.accessor((row) => row.id, {
        id: "id",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Projects" {...props} />,
        meta: {
          disableRowClick: allSelected,
        },
      }),
    ],
    [handleToggleSelection, handleToggleAll, allSelected, someSelected]
  );

  const tableInstance = useReactTable<DatabaseTableItem>({
    getCoreRowModel: getCoreRowModel(),
    getRowId: (row) => row.id,
    manualPagination: true,
    data,
    columns,
  });

  return (
    <Flex w="full" direction="column" maxH="lg">
      <TableActionBar w="full">
        <SearchBar
          value={searchParam}
          onChange={setSearchParam}
          placeholder="Search..."
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={(row) => handleToggleSelection(row.id)}
      />
    </Flex>
  );

  // return (
  //   <Flex w="full" direction="column" gap={3}>
  //     <Checkbox
  //       fontSize="md"
  //       isChecked={allSelected}
  //       size="md"
  //       mr={2}
  //       onChange={handleToggleAll}
  //       colorScheme="complimentary"
  //       data-testid="select-all"
  //       isIndeterminate={!allSelected && someSelected}
  //     >
  //       Select all
  //     </Checkbox>
  //     {numSelected > 0 ? (
  //       <Badge
  //         colorScheme="purple"
  //         variant="solid"
  //         width="fit-content"
  //         data-testid="num-selected-badge"
  //       >
  //         {numSelected} selected
  //       </Badge>
  //     ) : null}
  //     <Flex pl={6} fontSize="sm" gap={2} direction="column">
  //       <CheckboxGroup colorScheme="complimentary">
  //         {items.map((item) => (
  //           <Checkbox
  //             key={item.id}
  //             isChecked={selected.includes(item.id) || allSelected}
  //             size="md"
  //             onChange={() => handleToggleSelection(item.id)}
  //             disabled={allSelected}
  //             data-testid={`${item.id}-checkbox`}
  //           >
  //             {item.name}
  //           </Checkbox>
  //         ))}
  //       </CheckboxGroup>
  //     </Flex>
  //   </Flex>
  // );
};

export default MonitorDatabasePicker;

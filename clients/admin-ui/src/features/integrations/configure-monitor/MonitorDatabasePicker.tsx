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
  isSelected: boolean;
  isExcluded: boolean;
}

interface MonitorDatabasePickerProps {
  items: string[];
  selected: string[];
  excluded: string[];
  allSelected: boolean;
  someSelected: boolean;
  handleToggleSelection: (item: string) => void;
  handleToggleAll: () => void;
}

const columnHelper = createColumnHelper<DatabaseTableItem>();

const MonitorDatabasePicker = ({
  items,
  selected,
  excluded,
  allSelected,
  someSelected,
  handleToggleSelection,
  handleToggleAll,
}: MonitorDatabasePickerProps) => {
  const [searchParam, setSearchParam] = useState<string>("");

  const data: DatabaseTableItem[] = items.map((item) => ({
    id: item,
    isSelected: selected.includes(item),
    isExcluded: excluded.includes(item),
  }));

  const columns: ColumnDef<DatabaseTableItem, any>[] = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={
              row.original.isSelected ||
              (allSelected && !row.original.isExcluded)
            }
            onChange={() => handleToggleSelection(row.original.id)}
          />
        ),
        header: () => (
          <IndeterminateCheckboxCell
            isChecked={allSelected}
            isIndeterminate={someSelected}
            onChange={handleToggleAll}
          />
        ),
        size: 1,
      }),
      columnHelper.accessor((row) => row.id, {
        id: "id",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Projects" {...props} />,
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
};

export default MonitorDatabasePicker;

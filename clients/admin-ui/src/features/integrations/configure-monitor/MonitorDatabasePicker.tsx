/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button, Flex } from "fidesui";
import { useMemo } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableFooter,
  FidesTableV2,
  IndeterminateCheckboxCell,
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
  moreLoading?: boolean;
  handleToggleSelection: (item: string) => void;
  handleToggleAll: () => void;
  onMoreClick?: () => void;
}

const columnHelper = createColumnHelper<DatabaseTableItem>();

const MonitorDatabasePicker = ({
  items,
  selected,
  excluded,
  allSelected,
  someSelected,
  moreLoading,
  handleToggleSelection,
  handleToggleAll,
  onMoreClick,
}: MonitorDatabasePickerProps) => {
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
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={(row) => handleToggleSelection(row.id)}
        footer={
          !!onMoreClick && (
            <FidesTableFooter totalColumns={2}>
              <Flex justify="center">
                {moreLoading ? (
                  <FidesSpinner size="xs" />
                ) : (
                  <Button onClick={onMoreClick} variant="outline" size="xs">
                    Load more...
                  </Button>
                )}
              </Flex>
            </FidesTableFooter>
          )
        }
      />
    </Flex>
  );
};

export default MonitorDatabasePicker;

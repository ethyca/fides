import { Box, Button, Flex, HStack, Spinner } from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  FidesTableV2,
  GlobalFilterV2,
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/tablev2";
import {
  DictSystems,
  selectAllDictSystems,
  useGetAllCreatedSystemsQuery,
  usePostCreatedSystemsMutation,
} from "~/features/plus/plus.slice";

type MultipleSystemTable = DictSystems;

const columnHelper = createColumnHelper<MultipleSystemTable>();

type Props = {
  redirectRoute: string;
};

export const AddMultipleSystemsV2 = ({ redirectRoute }: Props) => {
  const features = useFeatures();
  const router = useRouter();
  const { isLoading: isGetLoading } = useGetAllCreatedSystemsQuery(undefined, {
    skip: !features.dictionaryService,
  });
  const [
    postVendorIds,
    { isLoading: isPostLoading, isSuccess: isPostSuccess },
  ] = usePostCreatedSystemsMutation();

  const dictionaryOptions = useAppSelector(selectAllDictSystems);
  const [globalFilter, setGlobalFilter] = useState();

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            {...{
              checked: table.getIsAllRowsSelected(),
              indeterminate: table.getIsSomeRowsSelected(),
              onChange: table.getToggleAllRowsSelectedHandler(),
            }}
          />
        ),
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            {...{
              checked: row.getIsSelected(),
              disabled: !row.getCanSelect(),
              indeterminate: row.getIsSomeSelected(),
              onChange: row.getToggleSelectedHandler(),
              initialValue: row.original.linked_system,
            }}
          />
        ),
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: "legal_name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Name",
      }),
    ],
    []
  );

  const rowSelection = useMemo(() => {
    const rowSelection: Record<string, boolean> = {};
    dictionaryOptions.forEach((ds, index) => {
      if (ds.linked_system) {
        rowSelection[index] = true;
      }
    });
    return rowSelection;
  }, [dictionaryOptions]);

  const tableInstance = useReactTable<MultipleSystemTable>({
    columns,
    data: dictionaryOptions.slice(0, 25),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    enableRowSelection: true,
    enableSorting: true,
    enableGlobalFilter: true,
    state: {
      globalFilter,
    },
    initialState: {
      rowSelection,
    },
  });

  const addVendors = async () => {
    const vendorIds = tableInstance
      .getSelectedRowModel()
      .rows.filter((r) => !r.original.linked_system)
      .map((r) => r.original.vendor_id);
    if (vendorIds.length > 0) {
      // await postVendorIds(vendorIds);
      // router.push(redirectRoute);
      console.log(vendorIds);
    }
  };

  const anyNewSelectedRows = tableInstance
    .getSelectedRowModel()
    .rows.some((row) => !row.original.linked_system);

  if (isGetLoading || isPostLoading || isPostSuccess) {
    return (
      <Flex justifyContent="center" alignItems="center" mt="5">
        <Spinner color="complimentary.500" />
      </Flex>
    );
  }

  return (
    <Box height="100%">
      <HStack
        justifyContent="space-between"
        alignItems="center"
        p={2}
        borderWidth="1px"
        borderBottomWidth="0px"
        borderColor="gray.200"
      >
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={setGlobalFilter}
          placeholder="search"
        />
        <Button
          onClick={addVendors}
          size="xs"
          variant="outline"
          disabled={!anyNewSelectedRows}
        >
          Add Vendors
        </Button>
      </HStack>
      <FidesTableV2<MultipleSystemTable>
        columns={columns}
        data={dictionaryOptions}
        tableInstance={tableInstance}
      />
    </Box>
  );
};

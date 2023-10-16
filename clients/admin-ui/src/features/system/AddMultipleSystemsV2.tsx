import { Box, Button, Flex, Spinner } from "@fidesui/react";
import { useRouter } from "next/router";
import {
  HTMLProps,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  createColumnHelper,
  useReactTable,
  ColumnDef,
  Row,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
} from "@tanstack/react-table";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  FidesTableV2,
  WrappedCell,
  useFidesTableV2,
} from "~/features/common/tablev2";
import {
  DictSystems,
  selectAllDictSystems,
  useGetAllCreatedSystemsQuery,
  usePostCreatedSystemsMutation,
} from "~/features/plus/plus.slice";

type MultipleSystemTable = DictSystems;

type CheckboxProps = {
  indeterminate?: boolean;
  row?: Row<MultipleSystemTable>;
} & HTMLProps<HTMLInputElement>;

const IndeterminateCheckboxTest = ({
  indeterminate,
  className = "",
  row,
  ...rest
}: CheckboxProps) => {
  const ref = useRef<HTMLInputElement>(null!);
  const [initialCheckBoxValue] = useState(row?.original.linked_system);

  useEffect(() => {
    if (typeof indeterminate === "boolean") {
      ref.current.indeterminate = !rest.checked && indeterminate;
    }
  }, [ref, indeterminate, rest.checked]);

  if (initialCheckBoxValue) {
    return (
      <input
        type="checkbox"
        ref={ref}
        disabled
        className={`${className} cursor-pointer`}
        checked
      />
    );
  }

  return (
    <input
      type="checkbox"
      ref={ref}
      className={`${className} cursor-pointer`}
      {...rest}
    />
  );
};

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
          <IndeterminateCheckboxTest
            {...{
              checked: table.getIsAllRowsSelected(),
              indeterminate: table.getIsSomeRowsSelected(),
              onChange: table.getToggleAllRowsSelectedHandler(),
            }}
          />
        ),
        cell: ({ row }) => (
          <IndeterminateCheckboxTest
            {...{
              checked: row.getIsSelected(),
              disabled: !row.getCanSelect(),
              indeterminate: row.getIsSomeSelected(),
              onChange: row.getToggleSelectedHandler(),
              row: row,
            }}
          />
        ),
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: "legal_name",
        cell: (props) => <div>{props.getValue()} </div>,
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
    data: dictionaryOptions,
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
      <input
        value={globalFilter ?? ""}
        onChange={(e) => setGlobalFilter(e.target.value)}
        placeholder="search"
      />
      <Button
        onClick={addVendors}
        colorScheme="black"
        backgroundColor="primary.800"
        fontWeight="semibold"
        disabled={!anyNewSelectedRows}
      >
        Add Vendors
      </Button>
      <FidesTableV2<MultipleSystemTable>
        columns={columns}
        showSearchBar
        data={dictionaryOptions}
        tableInstance={tableInstance}
      />
    </Box>
  );
};

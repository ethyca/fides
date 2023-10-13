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
import { Column, Hooks, Row, TableInstance, useRowSelect } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { FidesTable, WrappedCell } from "~/features/common/table";
import { FidesObject } from "~/features/common/table/FidesTable";
import {
  DictSystems,
  selectAllDictSystems,
  useGetAllCreatedSystemsQuery,
  usePostCreatedSystemsMutation,
} from "~/features/plus/plus.slice";

type CheckboxProps = {
  indeterminate?: boolean;
  row: Row<MultipleSystemTable>;
} & HTMLProps<HTMLInputElement>;

const IndeterminateCheckboxTest = ({
  indeterminate,
  className = "",
  ...rest
}: CheckboxProps) => {
  const ref = useRef<HTMLInputElement>(null!);
  const [initialCheckedValue] = useState(rest?.row?.original.linked_system);

  useEffect(() => {
    if (typeof indeterminate === "boolean") {
      ref.current.indeterminate = !rest.checked && indeterminate;
    }
  }, [ref, indeterminate, rest.checked]);

  if (initialCheckedValue) {
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
      disabled={initialCheckedValue}
      className={`${className} cursor-pointer`}
      {...rest}
    />
  );
};

type MultipleSystemTable = DictSystems & FidesObject;

type Props = {
  redirectRoute: string;
};

export const AddMultipleSystems = ({ redirectRoute }: Props) => {
  const features = useFeatures();
  const router = useRouter();
  const { isLoading: isGetLoading } = useGetAllCreatedSystemsQuery(undefined, {
    skip: !features.dictionaryService,
  });
  const [
    postVendorIds,
    { isLoading: isPostLoading, isSuccess: isPostSuccess },
  ] = usePostCreatedSystemsMutation();

  const customCheckboxHook = useCallback(
    (hooks: Hooks<MultipleSystemTable>) => {
      hooks.visibleColumns.push((columns) => [
        // Let's make a column for selection
        {
          id: "selection",
          /* eslint-disable */
          Header: ({ getToggleAllRowsSelectedProps }: any) => (
            <IndeterminateCheckboxTest {...getToggleAllRowsSelectedProps()} />
          ),
          Cell: ({ row }: any) => (
            <IndeterminateCheckboxTest
              {...row.getToggleRowSelectedProps()}
              row={row}
            />
          ),
          /* eslint-enable */
        },
        ...columns,
      ]);
    },
    []
  );

  const dictionaryOptions = useAppSelector(selectAllDictSystems);

  const columns: Column<DictSystems>[] = useMemo(
    () => [{ Header: "System", accessor: "legal_name", Cell: WrappedCell }],
    []
  );

  const tableInstanceRef = useRef<TableInstance<MultipleSystemTable>>();

  const initialTableState = useMemo(() => {
    const selectedRowIds: any = {};
    dictionaryOptions.forEach((ds, index) => {
      if (ds.linked_system) {
        selectedRowIds[index] = true;
      }
    });
    return {
      selectedRowIds,
    };
  }, [dictionaryOptions]);

  const addVendors = async () => {
    if (tableInstanceRef.current) {
      const vendorIds = tableInstanceRef.current.selectedFlatRows
        .filter((r) => r.isSelected && !r.original.linked_system)
        .map((r) => r.original.vendor_id);
      if (vendorIds.length > 0) {
        await postVendorIds(vendorIds);
        router.push(redirectRoute);
      }
    }
  };

  if (isGetLoading || isPostLoading || isPostSuccess) {
    return (
      <Flex justifyContent="center" alignItems="center" mt="5">
        <Spinner color="complimentary.500" />
      </Flex>
    );
  }

  return (
    <Box height="100%">
      <FidesTable<MultipleSystemTable>
        columns={columns}
        showSearchBar
        searchBarRightButton={
          <Button
            onClick={addVendors}
            colorScheme="black"
            backgroundColor="primary.800"
            fontWeight="semibold"
          >
            Add Vendors
          </Button>
        }
        data={dictionaryOptions}
        tableInstanceRef={tableInstanceRef}
        customHooks={[useRowSelect, customCheckboxHook]}
        initialState={initialTableState}
      />
    </Box>
  );
};

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
} from "~/features/plus/plus.slice";

type Props = {
  indeterminate?: boolean;
  row: Row<MultipleSystemTable>;
} & HTMLProps<HTMLInputElement>;

const IndeterminateCheckboxTest = ({
  indeterminate,
  className = "",
  ...rest
}: Props) => {
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

export const AddMultipleSystems = () => {
  const features = useFeatures();
  useGetAllCreatedSystemsQuery(undefined, {
    skip: !features.dictionaryService,
  });

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

  return (
    <div>
      <FidesTable<MultipleSystemTable>
        columns={columns}
        data={dictionaryOptions}
        tableInstanceRef={tableInstanceRef}
        customHooks={[useRowSelect, customCheckboxHook]}
        initialState={initialTableState}
      />
    </div>
  );
};

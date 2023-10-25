/* eslint-disable react/no-unstable-nested-components */
import {
  Badge,
  Button,
  Flex,
  Spinner,
  Tooltip,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import ConfirmationModal from "~/features/common/ConfirmationModal";
import { useFeatures } from "~/features/common/features";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  VendorSources,
} from "~/features/common/helpers";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  IndeterminateCheckboxCell,
  PaginationBar,
  RowSelectionBar,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  DictSystems,
  selectAllDictSystems,
  useGetAllCreatedSystemsQuery,
  usePostCreatedSystemsMutation,
} from "~/features/plus/plus.slice";

export const VendorSourceCell = ({ value }: { value: string }) => (
  <Flex alignItems="center" height="100%">
    <Badge>
      {extractVendorSource(value) === VendorSources.GVL ? "GVL" : "AC"}
    </Badge>
  </Flex>
);

type MultipleSystemTable = DictSystems;

const columnHelper = createColumnHelper<MultipleSystemTable>();

type Props = {
  redirectRoute: string;
};

export const AddMultipleSystems = ({ redirectRoute }: Props) => {
  const systemText = "Vendor";
  const toast = useToast();
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
  const { isOpen, onClose, onOpen } = useDisclosure();

  const allRowsAdded = dictionaryOptions.every((d) => d.linked_system);
  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            {...{
              checked: table.getIsAllRowsSelected(),
              indeterminate:
                table
                  .getSelectedRowModel()
                  .rows.filter((r) => !r.original.linked_system).length > 0,
              onChange: table.getToggleAllRowsSelectedHandler(),
              manualDisable: allRowsAdded,
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
        meta: {
          width: "55px",
        },
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: "legal_name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value={systemText} {...props} />,
      }),
      columnHelper.accessor((row) => row.vendor_id, {
        id: "vendor_id",
        cell: (props) => <VendorSourceCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Source" {...props} />,
        meta: {
          width: "80px",
        },
      }),
    ],
    [allRowsAdded, systemText]
  );

  const rowSelection = useMemo(() => {
    const innerRowSelection: Record<string, boolean> = {};
    dictionaryOptions.forEach((ds, index) => {
      if (ds.linked_system) {
        innerRowSelection[index] = true;
      }
    });
    return innerRowSelection;
  }, [dictionaryOptions]);

  const tableInstance = useReactTable<MultipleSystemTable>({
    columns,
    data: dictionaryOptions,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    enableRowSelection: true,
    enableSorting: true,
    enableGlobalFilter: true,
    state: {
      globalFilter,
    },
    initialState: {
      rowSelection,
      pagination: {
        pageSize: 25,
      },
    },
  });

  const addVendors = async () => {
    const vendorIds = tableInstance
      .getSelectedRowModel()
      .rows.filter((r) => !r.original.linked_system)
      .map((r) => r.original.vendor_id);
    if (vendorIds.length > 0) {
      const result = await postVendorIds(vendorIds);
      router.push(redirectRoute);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(
          successToastParams(
            `Successfully added ${
              vendorIds.length
            } ${systemText.toLocaleLowerCase()}`
          )
        );
      }
    }
  };

  const anyNewSelectedRows = tableInstance
    .getSelectedRowModel()
    .rows.some((row) => !row.original.linked_system);

  if (isPostLoading || isPostSuccess) {
    return (
      <Flex height="100%" justifyContent="center" alignItems="center">
        <Spinner />
      </Flex>
    );
  }

  if (isGetLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  const toolTipText = allRowsAdded
    ? `All ${systemText.toLocaleLowerCase()} have already been added`
    : `Select a ${systemText.toLocaleLowerCase()} `;

  const totalSelectSystemsLength = tableInstance
    .getSelectedRowModel()
    .rows.filter((r) => !r.original.linked_system).length;

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <ConfirmationModal
        isOpen={isOpen}
        isCentered
        onCancel={onClose}
        onClose={onClose}
        onConfirm={addVendors}
        title="Confirmation"
        message={`You are about to add ${totalSelectSystemsLength} ${systemText.toLocaleLowerCase()}${
          totalSelectSystemsLength > 1 ? "s" : ""
        }`}
      />
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={setGlobalFilter}
          placeholder="Search"
        />
        <Tooltip
          label={toolTipText}
          shouldWrapChildren
          placement="top"
          isDisabled={
            (anyNewSelectedRows && !allRowsAdded) ||
            (anyNewSelectedRows && allRowsAdded)
          }
        >
          <Button
            onClick={onOpen}
            data-testid="add-multiple-systems-btn"
            size="xs"
            variant="outline"
            disabled={!anyNewSelectedRows}
          >
            Add {`${systemText}s`}
          </Button>
        </Tooltip>
      </TableActionBar>
      <FidesTableV2<MultipleSystemTable>
        tableInstance={tableInstance}
        rowActionBar={
          <RowSelectionBar<MultipleSystemTable>
            tableInstance={tableInstance}
            selectedRows={
              tableInstance
                .getSelectedRowModel()
                .rows.filter((r) => !r.original.linked_system).length
            }
          />
        }
      />
      <PaginationBar tableInstance={tableInstance} />
    </Flex>
  );
};

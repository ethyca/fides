/* eslint-disable react/no-unstable-nested-components */
import {
  Badge,
  Box,
  Button,
  Flex,
  Spinner,
  Tag,
  Text,
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
import ConfirmationModal from "common/ConfirmationModal";
import { useFeatures } from "common/features";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  vendorSourceLabels,
} from "common/helpers";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  IndeterminateCheckboxCell,
  PAGE_SIZES,
  PaginationBar,
  RowSelectionBar,
  TableActionBar,
  TableSkeletonLoader,
} from "common/table/v2";
import { errorToastParams, successToastParams } from "common/toast";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { INDEX_ROUTE } from "~/features/common/nav/v2/routes";
import {
  DictSystems,
  selectAllDictSystems,
  useGetAllSystemVendorsQuery,
  useGetHealthQuery,
  usePostSystemVendorsMutation,
} from "~/features/plus/plus.slice";
import MultipleSystemsFilterModal from "~/features/system/add-multiple-systems/MultipleSystemsFilterModal";

export const VendorSourceCell = ({ value }: { value: string }) => {
  const source = extractVendorSource(value);
  const labels = vendorSourceLabels[source] ?? { label: "", fullName: "" };
  return (
    <Flex alignItems="center" justifyContent="center" height="100%" mr="2">
      <Tooltip label={labels.fullName} placement="top">
        <Badge>{labels.label}</Badge>
      </Tooltip>
    </Flex>
  );
};

type MultipleSystemTable = DictSystems;

const columnHelper = createColumnHelper<MultipleSystemTable>();

type Props = {
  redirectRoute: string;
};

export const AddMultipleSystems = ({ redirectRoute }: Props) => {
  const systemText = "Vendor";
  const toast = useToast();
  const { dictionaryService, tcf: isTcfEnabled } = useFeatures();
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const router = useRouter();
  const { isLoading: isGetLoading } = useGetAllSystemVendorsQuery(undefined, {
    skip: !dictionaryService,
  });
  const [
    postVendorIds,
    { isLoading: isPostLoading, isSuccess: isPostSuccess },
  ] = usePostSystemVendorsMutation();

  const dictionaryOptions = useAppSelector(selectAllDictSystems);
  const [globalFilter, setGlobalFilter] = useState();
  const {
    isOpen: isFilterOpen,
    onOpen: onOpenFilter,
    onClose: onCloseFilter,
  } = useDisclosure();
  const { isOpen, onClose, onOpen } = useDisclosure();
  const [isRowSelectionBarOpen, setIsRowSelectionBarOpen] =
    useState<boolean>(false);

  const allRowsLinkedToSystem = dictionaryOptions.every((d) => d.linked_system);
  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            {...{
              checked: table.getIsAllPageRowsSelected(),
              indeterminate: table
                .getPaginationRowModel()
                .rows.filter((r) => !r.original.linked_system)
                .some((r) => r.getIsSelected()),
              onChange: (e) => {
                table.getToggleAllPageRowsSelectedHandler()(e);
                setIsRowSelectionBarOpen((prev) => !prev);
              },
              manualDisable:
                allRowsLinkedToSystem ||
                table
                  .getPaginationRowModel()
                  .rows.filter((r) => r.original.linked_system).length ===
                  table.getState().pagination.pageSize,
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
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value={systemText} {...props} />,
      }),
      columnHelper.accessor((row) => row.vendor_id, {
        id: "vendor_id",
        cell: (props) => <VendorSourceCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Source" {...props} />,
        enableColumnFilter: isTcfEnabled,
        filterFn: "arrIncludesSome",
        meta: {
          width: "80px",
        },
      }),
    ],
    [allRowsLinkedToSystem, systemText, isTcfEnabled]
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
      columnVisibility: {
        vendor_id: isTcfEnabled,
      },
    },
    initialState: {
      rowSelection,
      pagination: {
        pageSize: PAGE_SIZES[0],
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

  const isTooltipDisabled = useMemo(() => {
    /*
      The tooltip surrounding the add button is conditionally displayed.

      It displays if no rows have been selected or if all of the vendors
      are already linked to systems
    */
    if (!anyNewSelectedRows || allRowsLinkedToSystem) {
      return false;
    }

    return true;
  }, [anyNewSelectedRows, allRowsLinkedToSystem]);

  if (!dictionaryService && !isLoadingHealthCheck) {
    router.push(INDEX_ROUTE);
    return null; // this prevents the empty table from flashing
  }

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

  const toolTipText = allRowsLinkedToSystem
    ? `All ${systemText.toLocaleLowerCase()} have already been added`
    : `Select a ${systemText.toLocaleLowerCase()} `;

  const totalSelectSystemsLength = tableInstance
    .getSelectedRowModel()
    .rows.filter((r) => !r.original.linked_system).length;

  const totalFilters =
    tableInstance.getState().columnFilters.length > 0
      ? // @ts-ignore
        (tableInstance
          .getState()
          .columnFilters.filter((c) => c.id === "vendor_id")[0].value
          .length as number)
      : 0;
  return (
    <Flex flex={1} direction="column" overflow="auto">
      <ConfirmationModal
        isOpen={isOpen}
        isCentered
        onCancel={onClose}
        onClose={onClose}
        onConfirm={addVendors}
        title="Confirmation"
        message={`You are about to add ${totalSelectSystemsLength.toLocaleString(
          "en"
        )} ${systemText.toLocaleLowerCase()}${
          totalSelectSystemsLength > 1 ? "s" : ""
        }`}
      />
      <MultipleSystemsFilterModal
        isOpen={isFilterOpen}
        onClose={onCloseFilter}
        tableInstance={tableInstance}
      />
      <TableActionBar>
        <Flex alignItems="center" grow={1}>
          <Box maxW="420px" width="100%">
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={setGlobalFilter}
              placeholder="Search"
            />
          </Box>
          {totalSelectSystemsLength > 0 ? (
            <Text fontWeight="700" fontSize="sm" lineHeight="2" ml={4}>
              {totalSelectSystemsLength.toLocaleString("en")} selected
            </Text>
          ) : null}

          <Tooltip
            label={toolTipText}
            shouldWrapChildren
            placement="top"
            isDisabled={isTooltipDisabled}
          >
            <Button
              onClick={onOpen}
              data-testid="add-multiple-systems-btn"
              size="xs"
              variant="outline"
              disabled={!anyNewSelectedRows}
              ml={4}
            >
              Add
            </Button>
          </Tooltip>
        </Flex>
        <Flex alignItems="center">
          {isTcfEnabled ? (
            // Wrap in a span so it is consistent height with the add button, whose
            // Tooltip wraps a span
            <span>
              <Button
                onClick={onOpenFilter}
                data-testid="filter-multiple-systems-btn"
                size="xs"
                variant="outline"
              >
                Filter{" "}
                {totalFilters > 0 ? (
                  <Tag borderRadius="full" size="sm" ml={2}>
                    {" "}
                    {totalFilters}{" "}
                  </Tag>
                ) : null}
              </Button>
            </span>
          ) : null}
        </Flex>
      </TableActionBar>
      <FidesTableV2<MultipleSystemTable>
        tableInstance={tableInstance}
        rowActionBar={
          <RowSelectionBar<MultipleSystemTable>
            tableInstance={tableInstance}
            selectedRows={totalSelectSystemsLength}
            isOpen={isRowSelectionBarOpen}
          />
        }
      />
      <PaginationBar<MultipleSystemTable>
        tableInstance={tableInstance}
        pageSizes={PAGE_SIZES}
      />
    </Flex>
  );
};

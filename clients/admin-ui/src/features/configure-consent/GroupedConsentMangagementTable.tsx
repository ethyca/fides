/* eslint-disable react/no-unstable-nested-components */
import { Button, Flex } from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getPaginationRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useFeatures } from "common/features";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  GroupCountBadgeCell,
  useClientSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";

import {
  ConsentManagementFilterModal,
  Option,
  useConsentManagementFilters,
} from "~/features/configure-consent/ConsentManagementFilterModal";
import {
  ConsentManagementModal,
  useConsentManagementModal,
} from "~/features/configure-consent/ConsentManagementModal";
import {
  useGetHealthQuery,
  useGetVendorReportQuery,
} from "~/features/plus/plus.slice";
import { Page_SystemSummary_, SystemSummary } from "~/types/api";

type PDGroupedBySystem = {
  systemName: string;
  dataUse: string;
  dataCategories: string[];
  dataSubject: string[];
};

const tableData: PDGroupedBySystem[] = [
  {
    systemName: "ACME 1",
    dataUse: "data use 1",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 1",
    dataUse: "data use 2",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 1",
    dataUse: "data use 3",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 1",
    dataUse: "data use 4",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 1",
    dataUse: "data use 5",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 1",
    dataUse: "data use 6",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },

  {
    systemName: "ACME 2",
    dataUse: "data use 1",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 2",
    dataUse: "data use 2",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 2",
    dataUse: "data use 3",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 2",
    dataUse: "data use 4",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 2",
    dataUse: "data use 5",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 2",
    dataUse: "data use 6",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },

  {
    systemName: "ACME 3",
    dataUse: "data use 1",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 3",
    dataUse: "data use 2",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 3",
    dataUse: "data use 3",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 3",
    dataUse: "data use 4",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 3",
    dataUse: "data use 5",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
  {
    systemName: "ACME 3",
    dataUse: "data use 6",
    dataCategories: ["cat1", " cat 2", "cat 3"],
    dataSubject: ["subject 1", "subject 2", "subject 3"],
  },
];

const columnHelper = createColumnHelper<PDGroupedBySystem>();

const emptyVendorReportResponse: Page_SystemSummary_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};
export const GroupedConsentManagementTable = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const {
    isOpen: isRowModalOpen,
    onOpen: onRowModalOpen,
    onClose: onRowModalClose,
  } = useConsentManagementModal();
  const [systemFidesKey, setSystemFidesKey] = useState<string>();

  const {
    isOpen: isFilterOpen,
    onOpen: onOpenFilter,
    onClose: onCloseFilter,
    resetFilters,
    purposeOptions,
    onPurposeChange,
    dataUseOptions,
    onDataUseChange,
    legalBasisOptions,
    onLegalBasisChange,
    consentCategoryOptions,
    onConsentCategoryChange,
  } = useConsentManagementFilters();

  const [globalFilter, setGlobalFilter] = useState<string>();

  const updateGlobalFilter = (searchTerm: string) => {
    resetPageIndexToDefault();
    setGlobalFilter(searchTerm);
  };

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.systemName, {
        enableGrouping: true,
        id: "systemName",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Vendor" {...props} />,
        meta: {
          maxWidth: "350px",
        },
      }),
      columnHelper.accessor((row) => row.dataUse, {
        id: "dataUse",
        cell: (props) => <BadgeCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.dataCategories, {
        id: "dataCategories",
        cell: (props) => (
          <GroupCountBadgeCell suffix="data uses" value={props.getValue()} />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.dataSubject, {
        id: "dataSubject",
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data subjects"
            expand={true}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data subject" {...props} />
        ),
        meta: {
          width: "175px",
        },
      }),
    ],
    []
  );
  const [grouping, setGrouping] = useState(["systemName"]);

  const tableInstance = useReactTable<PDGroupedBySystem>({
    columns: tcfColumns,
    getPaginationRowModel: getPaginationRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    data: tableData,
    debugTable: true,
    state: {
      expanded: true,
      grouping,
    },
    onGroupingChange: setGrouping,
    getCoreRowModel: getCoreRowModel(),
  });

  const pageProps = useClientSidePagination(tableInstance);

  const onRowClick = (system: SystemSummary) => {
    setSystemFidesKey(system.fides_key);
    onRowModalOpen();
  };

  return (
    <Flex flex={1} direction="column" overflow="auto">
      {grouping}
      {isRowModalOpen && systemFidesKey ? (
        <ConsentManagementModal
          isOpen={isRowModalOpen}
          fidesKey={systemFidesKey}
          onClose={onRowModalClose}
        />
      ) : null}
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
          placeholder="Search"
        />
        <ConsentManagementFilterModal
          isOpen={isFilterOpen}
          isTcfEnabled={isTcfEnabled}
          onClose={onCloseFilter}
          resetFilters={resetFilters}
          purposeOptions={purposeOptions}
          onPurposeChange={onPurposeChange}
          dataUseOptions={dataUseOptions}
          onDataUseChange={onDataUseChange}
          legalBasisOptions={legalBasisOptions}
          onLegalBasisChange={onLegalBasisChange}
          consentCategoryOptions={consentCategoryOptions}
          onConsentCategoryChange={onConsentCategoryChange}
        />
        <Flex alignItems="center">
          <Button
            onClick={onOpenFilter}
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
          >
            Filter
          </Button>
          <Button
            onClick={() => {
              tableInstance.setGrouping(["dataUse"]);
            }}
          >
            Group
          </Button>
        </Flex>
      </TableActionBar>

      <FidesTableV2 tableInstance={tableInstance} onRowClick={onRowClick} />
      <PaginationBar {...pageProps} pageSizes={[5, 10, 15]} />
    </Flex>
  );
};

/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  Flex,
  ChevronDownIcon,
  Menu,
  MenuButton,
  MenuList,
  MenuItemOption,
  Portal,
} from "@fidesui/react";
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
  useServerSidePagination,
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
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  DATAMAP_GROUPING,
  Page_MinimalDatamapReport_,
  MinimalDatamapReport,
} from "~/types/api";
import { useGetMininimalDatamapReportQuery } from "~/features/datamap/datamap.slice";

const columnHelper = createColumnHelper<MinimalDatamapReport>();

const emptyMinimalDatamapReportResponse: Page_MinimalDatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const SYSTEM_NAME_COLUMN_ID = "system_name";
const DATA_USE_COLUMN_ID = "data_use";
const DATA_CATEGORY_COLUMN_ID = "data_categories";
const DATA_SUBJECT_COLUMN_ID = "data_subjects";

export const GroupedConsentManagementTable = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
    resetPageIndexToDefault,
  } = useServerSidePagination();
  const [groupBy, setGroupBy] = useState<DATAMAP_GROUPING>(
    DATAMAP_GROUPING.SYSTEM_DATA_USE
  );

  const onGroupChange = (group: DATAMAP_GROUPING) => {
    setGroupBy(group);
    resetPageIndexToDefault();
  };

  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
  } = useGetMininimalDatamapReportQuery({
    pageIndex,
    pageSize,
    groupBy,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(
    () => datamapReport || emptyMinimalDatamapReportResponse,
    [datamapReport]
  );

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.system_name, {
        enableGrouping: true,
        id: SYSTEM_NAME_COLUMN_ID,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Vendor" {...props} />,
        meta: {
          maxWidth: "350px",
        },
      }),
      columnHelper.accessor((row) => row.data_use, {
        id: DATA_USE_COLUMN_ID,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data uses"
            expand={true}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.data_category, {
        id: DATA_CATEGORY_COLUMN_ID,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data categories"
            expand={true}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.data_subject, {
        id: DATA_SUBJECT_COLUMN_ID,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data subjects"
            expand={false}
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
  const grouping = useMemo(() => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
        return [SYSTEM_NAME_COLUMN_ID];
      }
      case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
        return [DATA_USE_COLUMN_ID];
      }
      case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
        return [DATA_CATEGORY_COLUMN_ID];
      }
    }
  }, [groupBy]);

  const columnOrder = useMemo(() => {
    if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
      return [
        SYSTEM_NAME_COLUMN_ID,
        DATA_USE_COLUMN_ID,
        DATA_CATEGORY_COLUMN_ID,
        DATA_SUBJECT_COLUMN_ID,
      ];
    }
    if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
      return [
        DATA_USE_COLUMN_ID,
        SYSTEM_NAME_COLUMN_ID,
        DATA_CATEGORY_COLUMN_ID,
        DATA_SUBJECT_COLUMN_ID,
      ];
    }
    if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
      return [
        DATA_CATEGORY_COLUMN_ID,
        SYSTEM_NAME_COLUMN_ID,
        DATA_USE_COLUMN_ID,
        DATA_SUBJECT_COLUMN_ID,
      ];
    }
  }, [groupBy]);

  const tableInstance = useReactTable<MinimalDatamapReport>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: tcfColumns,
    manualPagination: true,
    data,
    debugTable: true,
    state: {
      expanded: true,
      grouping,
      columnOrder,
    },
  });

  const getMenuDisplayValue = () => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
        return "system";
      }
      case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
        return "data use";
      }
      case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
        return "data category";
      }
    }
  };

  if (isReportLoading || isLoadingHealthCheck || isReportFetching) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={""}
          setGlobalFilter={() => {}}
          placeholder="Search"
        />
        <Flex alignItems="center">
          <Menu>
            <MenuButton
              as={Button}
              size="xs"
              variant="outline"
              mr={2}
              rightIcon={<ChevronDownIcon />}
            >
              Group by {getMenuDisplayValue()}
            </MenuButton>
            <MenuList zIndex={11}>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.SYSTEM_DATA_USE);
                }}
                isChecked={DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy}
                value={DATAMAP_GROUPING.SYSTEM_DATA_USE}
              >
                System
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.DATA_USE_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_USE_SYSTEM}
              >
                Data use
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM}
              >
                Data category
              </MenuItemOption>
            </MenuList>
          </Menu>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
          >
            Filter
          </Button>
        </Flex>
      </TableActionBar>

      <FidesTableV2<MinimalDatamapReport> tableInstance={tableInstance} />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isReportFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isReportFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </Flex>
  );
};

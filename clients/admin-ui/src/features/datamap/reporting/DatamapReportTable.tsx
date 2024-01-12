/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  ChevronDownIcon,
  Flex,
  Heading,
  Menu,
  MenuButton,
  MenuItemOption,
  MenuList,
  useDisclosure,
} from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  ColumnSettingsModal,
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";

import { getQueryParamsFromList } from "~/features/common/modals/FilterModal";
import { useGetMinimalDatamapReportQuery } from "~/features/datamap/datamap.slice";
import {
  DatamapReportFilterModal,
  useDatamapReportFilters,
} from "~/features/datamap/reporting/DatamapReportFilterModal";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  DATAMAP_GROUPING,
  DatamapReport,
  Page_DatamapReport_,
} from "~/types/api";

const columnHelper = createColumnHelper<DatamapReport>();

const emptyMinimalDatamapReportResponse: Page_DatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

// eslint-disable-next-line @typescript-eslint/naming-convention
enum COLUMN_IDS {
  SYSTEM_NAME = "system_name",
  DATA_USE = "data_use",
  DATA_CATEGORY = "data_categories",
  DATA_SUBJECT = "data_subjects",
  LEGAL_NAME = "legal_name",
  DPO = "dpo",
  LEGAL_BASIS_FOR_PROCESSING = "legal_basis_for_processing",
  ADMINISTRATING_DEPARTMENT = "adminstrating_department",
  COOKIE_MAX_AGE_SECONDS = "cookie_max_age_seconds",
  PRIVACY_POLICY = "privacy_policy",
  LEGAL_ADDRESS = "legal_address",
  COOKIE_REFRESH = "cookie_refresh",
  DATA_SECURITY_PRACTICES = "data_security_practices",
  DATA_SHARED_WITH_THIRD_PARTIES = "DATA_SHARED_WITH_THIRD_PARTIES",
  DATA_STEWARDS = "data_stewards",
  DECLARATION_NAME = "declaration_name",
  DESCRIPTION = "description",
  DOES_INTERNATIONAL_TRANSFERS = "does_internation_transfers",
  DPA_LOCATION = "dpa_location",
  EGRESS = "egress",
  EXEMPT_FROM_PRIVACY_REGULATIONS = "exempt_from_privacy_regulations",
  FEATURES = "features",
  FIDES_KEY = "fides_key",
  FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING = "flexible_legal_basis_for_processing",
  IMPACT_ASSESMENT_LOCATION = "impact_assesment_location",
  INGRESS = "ingress",
  JOINT_CONTROLLER_INFO = "joint_controller_info",
  LEGAL_BASIS_FOR_PROFILING = "legal_basis_for_profiling",
  LEGAL_BASIS_FOR_TRANSFERS = "legal_basis_for_transfers",
  LEGITIMATE_INTEREST_DISCLOSURE_URL = "legitimate_interest_disclosure_url",
  LINK_TO_PROCESSOR_CONTRACT = "link_to_processor_contract",
  PROCESSES_PERSONAL_DATA = "processes_personal_data",
  REASON_FOR_EXEMPTION = "reason_for_exemption",
  REQUIRES_DATA_PROTECTION_ASSESSMENTS = "requires_data_protection_assessments",
  RESPONSIBILITLY = "responsibilitly",
  RETENTION_PERIOD = "retention_period",
  SHARED_CATEGORIES = "shared_categories",
  SPECIAL_CATEGORY_LEGAL_BASIS = "special_category_legal_basis",
  SYSTEM_DEPENDENCIES = "system_dependencies",
  THIRD_COUNTRY_SAFEGUARDS = "third_country_safeguards",
  THIRD_PARTIES = "third_parties",
  USES_COOKIES = "uses_cookies",
  USES_NON_COOKIE_ACCESS = "uses_non_cookie_access",
  USES_PROFILING = "uses_profiling",
}

const getGrouping = (groupBy: DATAMAP_GROUPING) => {
  let grouping: string[] = [];
  switch (groupBy) {
    case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
      grouping = [COLUMN_IDS.SYSTEM_NAME];
      break;
    }
    case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
      grouping = [COLUMN_IDS.DATA_USE];
      break;
    }
    case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
      grouping = [COLUMN_IDS.DATA_CATEGORY];
      break;
    }
    default:
      grouping = [COLUMN_IDS.SYSTEM_NAME];
  }
  return grouping;
};
const getColumnOrder = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder: string[] = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
    columnOrder = [
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  return columnOrder;
};

const getPrefixColumns = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder: string[] = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [COLUMN_IDS.SYSTEM_NAME, COLUMN_IDS.DATA_USE];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [COLUMN_IDS.DATA_USE, COLUMN_IDS.SYSTEM_NAME];
  }
  if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
    columnOrder = [COLUMN_IDS.DATA_CATEGORY, COLUMN_IDS.SYSTEM_NAME];
  }
  return columnOrder;
};

export const DatamapReportTable = () => {
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

  const {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    dataUseOptions,
    onDataUseChange,
    dataCategoriesOptions,
    onDataCategoriesChange,
    dataSubjectOptions,
    onDataSubjectChange,
  } = useDatamapReportFilters();

  const selectedDataUseFilters = useMemo(
    () => getQueryParamsFromList(dataUseOptions, "data_uses"),
    [dataUseOptions]
  );

  const selectedDataCategoriesFilters = useMemo(
    () => getQueryParamsFromList(dataCategoriesOptions, "data_categories"),
    [dataCategoriesOptions]
  );

  const selectedDataSubjectFilters = useMemo(
    () => getQueryParamsFromList(dataSubjectOptions, "data_subjects"),
    [dataSubjectOptions]
  );

  const [groupChangeStarted, setGroupChangeStarted] = useState<boolean>(false);
  const [globalFilter, setGlobalFilter] = useState<string>("");
  const updateGlobalFilter = (searchTerm: string) => {
    resetPageIndexToDefault();
    setGlobalFilter(searchTerm);
  };

  const [groupBy, setGroupBy] = useState<DATAMAP_GROUPING>(
    DATAMAP_GROUPING.SYSTEM_DATA_USE
  );

  const onGroupChange = (group: DATAMAP_GROUPING) => {
    setGroupBy(group);
    setGroupChangeStarted(true);
    resetPageIndexToDefault();
  };

  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
  } = useGetMinimalDatamapReportQuery({
    pageIndex,
    pageSize,
    groupBy,
    search: globalFilter,
    dataUses: selectedDataUseFilters,
    dataSubjects: selectedDataSubjectFilters,
    dataCategories: selectedDataCategoriesFilters,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
    grouping,
    columnOrder,
  } = useMemo(() => {
    const report = datamapReport || emptyMinimalDatamapReportResponse;
    if (groupChangeStarted) {
      setGroupChangeStarted(false);
    }

    /*
      It's important that `grouping` and `columnOrder` are updated
      in this `useMemo`. It makes it so grouping and column order 
      updates are synced up with when the data changes. Otherwise
      the table will update the grouping and column order before 
      the correct data loads.
    */
    return {
      ...report,
      grouping: getGrouping(groupBy),
      columnOrder: getColumnOrder(groupBy),
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const cellWidth = "270px";

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.system_name, {
        enableGrouping: true,
        id: COLUMN_IDS.SYSTEM_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="System" {...props} />,
        meta: {
          width: cellWidth,
          minWidth: cellWidth,
          displayText: "System",
        },
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: COLUMN_IDS.DATA_USE,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data uses"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
        meta: {
          width: cellWidth,
          minWidth: cellWidth,
          displayText: "Data use",
        },
      }),
      columnHelper.accessor((row) => row.data_categories, {
        id: COLUMN_IDS.DATA_CATEGORY,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data categories"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data categories",
        },
      }),
      columnHelper.accessor((row) => row.data_subjects, {
        id: COLUMN_IDS.DATA_SUBJECT,
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
          width: cellWidth,
          displayText: "Data subject",
        },
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: COLUMN_IDS.LEGAL_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Legal name" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Legal name",
        },
      }),
      columnHelper.accessor((row) => row.dpo, {
        id: COLUMN_IDS.DPO,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Data privacy officer" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data privacy officer",
        },
      }),
      columnHelper.accessor((row) => row.legal_basis_for_processing, {
        id: COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Legal basis for processing" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legal basis for processing",
        },
      }),
      columnHelper.accessor((row) => row.administrating_department, {
        id: COLUMN_IDS.ADMINISTRATING_DEPARTMENT,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Administrating department" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Administrating department",
        },
      }),
      columnHelper.accessor((row) => row.cookie_max_age_seconds, {
        id: COLUMN_IDS.COOKIE_MAX_AGE_SECONDS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Cookie max age seconds" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Cookie max age seconds",
        },
      }),
      columnHelper.accessor((row) => row.privacy_policy, {
        id: COLUMN_IDS.PRIVACY_POLICY,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Privacy policy" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Privacy policy",
        },
      }),
      columnHelper.accessor((row) => row.legal_address, {
        id: COLUMN_IDS.LEGAL_ADDRESS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Legal address" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legal address",
        },
      }),
      columnHelper.accessor((row) => row.cookie_refresh, {
        id: COLUMN_IDS.COOKIE_REFRESH,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Cookie refresh"
            table={props.table}
            header={props.header}
            column={props.column}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Cookie refresh",
        },
      }),
      columnHelper.accessor((row) => row.data_security_practices, {
        id: COLUMN_IDS.DATA_SECURITY_PRACTICES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Data security practices" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data security practices",
        },
      }),
      columnHelper.accessor((row) => row.data_shared_with_third_parties, {
        id: COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Data shared with third parties"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data shared with third parties",
        },
      }),
      columnHelper.accessor((row) => row.data_stewards, {
        id: COLUMN_IDS.DATA_STEWARDS,
        cell: (props) => (
          <GroupCountBadgeCell
            expand={false}
            suffix="data stewards"
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data stewards" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data stewards",
        },
      }),
      columnHelper.accessor((row) => row.declaration_name, {
        id: COLUMN_IDS.DECLARATION_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Declaration name" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Declaration name",
        },
      }),
      columnHelper.accessor((row) => row.does_international_transfers, {
        id: COLUMN_IDS.DOES_INTERNATIONAL_TRANSFERS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Does internation transfers" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Does internation transfers",
        },
      }),
      columnHelper.accessor((row) => row.dpa_location, {
        id: COLUMN_IDS.DPA_LOCATION,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="DPA Location" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "DPA Location",
        },
      }),
      columnHelper.accessor((row) => row.egress, {
        id: COLUMN_IDS.EGRESS,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="egress"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Egress" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Egress",
        },
      }),
      columnHelper.accessor((row) => row.exempt_from_privacy_regulations, {
        id: COLUMN_IDS.EXEMPT_FROM_PRIVACY_REGULATIONS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Exempt from privacy regulations"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Exempt from privacy regulations",
        },
      }),
      columnHelper.accessor((row) => row.features, {
        id: COLUMN_IDS.FEATURES,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="features"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Features" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Features",
        },
      }),
      columnHelper.accessor((row) => row.fides_key, {
        id: COLUMN_IDS.FIDES_KEY,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Fides key" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Fides key",
        },
      }),
      columnHelper.accessor((row) => row.flexible_legal_basis_for_processing, {
        id: COLUMN_IDS.FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Flexible legal basis for processing"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Flexible legal basis for processing",
        },
      }),
      columnHelper.accessor((row) => row.impact_assessment_location, {
        id: COLUMN_IDS.IMPACT_ASSESMENT_LOCATION,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Impact assessment location" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Impact assessment location",
        },
      }),
      columnHelper.accessor((row) => row.ingress, {
        id: COLUMN_IDS.INGRESS,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="ingress"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Ingress" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Ingress",
        },
      }),
      columnHelper.accessor((row) => row.joint_controller_info, {
        id: COLUMN_IDS.JOINT_CONTROLLER_INFO,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Joint controller info" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Joint controller info",
        },
      }),
      columnHelper.accessor((row) => row.legal_basis_for_profiling, {
        id: COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="profiles"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Legal basis for profiling" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legal basis for profiling",
        },
      }),
      columnHelper.accessor((row) => row.legal_basis_for_transfers, {
        id: COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="transfers"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Legal basis for transfers" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legal basis for transfers",
        },
      }),
      columnHelper.accessor((row) => row.legitimate_interest_disclosure_url, {
        id: COLUMN_IDS.LEGITIMATE_INTEREST_DISCLOSURE_URL,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Legitimate interest disclosure url"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legitimate interest disclosure url",
        },
      }),
      columnHelper.accessor((row) => row.link_to_processor_contract, {
        id: COLUMN_IDS.LINK_TO_PROCESSOR_CONTRACT,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Link to processor contract" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Link to processor contract",
        },
      }),
      columnHelper.accessor((row) => row.processes_personal_data, {
        id: COLUMN_IDS.PROCESSES_PERSONAL_DATA,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Processes personal data" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Processes personal data",
        },
      }),
      columnHelper.accessor((row) => row.reason_for_exemption, {
        id: COLUMN_IDS.REASON_FOR_EXEMPTION,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Reason for excemption" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Reason for excemption",
        },
      }),
      columnHelper.accessor((row) => row.requires_data_protection_assessments, {
        id: COLUMN_IDS.REQUIRES_DATA_PROTECTION_ASSESSMENTS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Requires data protection assessments"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Requires data protection assessments",
        },
      }),
      columnHelper.accessor((row) => row.responsibility, {
        id: COLUMN_IDS.RESPONSIBILITLY,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="responsibilitlies"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Responsibility" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Responsibility",
        },
      }),
      columnHelper.accessor((row) => row.retention_period, {
        id: COLUMN_IDS.RETENTION_PERIOD,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Retention period" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Retention period",
        },
      }),
      columnHelper.accessor((row) => row.shared_categories, {
        id: COLUMN_IDS.SHARED_CATEGORIES,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="shared categories"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Shared categories" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Shared categories",
        },
      }),
      columnHelper.accessor((row) => row.special_category_legal_basis, {
        id: COLUMN_IDS.SPECIAL_CATEGORY_LEGAL_BASIS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Special category legal basis" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Special category legal basis",
        },
      }),
      columnHelper.accessor((row) => row.system_dependencies, {
        id: COLUMN_IDS.SYSTEM_DEPENDENCIES,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="dependencies"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="System dependencies" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "System dependencies",
        },
      }),
      columnHelper.accessor((row) => row.third_country_safeguards, {
        id: COLUMN_IDS.THIRD_COUNTRY_SAFEGUARDS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Third country safeguards" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Third country safeguards",
        },
      }),
      columnHelper.accessor((row) => row.third_parties, {
        id: COLUMN_IDS.THIRD_PARTIES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Third parties" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Third parties",
        },
      }),
      columnHelper.accessor((row) => row.uses_cookies, {
        id: COLUMN_IDS.USES_COOKIES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Uses cookies" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Uses cookies",
        },
      }),
      columnHelper.accessor((row) => row.uses_non_cookie_access, {
        id: COLUMN_IDS.USES_NON_COOKIE_ACCESS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Uses non cookie access" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Uses non cookie access",
        },
      }),
      columnHelper.accessor((row) => row.uses_profiling, {
        id: COLUMN_IDS.USES_PROFILING,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Uses profiling" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Uses profiling",
        },
      }),
    ],
    []
  );

  const {
    isOpen: isColumnSettingsOpen,
    onOpen: onColumnSettingsOpen,
    onClose: onColumnSettingsClose,
  } = useDisclosure();

  const tableInstance = useReactTable<DatamapReport>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: tcfColumns,
    manualPagination: true,
    data,
    initialState: {
      columnOrder,
    },
    state: {
      expanded: true,
      grouping,
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
      default: {
        return "system";
      }
    }
  };

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Datamap Report
      </Heading>
      <DatamapReportFilterModal
        isOpen={isOpen}
        onClose={onClose}
        resetFilters={resetFilters}
        dataUseOptions={dataUseOptions}
        onDataUseChange={onDataUseChange}
        dataCategoriesOptions={dataCategoriesOptions}
        onDataCategoriesChange={onDataCategoriesChange}
        dataSubjectOptions={dataSubjectOptions}
        onDataSubjectChange={onDataSubjectChange}
      />
      <ColumnSettingsModal<DatamapReport>
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        prefixColumns={getPrefixColumns(groupBy)}
        tableInstance={tableInstance}
      />
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
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
              spinnerPlacement="end"
              isLoading={groupChangeStarted}
              loadingText={`Group by ${getMenuDisplayValue()}`}
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
            </MenuList>
          </Menu>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
            onClick={onColumnSettingsOpen}
            mr={2}
          >
            Edit columns
          </Button>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
            onClick={onOpen}
          >
            Filter
          </Button>
        </Flex>
      </TableActionBar>

      <FidesTableV2<DatamapReport> tableInstance={tableInstance} />
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

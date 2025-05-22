import type { ColumnsType, FilterValue } from "antd/es/table/interface";
import { useFeatures } from "common/features";
import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntLayout as Layout,
  AntRow as Row,
  AntSpace as Space,
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { ADD_MULTIPLE_VENDORS_ROUTE } from "~/features/common/nav/routes";
import {
  selectPurposes,
  useGetPurposesQuery,
} from "~/features/common/purpose.slice";
import AddVendor from "~/features/configure-consent/AddVendor";
import {
  ConsentManagementModal,
  useConsentManagementModal,
} from "~/features/configure-consent/ConsentManagementModal";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { useGetVendorReportQuery } from "~/features/plus/plus.slice";
import { SystemSummary } from "~/types/api";

const { Content } = Layout;
const { Title, Paragraph } = Typography;

// Consent categories for filtering
const CONSENT_CATEGORIES = [
  { text: "Advertising", value: "advertising" },
  { text: "Analytics", value: "analytics" },
  { text: "Functional", value: "functional" },
  { text: "Essential", value: "essential" },
];

// Legal basis options for filtering
const LEGAL_BASIS_OPTIONS = [
  { text: "Consent", value: "Consent" },
  { text: "Legitimate Interest", value: "Legitimate interests" },
];

export const TableMigrationPOC = () => {
  const { tcf: isTcfEnabled, dictionaryService } = useFeatures();
  const router = useRouter();
  const [searchInput, setSearchInput] = useState<string>("");
  const [searchText, setSearchText] = useState<string>("");
  const [pageSize, setPageSize] = useState<number>(25);
  const [pageIndex, setPageIndex] = useState<number>(1);
  const [systemFidesKey, setSystemFidesKey] = useState<string>();
  const [filteredInfo, setFilteredInfo] = useState<
    Record<string, FilterValue | null>
  >({});

  // Load data use options for filtering
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);

  // Load purpose options for filtering
  useGetPurposesQuery();
  const purposeResponse = useAppSelector(selectPurposes);

  // Transform purposes for filtering
  const purposeOptions = useMemo(() => {
    const normalPurposes = Object.entries(purposeResponse.purposes).map(
      ([key, purpose]) => ({
        text: purpose.name,
        value: key,
      }),
    );

    const specialPurposes = Object.entries(
      purposeResponse.special_purposes,
    ).map(([key, purpose]) => ({
      text: purpose.name,
      value: key,
    }));

    return [...normalPurposes, ...specialPurposes];
  }, [purposeResponse]);

  // Transform data uses for filtering
  const dataUseOptions = useMemo(
    () =>
      dataUses.map((dataUse) => ({
        text: dataUse.name || dataUse.fides_key,
        value: dataUse.fides_key,
      })),
    [dataUses],
  );

  const {
    isOpen: isRowModalOpen,
    onOpen: onRowModalOpen,
    onClose: onRowModalClose,
  } = useConsentManagementModal();

  // Format filter parameters for the API
  const formatFilterParams = () => {
    // Format data uses filters as "data_uses=value1&data_uses=value2"
    const dataUsesFilters = ((filteredInfo.data_uses as string[]) || [])
      .map((value) => `data_uses=${encodeURIComponent(value)}`)
      .join("&");

    // Format legal basis filters as "legal_bases=value1&legal_bases=value2"
    const legalBasisFilters = ((filteredInfo.legal_bases as string[]) || [])
      .map((value) => `legal_bases=${encodeURIComponent(value)}`)
      .join("&");

    // Format purpose filters as "purposes=value1&purposes=value2"
    const purposeFilters = ((filteredInfo.tcf_purpose as string[]) || [])
      .map((value) => `purposes=${encodeURIComponent(value)}`)
      .join("&");

    // Format consent category filters as "consent_category=value1&consent_category=value2"
    const consentCategoryFilters = (
      (filteredInfo.consent_categories as string[]) || []
    )
      .map((value) => `consent_category=${encodeURIComponent(value)}`)
      .join("&");

    return {
      dataUses: dataUsesFilters,
      legalBasis: legalBasisFilters,
      purposes: purposeFilters,
      specialPurposes: "",
      consentCategories: consentCategoryFilters,
    };
  };

  const filterParams = formatFilterParams();

  const { data: vendorReport, isLoading } = useGetVendorReportQuery({
    pageIndex,
    pageSize,
    search: searchText,
    ...filterParams,
  });

  const totalRows = vendorReport?.total || 0;
  const items = vendorReport?.items || [];

  // Debounced search handler
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchText(searchInput);
      if (pageIndex !== 1) {
        setPageIndex(1);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput, pageIndex]);

  const onSearchInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchInput(e.target.value);
    },
    [],
  );

  const onSearch = (value: string) => {
    setSearchInput(value);
  };

  const handleTableChange = (
    pagination: any,
    filters: Record<string, FilterValue | null>,
  ) => {
    setPageIndex(pagination.current);
    setPageSize(pagination.pageSize);
    setFilteredInfo(filters);
  };

  const onRowClick = (record: SystemSummary) => {
    setSystemFidesKey(record.fides_key);
    onRowModalOpen();
  };

  const goToAddMultiple = () => {
    router.push(ADD_MULTIPLE_VENDORS_ROUTE);
  };

  // Clear all filters
  const clearAllFilters = () => {
    setFilteredInfo({});
  };

  // Table columns configuration
  const columns: ColumnsType<SystemSummary> = [
    {
      title: "Vendor",
      dataIndex: "name",
      key: "name",
      filteredValue: filteredInfo.name || null,
    },
    ...(isTcfEnabled
      ? [
          {
            title: "TCF purpose",
            dataIndex: "data_uses",
            key: "tcf_purpose",
            render: (count: number) => (
              <Tag>
                {count} {count === 1 ? "purpose" : "purposes"}
              </Tag>
            ),
            filters: purposeOptions,
            filteredValue: filteredInfo.tcf_purpose || null,
          },
          {
            title: "Data use",
            dataIndex: "data_uses",
            key: "data_uses",
            render: (count: number) => (
              <Tag>
                {count} {count === 1 ? "data use" : "data uses"}
              </Tag>
            ),
            filters: dataUseOptions,
            filteredValue: filteredInfo.data_uses || null,
          },
          {
            title: "Legal basis",
            dataIndex: "legal_bases",
            key: "legal_bases",
            render: (count: number) => (
              <Tag>
                {count} {count === 1 ? "basis" : "bases"}
              </Tag>
            ),
            filters: LEGAL_BASIS_OPTIONS,
            filteredValue: filteredInfo.legal_bases || null,
          },
        ]
      : [
          {
            title: "Categories",
            dataIndex: "consent_categories",
            key: "consent_categories",
            render: (count: number) => (
              <Tag>
                {count} {count === 1 ? "category" : "categories"}
              </Tag>
            ),
            filters: CONSENT_CATEGORIES,
            filteredValue: filteredInfo.consent_categories || null,
          },
          {
            title: "Cookies",
            dataIndex: "cookies",
            key: "cookies",
            render: (count: number) => (
              <Tag>
                {count} {count === 1 ? "cookie" : "cookies"}
              </Tag>
            ),
          },
        ]),
  ];

  return (
    <Content className="overflow-auto px-10 py-6">
      <Row>
        <Title>Table Migration POC</Title>
      </Row>
      <Paragraph className="mb-6">
        This is a demonstration of migrating the ConsentManagementTable from
        TanStack Table to Ant Design Table with built-in filtering.
      </Paragraph>

      {isRowModalOpen && systemFidesKey ? (
        <ConsentManagementModal
          isOpen={isRowModalOpen}
          fidesKey={systemFidesKey}
          onClose={onRowModalClose}
        />
      ) : null}

      <Flex justify="space-between" align="center" className="mb-4">
        <Input.Search
          placeholder="Search"
          onSearch={onSearch}
          style={{ width: 300 }}
          value={searchInput}
          onChange={onSearchInputChange}
        />
        <Space size={8}>
          <AddVendor
            buttonLabel="Add vendors"
            onButtonClick={dictionaryService ? goToAddMultiple : undefined}
          />
          <Button onClick={clearAllFilters}>Clear filters</Button>
        </Space>
      </Flex>

      <Table
        dataSource={items}
        columns={columns}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: pageIndex,
          pageSize,
          total: totalRows,
          showSizeChanger: true,
          pageSizeOptions: [25, 50, 100],
        }}
        onChange={handleTableChange}
        onRow={(record) => ({
          onClick: () => onRowClick(record),
          style: { cursor: "pointer" },
        })}
      />
    </Content>
  );
};

export default TableMigrationPOC;

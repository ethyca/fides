import type { ColumnsType } from "antd/es/table";
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
import { useState } from "react";

import { ADD_MULTIPLE_VENDORS_ROUTE } from "~/features/common/nav/routes";
import AddVendor from "~/features/configure-consent/AddVendor";
import {
  ConsentManagementModal,
  useConsentManagementModal,
} from "~/features/configure-consent/ConsentManagementModal";
import { useGetVendorReportQuery } from "~/features/plus/plus.slice";
import { SystemSummary } from "~/types/api";

const { Content } = Layout;
const { Title, Paragraph } = Typography;

export const TableMigrationPOC = () => {
  const { tcf: isTcfEnabled, dictionaryService } = useFeatures();
  const router = useRouter();
  const [searchText, setSearchText] = useState<string>("");
  const [pageSize, setPageSize] = useState<number>(25);
  const [pageIndex, setPageIndex] = useState<number>(1);
  const [systemFidesKey, setSystemFidesKey] = useState<string>();

  const {
    isOpen: isRowModalOpen,
    onOpen: onRowModalOpen,
    onClose: onRowModalClose,
  } = useConsentManagementModal();

  const { data: vendorReport, isLoading } = useGetVendorReportQuery({
    pageIndex,
    pageSize,
    search: searchText,
    dataUses: "",
    legalBasis: "",
    purposes: "",
    specialPurposes: "",
    consentCategories: "",
  });

  const totalRows = vendorReport?.total || 0;
  const items = vendorReport?.items || [];

  const onSearch = (value: string) => {
    setSearchText(value);
    setPageIndex(1);
  };

  const onTableChange = (pagination: any) => {
    setPageIndex(pagination.current);
    setPageSize(pagination.pageSize);
  };

  const onRowClick = (record: SystemSummary) => {
    setSystemFidesKey(record.fides_key);
    onRowModalOpen();
  };

  const goToAddMultiple = () => {
    router.push(ADD_MULTIPLE_VENDORS_ROUTE);
  };

  // Table columns configuration
  const columns: ColumnsType<SystemSummary> = [
    {
      title: "Vendor",
      dataIndex: "name",
      key: "name",
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
        TanStack Table to Ant Design Table.
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
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Space size={8}>
          <AddVendor
            buttonLabel="Add vendors"
            onButtonClick={dictionaryService ? goToAddMultiple : undefined}
          />
          <Button>Filter</Button>
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
        onChange={onTableChange}
        onRow={(record) => ({
          onClick: () => onRowClick(record),
          style: { cursor: "pointer" },
        })}
      />
    </Content>
  );
};

export default TableMigrationPOC;

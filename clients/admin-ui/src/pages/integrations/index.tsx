import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntTable as Table,
  AntTableProps as TableProps,
  AntTag as Tag,
  AntTypography as Typography,
  useDisclosure,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFlags } from "~/features/common/features/features.slice";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import SharedConfigModal from "~/features/integrations/SharedConfigModal";
import { ConnectionConfigurationResponse, ConnectionType } from "~/types/api";

const DEFAULT_PAGE_SIZE = 50;

interface IntegrationTableData extends ConnectionConfigurationResponse {
  integrationTypeInfo: ReturnType<typeof getIntegrationTypeInfo>;
}

const IntegrationListView: NextPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setPage(1);
  };

  const handleTableChange = useCallback(
    (pagination: any) => {
      if (pagination?.current !== page) {
        setPage(pagination.current);
      }
      if (pagination?.pageSize && pagination.pageSize !== pageSize) {
        setPageSize(pagination.pageSize);
      }
    },
    [page, pageSize],
  );

  // DEFER (ENG-675): Remove this once the alpha feature is released
  const { flags } = useFlags();
  const supportedIntegrations = useMemo(() => {
    return SUPPORTED_INTEGRATIONS.filter((integration) => {
      return (
        integration !== ConnectionType.MANUAL_WEBHOOK ||
        flags.alphaNewManualIntegration
      );
    });
  }, [flags.alphaNewManualIntegration]);

  const { data, isLoading } = useGetAllDatastoreConnectionsQuery({
    connection_type: supportedIntegrations,
    size: pageSize,
    page,
    search: searchTerm.trim() || undefined,
  });
  const { items, total } = data ?? {};

  const { onOpen, isOpen, onClose } = useDisclosure();

  const tableData: IntegrationTableData[] = useMemo(
    () =>
      items?.map((integration) => ({
        ...integration,
        integrationTypeInfo: getIntegrationTypeInfo(
          integration.connection_type,
          integration.saas_config?.type,
        ),
      })) ?? [],
    [items],
  );

  const handleManageClick = (integration: ConnectionConfigurationResponse) => {
    router.push(`${INTEGRATION_MANAGEMENT_ROUTE}/${integration.key}`);
  };

  const columns: ColumnsType<IntegrationTableData> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      width: 250,
      render: (name: string | null, record) => (
        <div className="flex items-center gap-3">
          <ConnectionTypeLogo data={record} boxSize="20px" />
          <Typography.Text
            ellipsis={{ tooltip: name || "(No name)" }}
            className="font-semibold"
          >
            {name || "(No name)"}
          </Typography.Text>
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "connection_type",
      key: "connection_type",
      width: 150,
      render: (connectionType) => {
        const typeInfo = getIntegrationTypeInfo(
          connectionType,
          items?.find((item) => item.connection_type === connectionType)
            ?.saas_config?.type,
        );
        return <Tag>{typeInfo.placeholder.name || connectionType}</Tag>;
      },
    },
    {
      title: "Category",
      dataIndex: ["integrationTypeInfo", "category"],
      key: "category",
      width: 150,
      render: (category: ConnectionCategory) => category,
    },
    {
      title: "Capabilities",
      dataIndex: ["integrationTypeInfo", "tags"],
      key: "capabilities",
      width: 300,
      render: (tags: string[]) => (
        <div className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </div>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      width: 100,
      render: (_, record) => (
        <Button
          onClick={() => handleManageClick(record)}
          data-testid={`manage-btn-${record.key}`}
          size="small"
        >
          Manage
        </Button>
      ),
    },
  ];

  const paginationConfig: TableProps<IntegrationTableData>["pagination"] = {
    current: page,
    pageSize,
    total,
    showSizeChanger: true,
    showQuickJumper: false,
    showTotal: (totalItems, range) =>
      `${range[0]}-${range[1]} of ${totalItems} integrations`,
    pageSizeOptions: ["10", "25", "50", "100"],
  };

  const tableLocale = {
    emptyText: searchTerm.trim()
      ? "No integrations match your search"
      : 'You have not configured any integrations. Click "Add Integration" to connect and configure systems now.',
  };

  return (
    <Layout title="Integrations">
      <PageHeader
        heading="Integrations"
        breadcrumbItems={[
          {
            title: "All integrations",
          },
        ]}
        rightContent={
          <Button
            onClick={onOpen}
            data-testid="add-integration-btn"
            type="primary"
          >
            Add integration
          </Button>
        }
      />

      <div className="mb-4 flex items-center justify-between gap-4">
        <DebouncedSearchInput
          placeholder="Search by name..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="max-w-sm"
        />
        <SharedConfigModal />
      </div>

      {isLoading ? (
        <FidesSpinner />
      ) : (
        <Table
          columns={columns}
          dataSource={tableData}
          rowKey="key"
          pagination={paginationConfig}
          loading={isLoading}
          size="small"
          locale={tableLocale}
          bordered
          onRow={(record) => ({
            onClick: () => handleManageClick(record),
          })}
          rowClassName="cursor-pointer"
          onChange={handleTableChange}
          data-testid="integrations-table"
        />
      )}

      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;

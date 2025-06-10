import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntTable as Table,
  AntTableProps as TableProps,
  AntTag as Tag,
  useDisclosure,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { formatDate } from "~/features/common/utils";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import SharedConfigModal from "~/features/integrations/SharedConfigModal";
import { ConnectionConfigurationResponse } from "~/types/api";

const DEFAULT_PAGE_SIZE = 50;

interface IntegrationTableData extends ConnectionConfigurationResponse {
  integrationTypeInfo: ReturnType<typeof getIntegrationTypeInfo>;
}

const IntegrationListView: NextPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [searchTerm, setSearchTerm] = useState("");
  const [connectionTypes, setConnectionTypes] = useState<string[]>([]);
  const router = useRouter();

  // Handle search change and reset page to 1
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setPage(1);
  };

  // Handle connection type filter change and reset page to 1
  const handleConnectionTypeChange = (filters: string[]) => {
    setConnectionTypes(filters);
    setPage(1);
  };

  const { data, isLoading } = useGetAllDatastoreConnectionsQuery({
    connection_type:
      connectionTypes.length > 0
        ? connectionTypes
        : (SUPPORTED_INTEGRATIONS as string[]),
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
        ),
      })) ?? [],
    [items],
  );

  const handleManageClick = (integration: ConnectionConfigurationResponse) => {
    router.push(`${INTEGRATION_MANAGEMENT_ROUTE}/${integration.key}`);
  };

  const formatLastConnection = (
    lastTestTimestamp?: string | null,
    lastTestSucceeded?: boolean | null,
  ) => {
    if (!lastTestTimestamp) {
      return "-";
    }

    const formattedDate = formatDate(lastTestTimestamp);

    if (lastTestSucceeded === true) {
      return (
        <span style={{ color: palette.FIDESUI_SUCCESS_TEXT }}>
          ✓ {formattedDate}
        </span>
      );
    }
    if (lastTestSucceeded === false) {
      return (
        <span style={{ color: palette.FIDESUI_ERROR_TEXT }}>
          ✗ {formattedDate}
        </span>
      );
    }

    return formattedDate;
  };

  // Get available connection types for filters from supported integrations
  const availableConnectionTypes = useMemo(() => {
    return SUPPORTED_INTEGRATIONS.map((type) => ({
      text: getIntegrationTypeInfo(type).placeholder.name || type,
      value: type,
    }));
  }, []);

  const columns: ColumnsType<IntegrationTableData> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string | null, record) => (
        <div className="flex items-center gap-3">
          <ConnectionTypeLogo data={record} boxSize="20px" />
          <span className="font-semibold">{name || "(No name)"}</span>
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "connection_type",
      key: "connection_type",
      filters: availableConnectionTypes,
      filteredValue: connectionTypes,
      filterMultiple: true,
      filterSearch: true,
      onFilter: () => true, // Server-side filtering
      render: (connectionType) => {
        const typeInfo = getIntegrationTypeInfo(connectionType);
        return <Tag>{typeInfo.placeholder.name || connectionType}</Tag>;
      },
    },
    {
      title: "Category",
      dataIndex: ["integrationTypeInfo", "category"],
      key: "category",
      render: (category: ConnectionCategory) => category,
    },
    {
      title: "Capabilities",
      dataIndex: ["integrationTypeInfo", "tags"],
      key: "capabilities",
      render: (tags: string[]) => (
        <div className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </div>
      ),
    },
    {
      title: "Last Connection",
      dataIndex: "last_test_timestamp",
      key: "last_connection",
      render: (lastTestTimestamp, record) =>
        formatLastConnection(lastTestTimestamp, record.last_test_succeeded),
    },
    {
      title: "Actions",
      key: "actions",
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
          allowClear
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
          scroll={{ x: "max-content" }}
          size="small"
          locale={tableLocale}
          bordered
          onRow={(record) => ({
            onClick: () => handleManageClick(record),
          })}
          rowClassName="cursor-pointer"
          onChange={(pagination, filters) => {
            // Handle pagination changes
            if (pagination?.current) {
              setPage(pagination.current);
            }
            if (pagination?.pageSize && pagination.pageSize !== pageSize) {
              setPageSize(pagination.pageSize);
            }

            // Handle filter changes - only when they actually change
            const connectionTypeFilters = filters?.connection_type as
              | string[]
              | undefined;
            if (connectionTypeFilters !== undefined) {
              // Handle the case where filters might be null (when cleared)
              const newFilters = connectionTypeFilters || [];
              const currentFilters = connectionTypes || [];

              // Check if filters actually changed (create copies to avoid mutating readonly arrays)
              const filtersChanged =
                JSON.stringify([...newFilters].sort()) !==
                JSON.stringify([...currentFilters].sort());
              if (filtersChanged) {
                handleConnectionTypeChange(newFilters);
              }
            }
          }}
        />
      )}

      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;

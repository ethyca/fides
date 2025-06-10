import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntInput as Input,
  AntTable as Table,
  AntTableProps as TableProps,
  AntTag as Tag,
  useDisclosure,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useMemo, useState } from "react";

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
  const router = useRouter();

  const { data, isLoading } = useGetAllDatastoreConnectionsQuery({
    connection_type: SUPPORTED_INTEGRATIONS,
    size: pageSize,
    page,
  });
  const { items } = data ?? {};

  const { onOpen, isOpen, onClose } = useDisclosure();

  const allTableData: IntegrationTableData[] = useMemo(
    () =>
      items?.map((integration) => ({
        ...integration,
        integrationTypeInfo: getIntegrationTypeInfo(
          integration.connection_type,
        ),
      })) ?? [],
    [items],
  );

  // Filter data based on search term
  const tableData = useMemo(() => {
    if (!searchTerm.trim()) {
      return allTableData;
    }

    const lowerSearchTerm = searchTerm.toLowerCase();
    return allTableData.filter((integration) => {
      const name = (integration.name || "").toLowerCase();

      return name.includes(lowerSearchTerm);
    });
  }, [allTableData, searchTerm]);

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

  // Get unique values for filters
  const connectionTypes = useMemo(() => {
    const types = new Set(tableData.map((item) => item.connection_type));
    return Array.from(types).map((type) => ({
      text: getIntegrationTypeInfo(type).placeholder.name || type,
      value: type,
    }));
  }, [tableData]);

  const categories = useMemo(() => {
    const cats = new Set(
      tableData.map((item) => item.integrationTypeInfo.category),
    );
    return Array.from(cats).map((category) => ({
      text: category,
      value: category,
    }));
  }, [tableData]);

  const capabilities = useMemo(() => {
    const caps = new Set(
      tableData.flatMap((item) => item.integrationTypeInfo.tags),
    );
    return Array.from(caps).map((capability) => ({
      text: capability,
      value: capability,
    }));
  }, [tableData]);

  const columns: ColumnsType<IntegrationTableData> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string | null, record) => (
        <div className="flex items-center gap-3">
          <ConnectionTypeLogo data={record} boxSize="32px" />
          <span className="font-medium">{name || "(No name)"}</span>
        </div>
      ),
      sorter: (a, b) => (a.name || "").localeCompare(b.name || ""),
    },
    {
      title: "Connection",
      dataIndex: "connection_type",
      key: "connection_type",
      filters: connectionTypes,
      filterMultiple: true,
      onFilter: (value, record) => record.connection_type === value,
      render: (connectionType) => {
        const typeInfo = getIntegrationTypeInfo(connectionType);
        return typeInfo.placeholder.name || connectionType;
      },
    },
    {
      title: "Category",
      dataIndex: ["integrationTypeInfo", "category"],
      key: "category",
      filters: categories,
      filterMultiple: true,
      onFilter: (value, record) =>
        record.integrationTypeInfo.category === value,
      render: (category: ConnectionCategory) => category,
    },
    {
      title: "Capabilities",
      dataIndex: ["integrationTypeInfo", "tags"],
      key: "capabilities",
      filters: capabilities,
      filterMultiple: true,
      onFilter: (value, record) =>
        record.integrationTypeInfo.tags.includes(value as string),
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
      sorter: (a, b) => {
        const aTime = a.last_test_timestamp
          ? new Date(a.last_test_timestamp).getTime()
          : 0;
        const bTime = b.last_test_timestamp
          ? new Date(b.last_test_timestamp).getTime()
          : 0;
        return aTime - bTime;
      },
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
    total: tableData.length,
    showSizeChanger: true,
    showQuickJumper: false,
    showTotal: (totalItems, range) =>
      `${range[0]}-${range[1]} of ${totalItems} integrations`,
    onChange: (newPage, newPageSize) => {
      setPage(newPage);
      if (newPageSize !== pageSize) {
        setPageSize(newPageSize);
      }
    },
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
          <Button onClick={onOpen} data-testid="add-integration-btn">
            Add integration
          </Button>
        }
      />

      <div className="mb-4 flex items-center justify-between gap-4">
        <Input.Search
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onSearch={setSearchTerm}
          className="max-w-sm"
          allowClear
          enterButton
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
          size="middle"
          locale={tableLocale}
        />
      )}

      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;

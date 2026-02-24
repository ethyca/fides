import {
  Button,
  ColumnsType,
  CUSTOM_TAG_COLOR,
  Icons,
  Table,
  TableProps,
  Tag,
  Tooltip,
  Typography,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFlags } from "~/features/common/features";
import { useConnectionLogo } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  EDIT_SYSTEM_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { ListExpandableCell } from "~/features/common/table/cells/ListExpandableCell";
import { formatDate } from "~/features/common/utils";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import SharedConfigModal from "~/features/integrations/SharedConfigModal";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

const isCustomIntegration = (
  record: ConnectionConfigurationResponse,
  connectionTypes: ConnectionSystemTypeMap[],
): boolean => {
  const identifier =
    record.connection_type === ConnectionType.SAAS
      ? record.saas_config?.type
      : record.connection_type;
  const connectionType = connectionTypes.find(
    (ct) => ct.identifier === identifier,
  );
  return connectionType?.custom ?? false;
};

const DEFAULT_PAGE_SIZE = 50;

interface IntegrationTableData extends ConnectionConfigurationResponse {
  integrationTypeInfo: ReturnType<typeof getIntegrationTypeInfo>;
}

// Component to render logo for each integration row
const IntegrationLogo = ({
  integration,
}: {
  integration: ConnectionConfigurationResponse;
}) => {
  const logoData = useConnectionLogo(integration);
  return <ConnectionTypeLogo data={logoData} size={20} />;
};

const IntegrationListView: NextPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();

  const {
    flags: { newIntegrationManagement },
  } = useFlags();

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

  // Fetch connection types for SAAS integration generation
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = useMemo(
    () => connectionTypesData?.items || [],
    [connectionTypesData],
  );

  // Filter connection types based on the new integration management flag
  const connectionTypesToQuery = useMemo(() => {
    if (newIntegrationManagement) {
      // Show all integrations (including SaaS) when the flag is enabled
      return SUPPORTED_INTEGRATIONS;
    }
    // Hide SaaS integrations when the flag is disabled
    return SUPPORTED_INTEGRATIONS.filter(
      (type) => type !== ConnectionType.SAAS,
    );
  }, [newIntegrationManagement]);

  const { data, isLoading, error } = useGetAllDatastoreConnectionsQuery({
    connection_type: connectionTypesToQuery,
    size: pageSize,
    page,
    search: searchTerm.trim() || undefined,
  });
  const { items } = data ?? {};

  const { onOpen, isOpen, onClose } = useDisclosure();

  const tableData: IntegrationTableData[] = useMemo(
    () =>
      items?.map((integration) => ({
        ...integration,
        integrationTypeInfo: getIntegrationTypeInfo(
          integration.connection_type,
          integration.saas_config?.type,
          connectionTypes,
        ),
      })) ?? [],
    [items, connectionTypes],
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
          <IntegrationLogo integration={record} />
          <LinkCell href={`${INTEGRATION_MANAGEMENT_ROUTE}/${record.key}`}>
            {name || "(No name)"}
          </LinkCell>
          {isCustomIntegration(record, connectionTypes) && (
            <Tooltip title="Custom integration">
              <Icons.SettingsCheck size={16} />
            </Tooltip>
          )}
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "connection_type",
      key: "connection_type",
      width: 150,
      render: (connectionType, record) => {
        const typeInfo = getIntegrationTypeInfo(
          connectionType,
          record.saas_config?.type,
          connectionTypes,
        );
        return typeInfo.placeholder.name || connectionType;
      },
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
      title: "Connection status",
      key: "connection_status",
      width: 150,
      render: (_, record) => {
        const getConnectionStatus = () => {
          if (
            record.last_test_timestamp === null ||
            record.last_test_timestamp === undefined
          ) {
            return { status: "Untested", color: CUSTOM_TAG_COLOR.DEFAULT };
          }
          if (record.last_test_succeeded === true) {
            return { status: "Healthy", color: CUSTOM_TAG_COLOR.SUCCESS };
          }
          if (record.last_test_succeeded === false) {
            return { status: "Failed", color: CUSTOM_TAG_COLOR.ERROR };
          }
          return { status: "Untested", color: CUSTOM_TAG_COLOR.DEFAULT };
        };

        const { status, color } = getConnectionStatus();
        const tooltipText = record.last_test_timestamp
          ? `Last connection: ${formatDate(record.last_test_timestamp)}`
          : "The connection has not been tested";

        return (
          <Tooltip title={tooltipText}>
            <Tag color={color}>{status}</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: "Linked system",
      dataIndex: "linked_systems",
      key: "linked_systems",
      width: 150,
      render: (_, { linked_systems }) => {
        if (!linked_systems) {
          return null;
        }
        if (linked_systems?.length === 1) {
          return (
            <Typography.Link
              href={`${EDIT_SYSTEM_ROUTE.replace("[id]", linked_systems[0].fides_key)}`}
              variant="primary"
              ellipsis
            >
              {linked_systems[0].name}
            </Typography.Link>
          );
        }
        return (
          <ListExpandableCell
            values={linked_systems.map((link) => link.name ?? link.fides_key)}
            valueSuffix="systems"
          />
        );
      },
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
    total: data?.total,
    showQuickJumper: false,
    showTotal: (totalItems, range) =>
      `${range[0]}-${range[1]} of ${totalItems} integrations`,
    pageSizeOptions: ["10", "25", "50", "100"],
  };

  const tableLocale = {
    emptyText: searchTerm.trim() ? (
      "No integrations match your search"
    ) : (
      <div data-testid="empty-state">
        You have not configured any integrations. Click &quot;Add
        Integration&quot; to connect and configure systems now.
      </div>
    ),
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your integrations"
      />
    );
  }

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

      <Table
        columns={columns}
        dataSource={tableData}
        rowKey="key"
        pagination={paginationConfig}
        loading={isLoading}
        size="small"
        locale={tableLocale}
        bordered
        onChange={handleTableChange}
        data-testid="integrations-table"
      />

      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;

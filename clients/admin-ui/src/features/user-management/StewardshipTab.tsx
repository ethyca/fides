import { skipToken } from "@reduxjs/toolkit/query";
import {
  Card,
  ColumnsType,
  Empty,
  Flex,
  Table,
  Tag,
  Typography,
} from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import { RouterLink } from "~/features/common/nav/RouterLink";
import {
  EDIT_SYSTEM_ROUTE,
  INTEGRATION_DETAIL_ROUTE,
} from "~/features/common/nav/routes";
import { EditableMonitorConfig, System } from "~/types/api";

import {
  selectActiveUserId,
  useGetUserManagedSystemsQuery,
  useGetUserMonitorsQuery,
} from "./user-management.slice";

const { Title, Text } = Typography;

const MONITOR_STEWARDSHIP_DOCS_URL =
  "https://ethyca.com/docs/data-mapping/guides/assigning-monitor-stewards";

const StewardshipTab = () => {
  const activeUserId = useAppSelector(selectActiveUserId);

  const { data: systems = [], isLoading: systemsLoading } =
    useGetUserManagedSystemsQuery(activeUserId ?? skipToken);
  const { data: monitors = [], isLoading: monitorsLoading } =
    useGetUserMonitorsQuery(activeUserId ? { id: activeUserId } : skipToken);

  const systemColumns: ColumnsType<System> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string | undefined, record) => (
        <RouterLink href={EDIT_SYSTEM_ROUTE.replace("[id]", record.fides_key)}>
          {name ?? record.fides_key}
        </RouterLink>
      ),
    },
    {
      title: "Fides key",
      dataIndex: "fides_key",
      key: "fides_key",
      render: (key: string) => <Text type="secondary">{key}</Text>,
    },
  ];

  const monitorColumns: ColumnsType<EditableMonitorConfig> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Integration",
      dataIndex: "connection_config_key",
      key: "connection_config_key",
      render: (key: string) => (
        <RouterLink href={INTEGRATION_DETAIL_ROUTE.replace("[id]", key)}>
          {key}
        </RouterLink>
      ),
    },
    {
      title: "Status",
      dataIndex: "enabled",
      key: "enabled",
      width: 120,
      render: (enabled: boolean | null | undefined) =>
        enabled ? (
          <Tag color="success">Enabled</Tag>
        ) : (
          <Tag color="marble">Disabled</Tag>
        ),
    },
  ];

  return (
    <Flex
      vertical
      gap="large"
      className="w-full p-4 md:w-4/5 xl:w-3/4"
      data-testid="stewardship-tab"
    >
      <Card
        size="small"
        title={
          <Title level={5} className="!mb-0">
            Systems ({systems.length})
          </Title>
        }
        data-testid="stewardship-systems-card"
      >
        <Text type="secondary" className="mb-3 block">
          Systems where this user is assigned as a data steward.
        </Text>
        <Table<System>
          size="small"
          rowKey="fides_key"
          loading={systemsLoading}
          dataSource={systems}
          columns={systemColumns}
          pagination={false}
          locale={{
            emptyText: <Empty description="No assigned systems" />,
          }}
          onRow={(record) =>
            ({
              "data-testid": `stewardship-system-row-${record.fides_key}`,
            }) as React.HTMLAttributes<HTMLTableRowElement>
          }
        />
      </Card>

      <Card
        size="small"
        title={
          <Title level={5} className="!mb-0">
            Monitors ({monitors.length})
          </Title>
        }
        data-testid="stewardship-monitors-card"
      >
        <Text type="secondary" className="mb-3 block">
          Discovery monitors where this user is assigned as a steward. To change
          which monitors a steward is assigned to, see the{" "}
          <DocsLink href={MONITOR_STEWARDSHIP_DOCS_URL}>documentation</DocsLink>
          .
        </Text>
        <Table<EditableMonitorConfig>
          size="small"
          rowKey={(record) => record.key ?? record.name}
          loading={monitorsLoading}
          dataSource={monitors}
          columns={monitorColumns}
          pagination={false}
          locale={{
            emptyText: <Empty description="No assigned monitors" />,
          }}
          onRow={(record) =>
            ({
              "data-testid": `stewardship-monitor-row-${record.key ?? record.name}`,
            }) as React.HTMLAttributes<HTMLTableRowElement>
          }
        />
      </Card>
    </Flex>
  );
};

export default StewardshipTab;

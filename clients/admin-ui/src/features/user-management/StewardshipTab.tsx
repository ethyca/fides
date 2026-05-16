import {
  Card,
  ColumnsType,
  Empty,
  Space,
  Table,
  Tag,
  Typography,
} from "fidesui";
import NextLink from "next/link";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import {
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import { EditableMonitorConfig, System } from "~/types/api";

import {
  selectActiveUserId,
  useGetUserManagedSystemsQuery,
  useGetUserMonitorsQuery,
} from "./user-management.slice";

const { Title, Text } = Typography;

const StewardshipTab = () => {
  const activeUserId = useAppSelector(selectActiveUserId);

  const { data: systems = [], isLoading: systemsLoading } =
    useGetUserManagedSystemsQuery(activeUserId as string, {
      skip: !activeUserId,
    });
  const { data: monitors = [], isLoading: monitorsLoading } =
    useGetUserMonitorsQuery(
      { id: activeUserId as string },
      { skip: !activeUserId },
    );

  const systemColumns: ColumnsType<System> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string | undefined, record) => (
        <NextLink href={`${SYSTEM_ROUTE}/configure/${record.fides_key}`}>
          {name ?? record.fides_key}
        </NextLink>
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
        <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/${key}`}>
          {key}
        </NextLink>
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
    <Space
      direction="vertical"
      size="large"
      className="w-full p-4 md:w-[80%] xl:w-3/4"
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
          Discovery monitors where this user is assigned as a steward.
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
    </Space>
  );
};

export default StewardshipTab;

import {
  AntColumnsType as ColumnsType,
  AntTypography as Typography,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import MonitorConfigActionsCell from "~/features/integrations/configure-monitor/MonitorConfigActionsCell";
import MonitorStatusCell from "~/features/integrations/configure-monitor/MonitorStatusCell";
import {
  ConnectionConfigurationResponse,
  MonitorConfig,
  PrivacyNoticeRegion,
  WebsiteSchema,
} from "~/types/api";

import { MonitorConfigEnableCell } from "../configure-monitor/MonitorConfigEnableCell";

const { Text } = Typography;

enum MonitorConfigColumnKeys {
  NAME = "name",
  PROJECTS = "projects",
  SOURCE_URL = "source_url",
  FREQUENCY = "execution_frequency",
  MONITOR_STATUS = "monitor_status",
  REGIONS = "regions",
  STATUS = "status",
  ACTION = "action",
}

interface UseMonitorConfigTableConfig {
  integration: ConnectionConfigurationResponse;
  isWebsiteMonitor: boolean;
  onEditMonitor: (monitor: MonitorConfig) => void;
}

export const useMonitorConfigTable = ({
  integration,
  isWebsiteMonitor,
  onEditMonitor,
}: UseMonitorConfigTableConfig) => {
  const tableState = useTableState<MonitorConfigColumnKeys>();

  const { pageIndex, pageSize } = tableState;

  const {
    isLoading,
    isFetching,
    data: response,
  } = useGetMonitorsByIntegrationQuery({
    page: pageIndex,
    size: pageSize,
    connection_config_key: integration.key,
  });

  const antTableConfig = useMemo(
    () => ({
      enableSelection: false,
      getRowKey: (record: MonitorConfig) => record.key ?? record.name,
      isLoading,
      isFetching,
      dataSource: response?.items ?? [],
      totalRows: response?.total ?? 0,
    }),
    [isLoading, isFetching, response?.items, response?.total],
  );

  const antTable = useAntTable<MonitorConfig, MonitorConfigColumnKeys>(
    tableState,
    antTableConfig,
  );

  const columns: ColumnsType<MonitorConfig> = useMemo(() => {
    const nameColumn = {
      title: "Name",
      dataIndex: MonitorConfigColumnKeys.NAME,
      key: MonitorConfigColumnKeys.NAME,
      render: (name: string) => (
        <Text ellipsis={{ tooltip: name }} style={{ maxWidth: 150 }}>
          {name}
        </Text>
      ),
      fixed: "left" as const,
    };

    const scopeColumn = {
      title: "Scope",
      dataIndex: MonitorConfigColumnKeys.PROJECTS,
      key: MonitorConfigColumnKeys.PROJECTS,
      render: (_: unknown, record: MonitorConfig) => {
        const databases = record.databases ?? [];
        if (databases.length === 0) {
          return "All projects";
        }
        return `${databases.length} ${databases.length === 1 ? "Project" : "Projects"}`;
      },
    };

    const sourceUrlColumn = {
      title: "Source URL",
      dataIndex: MonitorConfigColumnKeys.SOURCE_URL,
      key: MonitorConfigColumnKeys.SOURCE_URL,
      render: () => {
        const secrets = integration.secrets as WebsiteSchema | null;
        return (
          <Text ellipsis={{ tooltip: secrets?.url }} style={{ maxWidth: 150 }}>
            {secrets?.url ?? "Not scheduled"}
          </Text>
        );
      },
    };

    const scanFrequencyColumn = {
      title: "Scan frequency",
      dataIndex: MonitorConfigColumnKeys.FREQUENCY,
      key: MonitorConfigColumnKeys.FREQUENCY,
      render: (frequency: string | undefined) => frequency ?? "Not scheduled",
    };

    const lastScanColumn = {
      title: "Scan status",
      key: MonitorConfigColumnKeys.MONITOR_STATUS,
      render: (_: unknown, record: MonitorConfig) => (
        <MonitorStatusCell monitor={record} />
      ),
    };

    const regionsColumn = {
      title: "Regions",
      dataIndex: MonitorConfigColumnKeys.REGIONS,
      key: MonitorConfigColumnKeys.REGIONS,
      render: (_: unknown, record: MonitorConfig) => {
        const locations =
          record.datasource_params &&
          "locations" in record.datasource_params &&
          Array.isArray(record.datasource_params.locations)
            ? record.datasource_params.locations
            : [];

        if (locations.length === 0) {
          return "No regions selected";
        }

        const formattedLocations = locations
          .map((location) => {
            const isoEntry = isoStringToEntry(location);

            // Early return if we have a valid ISO entry to avoid problematic enum navigation
            if (isoEntry) {
              return formatIsoLocation({ isoEntry });
            }

            /**
             * regionCode and regionRecord are the result of navigating enums that should be deprecated.
             * if the backend decides to maintain a list of values for the frontend to use, a less convoluted
             * method should be used
             */
            const regionCode = Object.entries(PrivacyNoticeRegion).find(
              ([, region]) => region === location,
            );

            const regionRecord =
              regionCode &&
              PRIVACY_NOTICE_REGION_RECORD[
                regionCode[1]
              ]; /* regionCode[1] refers to enum value that is the key for the region records enum (enum-ception) */

            return regionRecord;
          })
          .join(", ");

        return (
          <Text
            ellipsis={{ tooltip: formattedLocations }}
            style={{ maxWidth: 150 }}
          >
            {formattedLocations}
          </Text>
        );
      },
    };

    const statusColumn = {
      title: "Status",
      dataIndex: MonitorConfigColumnKeys.STATUS,
      key: MonitorConfigColumnKeys.STATUS,
      width: 100,
      render: (_: unknown, record: MonitorConfig) => (
        <MonitorConfigEnableCell record={record} />
      ),
    };

    const actionsColumn = {
      title: "Actions",
      key: MonitorConfigColumnKeys.ACTION,
      width: 100,
      render: (_: unknown, record: MonitorConfig) => (
        <MonitorConfigActionsCell
          onEditClick={() => onEditMonitor(record)}
          isWebsiteMonitor={isWebsiteMonitor}
          monitorId={record.key}
        />
      ),
      fixed: "right" as const,
    };

    if (isWebsiteMonitor) {
      return [
        nameColumn,
        sourceUrlColumn,
        scanFrequencyColumn,
        regionsColumn,
        lastScanColumn,
        statusColumn,
        actionsColumn,
      ];
    }

    return [
      nameColumn,
      scopeColumn,
      scanFrequencyColumn,
      lastScanColumn,
      statusColumn,
      actionsColumn,
    ];
  }, [integration.secrets, isWebsiteMonitor, onEditMonitor]);

  return {
    // Table state and data
    columns,
    monitors: response?.items ?? [],
    isLoading,
    isFetching,
    totalRows: response?.total ?? 0,

    // Ant Design table integration
    tableProps: antTable.tableProps,

    // Utilities
    hasData: !!response?.items?.length,
  };
};

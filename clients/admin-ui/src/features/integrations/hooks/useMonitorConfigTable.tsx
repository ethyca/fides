import { ColumnsType, formatIsoLocation, isoStringToEntry } from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { EllipsisCell } from "~/features/common/table/cells/EllipsisCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { pluralize } from "~/features/common/utils";
import {
  useGetIdentityProviderMonitorsQuery,
  useGetMonitorsByIntegrationQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import MonitorConfigActionsCell from "~/features/integrations/configure-monitor/MonitorConfigActionsCell";
import MonitorStatusCell from "~/features/integrations/configure-monitor/MonitorStatusCell";
import {
  ConnectionConfigurationResponse,
  ConnectionType,
  EditableMonitorConfig,
  MonitorConfig,
  PrivacyNoticeRegion,
  WebsiteSchema,
} from "~/types/api";

import { MonitorConfigEnableCell } from "../configure-monitor/MonitorConfigEnableCell";

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
  onEditMonitor: (monitor: EditableMonitorConfig) => void;
}

export const useMonitorConfigTable = ({
  integration,
  isWebsiteMonitor,
  onEditMonitor,
}: UseMonitorConfigTableConfig) => {
  const tableState = useTableState<MonitorConfigColumnKeys>();

  const { pageIndex, pageSize } = tableState;

  const isOktaIntegration = integration.connection_type === ConnectionType.OKTA;

  // Use Identity Provider Monitor endpoint for Okta, otherwise use regular endpoint
  const regularMonitorsQuery = useGetMonitorsByIntegrationQuery(
    {
      page: pageIndex,
      size: pageSize,
      connection_config_key: integration.key,
    },
    {
      skip: isOktaIntegration,
    },
  );

  const oktaMonitorsQuery = useGetIdentityProviderMonitorsQuery(
    {
      page: pageIndex,
      size: pageSize,
      connection_config_key: integration.key,
    },
    {
      skip: !isOktaIntegration,
    },
  );

  const {
    isLoading,
    isFetching,
    data: response,
  } = isOktaIntegration ? oktaMonitorsQuery : regularMonitorsQuery;

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
    const nameColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Name",
      dataIndex: MonitorConfigColumnKeys.NAME,
      key: MonitorConfigColumnKeys.NAME,
      render: (_, { name }) => (
        <EllipsisCell style={{ maxWidth: 150 }}>{name}</EllipsisCell>
      ),
      fixed: "left" as const,
    };

    const scopeColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Scope",
      dataIndex: MonitorConfigColumnKeys.PROJECTS,
      key: MonitorConfigColumnKeys.PROJECTS,
      render: (_, record) => {
        const databases = record.databases ?? [];
        if (databases.length === 0) {
          return "All projects";
        }
        return `${databases.length} ${pluralize(databases.length, "project", "projects")}`;
      },
    };

    const sourceUrlColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Source URL",
      dataIndex: MonitorConfigColumnKeys.SOURCE_URL,
      key: MonitorConfigColumnKeys.SOURCE_URL,
      render: () => {
        const secrets = integration.secrets as WebsiteSchema | null;
        return (
          <EllipsisCell style={{ maxWidth: 150 }}>
            {secrets?.url ?? "Not scheduled"}
          </EllipsisCell>
        );
      },
    };

    const scanFrequencyColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Scan frequency",
      dataIndex: MonitorConfigColumnKeys.FREQUENCY,
      key: MonitorConfigColumnKeys.FREQUENCY,
      render: (_, { execution_frequency }) =>
        execution_frequency ?? "Not scheduled",
    };

    const lastScanColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Scan status",
      key: MonitorConfigColumnKeys.MONITOR_STATUS,
      render: (_: unknown, record) => <MonitorStatusCell monitor={record} />,
    };

    const regionsColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Regions",
      dataIndex: MonitorConfigColumnKeys.REGIONS,
      key: MonitorConfigColumnKeys.REGIONS,
      render: (_: unknown, record) => {
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
          <EllipsisCell style={{ maxWidth: 150 }}>
            {formattedLocations}
          </EllipsisCell>
        );
      },
    };

    const statusColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Status",
      dataIndex: MonitorConfigColumnKeys.STATUS,
      key: MonitorConfigColumnKeys.STATUS,
      width: 100,
      render: (_: unknown, record) => (
        <MonitorConfigEnableCell record={record} />
      ),
    };

    const actionsColumn: ColumnsType<MonitorConfig>[number] = {
      title: "Actions",
      key: MonitorConfigColumnKeys.ACTION,
      width: 100,
      render: (_: unknown, { stewards, ...data }) => (
        <MonitorConfigActionsCell
          onEditClick={() =>
            onEditMonitor({ ...data, stewards: stewards?.map(({ id }) => id) })
          }
          isWebsiteMonitor={isWebsiteMonitor}
          isOktaMonitor={isOktaIntegration}
          monitorId={data.key}
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
  }, [integration.secrets, isWebsiteMonitor, onEditMonitor, isOktaIntegration]);

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

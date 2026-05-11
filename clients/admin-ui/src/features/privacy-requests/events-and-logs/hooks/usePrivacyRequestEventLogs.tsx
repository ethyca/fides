import { useMemo } from "react";

import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import {
  connectionLogoFromConfiguration,
  connectionLogoFromSystemType,
} from "~/features/datastore-connections/ConnectionTypeLogo";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import {
  hasAwaitingProcessing,
  hasPolling,
  hasSkippedEntry,
  hasUnresolvedError,
} from "~/features/privacy-requests/events-and-logs/helpers";
import {
  humanizeIdentifier,
  systemEventIcon,
} from "~/features/privacy-requests/events-and-logs/timelineDisplay";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  ExecutionLogStatus,
  PrivacyRequestResults,
} from "~/features/privacy-requests/types";
import { ConnectionType } from "~/types/api";
import type {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
} from "~/types/api";

/**
 * Hook for processing privacy request event logs.
 *
 * When taskStatusByDataset is provided, task statuses are read directly from
 * the RequestTask.status field (via the backend) instead of being inferred
 * from execution log history. This avoids incorrect status display when logs
 * are truncated by the embedded log limit.
 */
export const usePrivacyRequestEventLogs = (
  results?: PrivacyRequestResults,
  taskStatusByDataset?: Record<string, string>,
) => {
  const { data: connectionsResponse, isLoading: isConnectionsLoading } =
    useGetAllDatastoreConnectionsQuery({ size: 100 });

  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});

  const connectionsByKey = useMemo(() => {
    const map = new Map<string, ConnectionConfigurationResponse>();
    connectionsResponse?.items?.forEach((conn) => {
      if (conn.key) {
        map.set(conn.key, conn);
      }
    });
    return map;
  }, [connectionsResponse]);

  const connectionTypesByIdentifier = useMemo(() => {
    const map = new Map<string, ConnectionSystemTypeMap>();
    connectionTypesData?.items?.forEach((ct) => {
      if (ct.identifier) {
        map.set(ct.identifier, ct);
      }
    });
    return map;
  }, [connectionTypesData]);

  // We don't block the timeline on connections — if the lookup hasn't resolved
  // we just fall back to humanized keys.
  const isLoading = !results || isConnectionsLoading;

  // Map from source events to ActivityTimelineItems
  const eventItems: ActivityTimelineItem[] = !results
    ? []
    : Object.entries(results).map(([key, logs]) => {
        const taskStatus = taskStatusByDataset?.[key];

        // When we have an authoritative task status from the backend, use it
        // directly. Otherwise fall back to scanning execution logs (needed for
        // audit-log entries like "Request approved" which have no RequestTask).
        const hasUnresolvedErrorStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.ERROR
            : hasUnresolvedError(logs);
        const hasSkippedEntryStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.SKIPPED
            : hasSkippedEntry(logs);
        const hasAwaitingProcessingStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.AWAITING_PROCESSING
            : hasAwaitingProcessing(logs);
        const hasPollingStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.POLLING
            : hasPolling(logs);

        const firstLog = logs[0];
        const connectionKey = firstLog?.connection_key;
        const connection = connectionKey
          ? connectionsByKey.get(connectionKey)
          : undefined;

        let title: string;
        let connectionLogo: ActivityTimelineItem["connectionLogo"];
        let icon: ActivityTimelineItem["icon"];

        if (connection) {
          title = connection.name || humanizeIdentifier(connection.key);
          // SaaS connections carry their logo as a base64-encoded SVG on the
          // matching ConnectionSystemTypeMap, not on the connection itself.
          const saasType =
            connection.connection_type === ConnectionType.SAAS
              ? connection.saas_config?.type
              : undefined;
          const systemType = saasType
            ? connectionTypesByIdentifier.get(saasType)
            : undefined;
          connectionLogo = systemType
            ? connectionLogoFromSystemType(systemType)
            : connectionLogoFromConfiguration(connection);
        } else {
          // Legacy ExecutionLogs persisted with dataset_name "Access package
          // upload" should display as "Access package sent" alongside newly
          // created rows. Remove once legacy rows are migrated.
          const displayKey =
            key === "Access package upload" ? "Access package sent" : key;
          title = humanizeIdentifier(displayKey);
          icon = systemEventIcon(key, firstLog?.status ?? "");
        }

        return {
          author: "Fides",
          title,
          date: new Date(logs[0].updated_at),
          type: ActivityTimelineItemTypeEnum.REQUEST_UPDATE,
          onClick: () => {}, // This will be overridden in the component
          isError: hasUnresolvedErrorStatus,
          isSkipped: hasSkippedEntryStatus,
          isAwaitingInput: hasAwaitingProcessingStatus,
          isPolling: hasPollingStatus,
          isFinished: firstLog?.status === "finished",
          id: `request-${key}`,
          logCount: logs.length,
          connectionLogo,
          icon,
          resultsKey: key,
        };
      });

  return {
    eventItems,
    isLoading,
  };
};

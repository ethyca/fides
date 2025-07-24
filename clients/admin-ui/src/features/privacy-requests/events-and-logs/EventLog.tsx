import { formatDate } from "common/utils";
import {
  AntTag,
  Box,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import {
  ExecutionLog,
  ExecutionLogStatus,
  ExecutionLogStatusColors,
  ExecutionLogStatusLabels,
  PrivacyRequestEntity,
} from "privacy-requests/types";
import React from "react";

import { ActionType } from "~/types/api";

type EventDetailsProps = {
  eventLogs: ExecutionLog[];
  allEventLogs?: ExecutionLog[]; // All event logs from all groups for total calculation
  onDetailPanel: (message: string, status?: ExecutionLogStatus) => void;
  privacyRequest?: PrivacyRequestEntity;
};

const actionTypeToLabel = (actionType: string) => {
  switch (actionType) {
    case ActionType.ACCESS:
      return "Data Retrieval";
    case ActionType.ERASURE:
      return "Data Deletion";
    case ActionType.CONSENT:
      return "Consent";
    case ActionType.UPDATE:
      return "Data Update";
    default:
      return actionType;
  }
};

const extractRecordCount = (detail: ExecutionLog): string => {
  // Only show record counts for completed operations
  if (detail.status !== ExecutionLogStatus.COMPLETE) {
    return "-";
  }

  // Only show record counts for actual dataset entries that have a collection_name
  if (!detail.collection_name) {
    return "-";
  }

  // Extract record count from standardized message format
  const message = detail.message || "";

  // Standardized format: "success - retrieved/masked/processed X records"
  const standardPattern = /(?:retrieved|masked|processed)\s+(\d+)\s+records?$/i;
  const standardMatch = message.match(standardPattern);
  if (standardMatch) {
    return parseInt(standardMatch[1], 10).toLocaleString();
  }

  return "-";
};

const calculateTotalRecordCount = (
  eventLogs: ExecutionLog[],
  actionType: string,
): number | null => {
  // Get all execution logs for the current action type that are complete
  // and have collection names (actual dataset entries)
  const relevantLogs = eventLogs.filter(
    (log) =>
      log.action_type === actionType &&
      log.status === ExecutionLogStatus.COMPLETE &&
      log.collection_name,
  );

  // Sort by updated_at descending to get latest entries first
  const sortedLogs = relevantLogs.sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );

  // Group by collection and keep only the latest entry for each
  // to avoid multiples in case the request is reprocessed
  const latestByCollection: { [key: string]: ExecutionLog } = {};
  sortedLogs.forEach((log) => {
    // Use collection_name as key since dataset_name is not available in this interface
    const collectionKey = log.collection_name || "unknown";
    if (!latestByCollection[collectionKey]) {
      latestByCollection[collectionKey] = log;
    }
  });

  // Extract record counts from the standardized message format
  let totalCount = 0;
  let foundAnyRecordInfo = false;
  const recordPattern = /(?:retrieved|masked|processed)\s+(\d+)\s+records?$/i;

  Object.values(latestByCollection).forEach((log) => {
    if (log.message) {
      const match = log.message.match(recordPattern);
      if (match) {
        foundAnyRecordInfo = true;
        const count = parseInt(match[1], 10);
        totalCount += count;
      }
    }
  });

  // Return null if no record count information was found
  // Return the actual count (including 0) if we found record information
  return foundAnyRecordInfo ? totalCount : null;
};

const extractRecordCountOrTotal = (
  detail: ExecutionLog,
  eventLogs: ExecutionLog[],
  privacyRequestActionType?: string,
): string => {
  // For "Request finished" entries, show total record count
  // Check if status is "finished" (audit log action) and no collection_name
  // Cast to string since audit log status values are not in ExecutionLogStatus enum
  if (
    (detail.status as string) === "finished" &&
    !detail.collection_name &&
    privacyRequestActionType
  ) {
    const totalCount = calculateTotalRecordCount(
      eventLogs,
      privacyRequestActionType,
    );

    // Show the actual count (including 0) if we found record count information
    // Show "-" if no record count information was found in any logs
    return totalCount !== null ? totalCount.toLocaleString() : "-";
  }

  // For individual collection entries, use the existing logic
  return extractRecordCount(detail);
};

const EventLog = ({
  eventLogs,
  allEventLogs,
  onDetailPanel,
  privacyRequest,
}: EventDetailsProps) => {
  // Check if any logs have collection_name OR if there's a finished entry to determine if we should show Records and Collection columns
  const hasDatasetEntries =
    eventLogs?.some((log) => log.collection_name) ||
    eventLogs?.some(
      (log) => (log.status as string) === "finished" && !log.collection_name,
    ) ||
    false;

  // Check if we're viewing only "Request finished" entries
  const isRequestFinishedView = eventLogs?.every(
    (log) => (log.status as string) === "finished" && !log.collection_name,
  );

  // Get the primary action type from the privacy request policy rules
  const privacyRequestActionType =
    privacyRequest?.policy?.rules?.[0]?.action_type;

  // Helper function to get action type label with fallback
  const getActionTypeLabel = (
    logActionType: string | null | undefined,
  ): string => {
    if (logActionType) {
      return actionTypeToLabel(logActionType);
    }
    if (privacyRequestActionType) {
      return actionTypeToLabel(privacyRequestActionType);
    }
    return "-";
  };

  const tableItems = eventLogs?.map((detail) => (
    <Tr
      key={detail.updated_at}
      backgroundColor={
        detail.status === ExecutionLogStatus.ERROR ||
        (detail.status === ExecutionLogStatus.SKIPPED && detail.message) ||
        detail.status === ExecutionLogStatus.AWAITING_PROCESSING
          ? palette.FIDESUI_NEUTRAL_50
          : "unset"
      }
      onClick={() => {
        if (
          detail.status === ExecutionLogStatus.ERROR ||
          (detail.status === ExecutionLogStatus.SKIPPED && detail.message) ||
          detail.status === ExecutionLogStatus.AWAITING_PROCESSING
        ) {
          onDetailPanel(detail.message, detail.status);
        }
      }}
      style={{
        cursor: detail.message ? "pointer" : "unset",
      }}
      _hover={{ backgroundColor: palette.FIDESUI_NEUTRAL_50 }}
    >
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {formatDate(detail.updated_at)}
        </Text>
      </Td>
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {getActionTypeLabel(detail.action_type)}
        </Text>
      </Td>
      {hasDatasetEntries && !isRequestFinishedView && (
        <Td>
          {ExecutionLogStatusLabels[detail.status] ? (
            <AntTag color={ExecutionLogStatusColors[detail.status]}>
              {ExecutionLogStatusLabels[detail.status]}
            </AntTag>
          ) : (
            <Text
              color="gray.600"
              fontSize="xs"
              lineHeight="4"
              fontWeight="medium"
            >
              {detail.status}
            </Text>
          )}
        </Td>
      )}
      {hasDatasetEntries && (
        <Td>
          <Text
            color="gray.600"
            fontSize="xs"
            lineHeight="4"
            fontWeight="medium"
          >
            {extractRecordCountOrTotal(
              detail,
              allEventLogs || eventLogs,
              privacyRequestActionType,
            )}
          </Text>
        </Td>
      )}
      {hasDatasetEntries && !isRequestFinishedView && (
        <Td>
          <Text
            color="gray.600"
            fontSize="xs"
            lineHeight="4"
            fontWeight="medium"
          >
            {(detail.status as string) === "finished"
              ? "Request completed"
              : detail.collection_name}
          </Text>
        </Td>
      )}
    </Tr>
  ));

  return (
    <Box width="100%" paddingTop="0px" height="100%">
      <TableContainer
        id="tableContainer"
        height="100%"
        style={{
          overflowY: "auto", // needs to be set on style. Chakra overrides it
        }}
      >
        <Table size="sm" id="table" position="relative">
          <Thead
            id="tableHeader"
            position="sticky"
            top="0px"
            backgroundColor="white"
            zIndex={10}
          >
            <Tr>
              <Th>
                <Text
                  color="black"
                  fontSize="xs"
                  lineHeight="4"
                  fontWeight="medium"
                >
                  Time
                </Text>
              </Th>
              <Th>
                <Text
                  color="black"
                  fontSize="xs"
                  lineHeight="4"
                  fontWeight="medium"
                >
                  Action Type
                </Text>
              </Th>
              {hasDatasetEntries && !isRequestFinishedView && (
                <Th>
                  <Text
                    color="black"
                    fontSize="xs"
                    lineHeight="4"
                    fontWeight="medium"
                  >
                    Status
                  </Text>
                </Th>
              )}
              {hasDatasetEntries && (
                <Th>
                  <Text
                    color="black"
                    fontSize="xs"
                    lineHeight="4"
                    fontWeight="medium"
                  >
                    Records
                  </Text>
                </Th>
              )}
              {hasDatasetEntries && !isRequestFinishedView && (
                <Th>
                  <Text
                    color="black"
                    fontSize="xs"
                    lineHeight="4"
                    fontWeight="medium"
                  >
                    Collection
                  </Text>
                </Th>
              )}
            </Tr>
          </Thead>

          <Tbody id="tableBody">{tableItems}</Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default EventLog;

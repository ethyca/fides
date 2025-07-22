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

const EventLog = ({
  eventLogs,
  onDetailPanel,
  privacyRequest,
}: EventDetailsProps) => {
  // Check if any logs have collection_name to determine if we should show Records and Collection columns
  const hasDatasetEntries =
    eventLogs?.some((log) => log.collection_name) || false;

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
      {hasDatasetEntries && (
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
            {extractRecordCount(detail)}
          </Text>
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
            {detail.collection_name}
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
              {hasDatasetEntries && (
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
              {hasDatasetEntries && (
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

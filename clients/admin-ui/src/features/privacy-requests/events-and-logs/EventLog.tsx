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
} from "privacy-requests/types";

import { ActionType } from "~/types/api";

type EventDetailsProps = {
  eventLogs: ExecutionLog[];
  openErrorPanel: (message: string, status?: ExecutionLogStatus) => void;
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

const EventLog = ({ eventLogs, openErrorPanel }: EventDetailsProps) => {
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
          openErrorPanel(detail.message, detail.status);
        }
      }}
      style={{
        cursor:
          detail.status === ExecutionLogStatus.ERROR ||
          (detail.status === ExecutionLogStatus.SKIPPED && detail.message) ||
          detail.status === ExecutionLogStatus.AWAITING_PROCESSING
            ? "pointer"
            : "unset",
      }}
    >
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {formatDate(detail.updated_at)}
        </Text>
      </Td>
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {actionTypeToLabel(detail.action_type)}
        </Text>
      </Td>
      <Td>
        <AntTag color={ExecutionLogStatusColors[detail.status]}>
          {ExecutionLogStatusLabels[detail.status]}
        </AntTag>
      </Td>
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {detail.collection_name}
        </Text>
      </Td>
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
            </Tr>
          </Thead>

          <Tbody id="tableBody">{tableItems}</Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default EventLog;

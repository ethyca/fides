import {
  Box,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { format } from "date-fns-tz";
import { ExecutionLog, ExecutionLogStatus } from "privacy-requests/types";
import React from "react";

type EventDetailsProps = {
  eventLogs: ExecutionLog[];
  openErrorPanel: (message: string) => void;
};

const EventLog = ({ eventLogs, openErrorPanel }: EventDetailsProps) => {
  const tableItems = eventLogs?.map((detail) => (
    <Tr
      key={detail.updated_at}
      _hover={{
        backgroundColor:
          detail.status === ExecutionLogStatus.ERROR ? "#F7FAFC" : "unset",
      }}
      onClick={() => {
        if (detail.status === ExecutionLogStatus.ERROR) {
          openErrorPanel(detail.message);
        }
      }}
      style={{
        cursor:
          detail.status === ExecutionLogStatus.ERROR ? "pointer" : "unset",
      }}
    >
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {format(new Date(detail.updated_at), "MMMM d, Y, KK:mm:ss z")}
        </Text>
      </Td>
      <Td>
        <Text color="gray.600" fontSize="xs" lineHeight="4" fontWeight="medium">
          {detail.status}
        </Text>
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

          <Tbody id="tabelBody">{tableItems}</Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default EventLog;

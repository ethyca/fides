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
import React from "react";

import { ExecutionLog } from "../privacy-requests/types";

type EventDetailsProps = {
  eventDetails: ExecutionLog[];
};

const EventDetails = ({ eventDetails }: EventDetailsProps) => (
  <Box width="100%">
    <Text color="gray.900" fontSize="md" fontWeight="500" mb={1}>
      Event Details
    </Text>
    <TableContainer>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th>Timestamp </Th>
            <Th>Collection </Th>
            <Th>Status </Th>
            <Th>Message </Th>
          </Tr>
        </Thead>
        <Tbody>
          {eventDetails?.map((detail) => (
            <Tr key={detail.updated_at}>
              <Td>
                {format(new Date(detail.updated_at), "MMMM d, Y, KK:mm:ss z")}
              </Td>
              <Td> {detail.collection_name}</Td>
              <Td> {detail.status}</Td>
              <Td>{detail.message}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  </Box>
);

export default EventDetails;

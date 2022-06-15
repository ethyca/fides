import { Box, Divider, Flex, Heading, Text } from "@fidesui/react";
import React from "react";

import ClipboardButton from "../common/ClipboardButton";
import RequestStatusBadge from "../common/RequestStatusBadge";
import RequestType from "../common/RequestType";
import { PrivacyRequest } from "../privacy-requests/types";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequest;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { id, status, policy } = subjectRequest;

  return (
    <>
      <Heading fontSize="lg" fontWeight="semibold" mb={4}>
        Request details
      </Heading>
      <Divider />
      <Flex alignItems="center">
        <Text
          mt={4}
          mb={4}
          mr={2}
          fontSize="sm"
          color="gray.900"
          fontWeight="500"
        >
          Request ID:
        </Text>
        <Text color="gray.600" fontWeight="500" fontSize="sm" mr={1}>
          {id}
        </Text>
        <ClipboardButton requestId={id} />
      </Flex>

      <Flex alignItems="center">
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Request Type:
        </Text>
        <RequestType rules={policy.rules} />
      </Flex>
      <Flex alignItems="flex-start">
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Status:
        </Text>
        <Box>
          <RequestStatusBadge status={status} />
        </Box>
      </Flex>
    </>
  );
};

export default RequestDetails;

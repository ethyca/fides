import { Box, Divider, Flex, Heading, HStack, Tag, Text } from "@fidesui/react";
import DaysLeftTag from "common/DaysLeftTag";
import { PrivacyRequestEntity } from "privacy-requests/types";

import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import ClipboardButton from "../common/ClipboardButton";
import RequestStatusBadge from "../common/RequestStatusBadge";
import RequestType from "../common/RequestType";
import ReprocessButton from "./buttons/ReprocessButton";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { id, status, policy } = subjectRequest;

  return (
    <>
      <Heading color="gray.900" fontSize="lg" fontWeight="semibold" mb={4}>
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
        <ClipboardButton copyText={id} />
      </Flex>

      <Flex alignItems="center">
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Request Type:
        </Text>
        <Box mr={1} mb={4}>
          <RequestType rules={policy.rules} />
        </Box>
      </Flex>
      <Flex>
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Policy key:
        </Text>
        <Box>
          <Tag color="white" bg="primary.400" fontWeight="medium" fontSize="sm">
            {subjectRequest.policy.key}
          </Tag>
        </Box>
      </Flex>
      <Flex alignItems="flex-start">
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Status:
        </Text>
        <HStack spacing="16px">
          <RequestStatusBadge status={status} />
          {status === "error" && (
            <ReprocessButton
              buttonProps={{ size: "xs" }}
              subjectRequest={subjectRequest}
            />
          )}

          <DaysLeftTag
            daysLeft={subjectRequest.days_left}
            includeText
            status={subjectRequest.status as ApiPrivacyRequestStatus}
          />
        </HStack>
      </Flex>
    </>
  );
};

export default RequestDetails;

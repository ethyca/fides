import { Box, Divider, Flex, Heading, HStack, Tag, Text } from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType from "~/features/common/RequestType";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import ApproveButton from "./buttons/ApproveButton";
import DenyButton from "./buttons/DenyButton";
import ReprocessButton from "./buttons/ReprocessButton";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { plus: hasPlus } = useFeatures();
  const { id, status, policy } = subjectRequest;

  return (
    <>
      <Heading
        color="gray.900"
        fontSize="lg"
        fontWeight="semibold"
        mt={4}
        mb={4}
      >
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
      {hasPlus && subjectRequest.source && (
        <Flex>
          <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
            Source:
          </Text>
          <Box>
            <Tag
              color="white"
              bg="primary.400"
              fontWeight="medium"
              fontSize="sm"
            >
              {subjectRequest.source}
            </Tag>
          </Box>
        </Flex>
      )}
      <Flex alignItems="center">
        <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Request type:
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
      <Flex alignItems="center">
        <Text mb={0} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Status:
        </Text>
        <HStack spacing="8px">
          <Flex>
            <RequestStatusBadge status={status} />
          </Flex>
          <div className="flex gap-3">
            {status === "error" && (
              <ReprocessButton subjectRequest={subjectRequest} />
            )}

            {status === "pending" && (
              <>
                <ApproveButton subjectRequest={subjectRequest}>
                  Approve
                </ApproveButton>
                <DenyButton subjectRequest={subjectRequest}>Deny</DenyButton>
              </>
            )}
          </div>

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

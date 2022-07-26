import {
  Button,
  Divider,
  Flex,
  Heading,
  HStack,
  Text,
  useToast,
} from "@fidesui/react";
import ClipboardButton from "common/ClipboardButton";
import { isErrorWithDetail, isErrorWithDetailArray } from "common/helpers";
import RequestStatusBadge from "common/RequestStatusBadge";
import RequestType from "common/RequestType";
import { useRetryMutation } from "privacy-requests/privacy-requests.slice";
import { PrivacyRequest } from "privacy-requests/types";
import { useState } from "react";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequest;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { id, status, policy } = subjectRequest;
  const [retry] = useRetryMutation();
  const toast = useToast();
  const [isRetrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    retry(subjectRequest)
      .unwrap()
      .catch((error) => {
        let errorMsg = "An unexpected error occurred. Please try again.";
        if (isErrorWithDetail(error)) {
          errorMsg = error.data.detail;
        } else if (isErrorWithDetailArray(error)) {
          errorMsg = error.data.detail[0].msg;
        }
        toast({
          status: "error",
          description: errorMsg,
        });
      })
      .finally(() => {
        setRetrying(false);
      });
  };

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
        <HStack spacing="16px">
          <RequestStatusBadge status={status} />
          {status === "error" && (
            <Button
              isLoading={isRetrying}
              loadingText="Retrying"
              onClick={handleRetry}
              size="xs"
              spinnerPlacement="end"
              variant="outline"
            >
              Retry
            </Button>
          )}
        </HStack>
      </Flex>
    </>
  );
};

export default RequestDetails;

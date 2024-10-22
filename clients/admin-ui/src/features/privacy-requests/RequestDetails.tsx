import {
  AntButton,
  Box,
  Divider,
  Flex,
  Heading,
  HStack,
  Tag,
  Text,
  useToast,
} from "fidesui";
import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth";

import ClipboardButton from "~/features/common/ClipboardButton";
import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import { DownloadLightIcon } from "~/features/common/Icon";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType from "~/features/common/RequestType";
import Restrict from "~/features/common/Restrict";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import { useLazyGetPrivacyRequestAccessResultsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { ScopeRegistryEnum } from "~/types/api";
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

  // TODO: switch this not to use a lazy query and disable the button if the URL is local

  const [getAccessResult, { isLoading, isFetching }] =
    useLazyGetPrivacyRequestAccessResultsQuery();

  const toast = useToast();

  const handleGetAccessResult = async () => {
    const { data, isError, error } = await getAccessResult({
      privacy_request_id: id,
    });
    if (isError) {
      const errorMsg = getErrorMessage(
        error,
        "A problem occurred while finding the location of the request details",
      );
      toast({ status: "error", description: errorMsg });
      return;
    }
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const url = data?.access_result_urls[0] ?? "";
    if (url[0] === "your local fides_uploads folder") {
      toast({
        ...DEFAULT_TOAST_PARAMS,
        status: "warning",
        description:
          "Access results are stored in your local fides_uploads folder and will not be downloaded",
      });
    } else {
      // fetchPrivacyRequest(url);
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.click();
      link.remove();
    }
  };

  return (
    <Flex direction="column" gap={4}>
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
        <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Request ID:
        </Text>
        <Text color="gray.600" fontWeight="500" fontSize="sm" mr={1}>
          {id}
        </Text>
        <ClipboardButton copyText={id} size="small" />
      </Flex>
      {hasPlus && subjectRequest.source && (
        <Flex>
          <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
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
        <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
          Request type:
        </Text>
        <Box mr={1}>
          <RequestType rules={policy.rules} />
        </Box>
      </Flex>
      <Flex>
        <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
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
      <Restrict
        scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_ACCESS_RESULTS_READ]}
      >
        <Flex>
          <AntButton
            onClick={handleGetAccessResult}
            icon={<DownloadLightIcon />}
            loading={isLoading || isFetching}
          >
            Download request details
          </AntButton>
        </Flex>
      </Restrict>
    </Flex>
  );
};

export default RequestDetails;

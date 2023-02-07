import {
  useApproveRequestMutation,
  useDenyRequestMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

export const useMutations = ({
  subjectRequest,
}: {
  subjectRequest: PrivacyRequestEntity;
}) => {
  // The `fixedCacheKey` options allows multiple components to reference the same mutation state for
  // a subject request.
  const [approveRequest, approveRequestResult] = useApproveRequestMutation({
    fixedCacheKey: subjectRequest.id,
  });
  const [denyRequest, denyRequestResult] = useDenyRequestMutation({
    fixedCacheKey: subjectRequest.id,
  });

  const handleApproveRequest = () => approveRequest(subjectRequest);
  const handleDenyRequest = (reason: string) =>
    denyRequest({ id: subjectRequest.id, reason });

  const isLoading =
    denyRequestResult.isLoading || approveRequestResult.isLoading;

  return {
    approveRequest,
    approveRequestResult,
    denyRequest,
    denyRequestResult,
    handleApproveRequest,
    handleDenyRequest,
    isLoading,
  };
};

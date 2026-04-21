import { useChakraDisclosure as useDisclosure, useMessage } from "fidesui";

import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { PrivacyRequestStatus } from "~/types/api";

import { PrivacyRequestEntity } from "../types";
import { useMutations } from "./useMutations";

const useApproveDenyPrivacyRequest = ({
  privacyRequest,
  action,
}: {
  privacyRequest: PrivacyRequestEntity;
  action: "approve" | "deny";
}) => {
  const { handleApproveRequest, handleDenyRequest } = useMutations({
    subjectRequest: privacyRequest,
  });

  const message = useMessage();
  const { data: config } = useGetConfigurationSettingsQuery({
    api_set: false,
  });
  const identityVerificationRequired =
    config?.execution?.subject_identity_verification_required ?? false;

  const isPendingStatus =
    privacyRequest.status === PrivacyRequestStatus.PENDING;
  const isDuplicateStatus =
    privacyRequest.status === PrivacyRequestStatus.DUPLICATE;
  const isUnverifiedDuplicate =
    isDuplicateStatus &&
    !privacyRequest.identity_verified_at &&
    identityVerificationRequired;
  const isAwaitingPreApproval =
    privacyRequest.status === PrivacyRequestStatus.AWAITING_PRE_APPROVAL;
  const isPreApprovalNotEligible =
    privacyRequest.status === PrivacyRequestStatus.PRE_APPROVAL_NOT_ELIGIBLE;

  const showAction =
    isPendingStatus ||
    (isDuplicateStatus && !(action === "approve" && isUnverifiedDuplicate)) ||
    isAwaitingPreApproval ||
    isPreApprovalNotEligible;
  const modal = useDisclosure();

  const performAction = async ({ reason }: { reason: string }) => {
    const content =
      action === "approve" ? "Approving request..." : "Denying request...";
    const closeLoading = message.loading({ content });
    if (action === "deny") {
      await handleDenyRequest(reason);
    }
    if (action === "approve") {
      await handleApproveRequest();
    }
    closeLoading();
  };

  return {
    showAction,
    closeModal: modal.onClose,
    performAction,
    openConfirmationModal: modal.onOpen,
    isModalOpen: modal.isOpen,
  };
};
export default useApproveDenyPrivacyRequest;

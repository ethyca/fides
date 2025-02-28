import { message, useDisclosure } from "fidesui";

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

  const isPendingStatus =
    privacyRequest.status === PrivacyRequestStatus.PENDING;

  const showAction = isPendingStatus;
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

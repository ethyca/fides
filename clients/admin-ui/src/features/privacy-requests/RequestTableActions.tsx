import {
  AntButton,
  CheckIcon,
  CloseIcon,
  HStack,
  Portal,
  StackProps,
  useDisclosure,
} from "fidesui";

import ApprovePrivacyRequestModal from "~/features/privacy-requests/ApprovePrivacyRequestModal";
import DenyPrivacyRequestModal from "~/features/privacy-requests/DenyPrivacyRequestModal";
import { useMutations } from "~/features/privacy-requests/hooks/useMutations";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

interface RequestTableActionsProps extends StackProps {
  subjectRequest: PrivacyRequestEntity;
}

export const RequestTableActions = ({
  subjectRequest,
  ...props
}: RequestTableActionsProps): JSX.Element | null => {
  const approvalModal = useDisclosure();
  const denyModal = useDisclosure();
  const { handleApproveRequest, handleDenyRequest, isLoading } = useMutations({
    subjectRequest,
  });
  if (subjectRequest.status !== "pending") {
    return null;
  }
  return (
    <>
      <HStack {...props}>
        <AntButton
          title="Approve"
          aria-label="Approve"
          icon={<CheckIcon w={2} h={2} />}
          onClick={approvalModal.onOpen}
          loading={isLoading}
          disabled={isLoading}
          data-testid="privacy-request-approve-btn"
          size="small"
        />
        <AntButton
          title="Deny"
          aria-label="Deny"
          icon={<CloseIcon w={2} h={2} />}
          onClick={denyModal.onOpen}
          loading={isLoading}
          disabled={isLoading}
          data-testid="privacy-request-deny-btn"
          size="small"
        />
      </HStack>

      <Portal>
        <ApprovePrivacyRequestModal
          isOpen={approvalModal.isOpen}
          isLoading={isLoading}
          onClose={approvalModal.onClose}
          onApproveRequest={handleApproveRequest}
          subjectRequest={subjectRequest}
        />
      </Portal>
      <Portal>
        <DenyPrivacyRequestModal
          isOpen={denyModal.isOpen}
          onClose={denyModal.onClose}
          onDenyRequest={handleDenyRequest}
        />
      </Portal>
    </>
  );
};

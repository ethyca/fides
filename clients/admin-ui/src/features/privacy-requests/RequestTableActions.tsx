import {
  AntButton as Button,
  HStack,
  Icons,
  Portal,
  StackProps,
  Text,
  useDisclosure,
} from "fidesui";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import Restrict from "~/features/common/Restrict";
import ApprovePrivacyRequestModal from "~/features/privacy-requests/ApprovePrivacyRequestModal";
import DenyPrivacyRequestModal from "~/features/privacy-requests/DenyPrivacyRequestModal";
import { useMutations } from "~/features/privacy-requests/hooks/useMutations";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { ScopeRegistryEnum } from "~/types/api";

interface RequestTableActionsProps extends StackProps {
  subjectRequest: PrivacyRequestEntity;
}

export const RequestTableActions = ({
  subjectRequest,
  ...props
}: RequestTableActionsProps): JSX.Element | null => {
  const approvalModal = useDisclosure();
  const denyModal = useDisclosure();
  const deleteModal = useDisclosure();
  const {
    handleApproveRequest,
    handleDenyRequest,
    handleDeleteRequest,
    isLoading,
  } = useMutations({
    subjectRequest,
  });

  const renderApproveButton = () => {
    if (subjectRequest.status !== "pending") {
      return null;
    }

    return (
      <Button
        title="Approve"
        aria-label="Approve"
        icon={<Icons.Checkmark />}
        onClick={approvalModal.onOpen}
        loading={isLoading}
        disabled={isLoading}
        data-testid="privacy-request-approve-btn"
        size="small"
      />
    );
  };

  const renderDenyButton = () => {
    if (subjectRequest.status !== "pending") {
      return null;
    }

    return (
      <Button
        title="Deny"
        aria-label="Deny"
        icon={<Icons.Close />}
        onClick={denyModal.onOpen}
        loading={isLoading}
        disabled={isLoading}
        data-testid="privacy-request-deny-btn"
        size="small"
      />
    );
  };

  const renderDeleteButton = () => {
    return (
      <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_DELETE]}>
        <Button
          title="Delete"
          aria-label="Delete"
          icon={<Icons.TrashCan size={14} />}
          onClick={deleteModal.onOpen}
          loading={isLoading}
          disabled={isLoading}
          data-testid="privacy-request-delete-btn"
          size="small"
        />
      </Restrict>
    );
  };

  return (
    <>
      <HStack {...props}>
        {renderApproveButton()}
        {renderDenyButton()}
        {renderDeleteButton()}
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
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.onClose}
        onConfirm={handleDeleteRequest}
        message={
          <Text>
            You are about to permanently delete the privacy request. Are you
            sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

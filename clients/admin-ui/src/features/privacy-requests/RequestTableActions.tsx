import {
  Button,
  ChakraHStack as HStack,
  ChakraPortal as Portal,
  ChakraStackProps as StackProps,
  ChakraText as Text,
  Icons,
  useChakraDisclosure as useDisclosure,
  useModal,
} from "fidesui";

import Restrict from "~/features/common/Restrict";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { useGetActiveMessagingProviderQuery } from "~/features/messaging/messaging.slice";
import DenyPrivacyRequestModal from "~/features/privacy-requests/DenyPrivacyRequestModal";
import {
  PrivacyRequestResponse,
  PrivacyRequestStatus,
  ScopeRegistryEnum,
} from "~/types/api";

import ApprovePrivacyRequestModal from "./ApprovePrivacyRequestModal";
import { getButtonVisibility } from "./helpers";
import { useMutations } from "./hooks/useMutations";
import { PrivacyRequestEntity } from "./types";

interface RequestTableActionsProps extends StackProps {
  subjectRequest: PrivacyRequestResponse | PrivacyRequestEntity;
}

export const RequestTableActions = ({
  subjectRequest,
  ...props
}: RequestTableActionsProps): JSX.Element | null => {
  const approvalModal = useDisclosure();
  const denyModal = useDisclosure();
  const modal = useModal();
  const {
    handleApproveRequest,
    handleDenyRequest,
    handleDeleteRequest,
    handleFinalizeRequest,
    isLoading,
  } = useMutations({
    subjectRequest,
  });

  const { data: config } = useGetConfigurationSettingsQuery({
    api_set: false,
  });
  const { data: activeMessagingProvider } =
    useGetActiveMessagingProviderQuery();
  const sendRequestCompletionNotification =
    config?.notifications?.send_request_completion_notification;
  const identityVerificationRequired =
    config?.execution?.subject_identity_verification_required ?? false;

  const isUnverifiedDuplicate =
    subjectRequest.status === PrivacyRequestStatus.DUPLICATE &&
    !subjectRequest.identity_verified_at &&
    identityVerificationRequired;
  const buttonVisibility = {
    ...getButtonVisibility(subjectRequest.status),
    ...(isUnverifiedDuplicate && { approve: false }),
  };

  const renderApproveButton = () => {
    if (!buttonVisibility.approve) {
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
    if (!buttonVisibility.deny) {
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

  const handleFinalizeConfirm = () => {
    modal.confirm({
      title: "Finalize privacy request",
      content: (
        <Text>
          You are about to finalize this privacy request. The status will be
          updated to &#34;Complete&#34;
          {sendRequestCompletionNotification &&
          activeMessagingProvider?.service_type
            ? " and the requesting user will be notified"
            : ""}
          . Would you like to continue?
        </Text>
      ),
      centered: true,
      icon: null,
      onOk: () => {
        handleFinalizeRequest();
      },
    });
  };

  const renderFinalizeButton = () => {
    if (!buttonVisibility.finalize) {
      return null;
    }
    return (
      <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW]}>
        <Button
          title="Finalize"
          aria-label="Finalize"
          icon={<Icons.Stamp />}
          onClick={handleFinalizeConfirm}
          loading={isLoading}
          disabled={isLoading}
          data-testid="privacy-request-finalize-btn"
          size="small"
        />
      </Restrict>
    );
  };

  const handleDeleteConfirm = () => {
    modal.confirm({
      content: (
        <Text>
          You are about to permanently delete the privacy request. Are you sure
          you would like to continue?
        </Text>
      ),
      centered: true,
      icon: null,
      onOk: handleDeleteRequest,
    });
  };

  const renderDeleteButton = () => {
    if (!buttonVisibility.delete) {
      return null;
    }
    return (
      <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_DELETE]}>
        <Button
          title="Delete"
          aria-label="Delete"
          icon={<Icons.TrashCan size={14} />}
          onClick={handleDeleteConfirm}
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
        {renderFinalizeButton()}
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
    </>
  );
};

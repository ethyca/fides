import { Button, Flex, FlexProps, Icons, Typography, useModal } from "fidesui";
import { useState } from "react";

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

interface RequestTableActionsProps extends FlexProps {
  subjectRequest: PrivacyRequestResponse | PrivacyRequestEntity;
}

export const RequestTableActions = ({
  subjectRequest,
  ...props
}: RequestTableActionsProps): JSX.Element | null => {
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [denyModalOpen, setDenyModalOpen] = useState(false);
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
        onClick={() => setApprovalModalOpen(true)}
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
        onClick={() => setDenyModalOpen(true)}
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
        <Typography.Text>
          You are about to finalize this privacy request. The status will be
          updated to &#34;Complete&#34;
          {sendRequestCompletionNotification &&
          activeMessagingProvider?.service_type
            ? " and the requesting user will be notified"
            : ""}
          . Would you like to continue?
        </Typography.Text>
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
        <Typography.Text>
          You are about to permanently delete the privacy request. Are you sure
          you would like to continue?
        </Typography.Text>
      ),
      centered: true,
      onOk: handleDeleteRequest,
      okButtonProps: {
        danger: true,
      },
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
      <Flex {...props}>
        {renderApproveButton()}
        {renderDenyButton()}
        {renderFinalizeButton()}
        {renderDeleteButton()}
      </Flex>

      <ApprovePrivacyRequestModal
        isOpen={approvalModalOpen}
        isLoading={isLoading}
        onClose={() => setApprovalModalOpen(false)}
        onApproveRequest={handleApproveRequest}
        subjectRequest={subjectRequest}
      />
      <DenyPrivacyRequestModal
        isOpen={denyModalOpen}
        onClose={() => setDenyModalOpen(false)}
        onDenyRequest={handleDenyRequest}
      />
    </>
  );
};

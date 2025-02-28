import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";
import { useMemo } from "react";

import { PrivacyRequestStatus } from "~/types/api";

import ApprovePrivacyRequestModal from "./ApprovePrivacyRequestModal";
import DenyPrivacyRequestModal from "./DenyPrivacyRequestModal";
import useApproveDenyPrivacyRequest from "./hooks/useApproveDenyPrivacyRequest";
import useDownloadPrivacyRequestResults from "./hooks/useDownloadPrivacyRequestResults";
import { PrivacyRequestEntity } from "./types";

interface PrivacyRequestActionsDropdownProps {
  privacyRequest: PrivacyRequestEntity;
}

const PrivacyRequestActionsDropdown = ({
  privacyRequest,
}: PrivacyRequestActionsDropdownProps) => {
  const isErrorStatus = privacyRequest.status === PrivacyRequestStatus.ERROR;

  const {
    showDownloadResults,
    downloadResults,
    infoTooltip,
    isDisabled: isDownloadDisabled,
  } = useDownloadPrivacyRequestResults({ privacyRequest });

  const {
    isModalOpen: isApproveModalOpen,
    closeModal: closeApproveModal,
    performAction: approveRequest,
    openConfirmationModal: openApproveConfirmationModal,
    showAction: showApproveRequest,
  } = useApproveDenyPrivacyRequest({ privacyRequest, action: "approve" });

  const {
    isModalOpen: isDenyModalOpen,
    closeModal: closeDenyModal,
    performAction: denyRequest,
    openConfirmationModal: openDenyConfirmationModal,
    showAction: showDenyRequest,
  } = useApproveDenyPrivacyRequest({
    privacyRequest,
    action: "deny",
  });

  const menuItems = useMemo(() => {
    const menu = [];
    if (showApproveRequest) {
      menu.push({
        key: "approve",
        label: <span data-testid="privacy-request-approve-btn">Approve</span>,
        onClick: openApproveConfirmationModal,
      });
    }

    if (showDenyRequest) {
      menu.push({
        key: "deny",
        label: <span data-testid="privacy-request-deny-btn">Deny</span>,
        onClick: openDenyConfirmationModal,
      });
    }

    if (showDownloadResults) {
      menu.push({
        key: "download",
        label: (
          <Tooltip
            title={isDownloadDisabled ? infoTooltip : null}
            placement="bottom"
          >
            <span data-testid="download-results-btn">
              Download request results
            </span>
          </Tooltip>
        ),
        onClick: downloadResults,
        disabled: isDownloadDisabled,
      });
    }

    if (isErrorStatus) {
      menu.push({
        key: "reprocess",
        label: (
          <span data-testid="privacy-request-action-reprocess">Reprocess</span>
        ),
      });
    }

    return menu;
  }, [
    showDownloadResults,
    isErrorStatus,
    downloadResults,
    infoTooltip,
    isDownloadDisabled,
    showApproveRequest,
    showDenyRequest,
    openApproveConfirmationModal,
    openDenyConfirmationModal,
  ]);

  return (
    <>
      <Dropdown
        menu={{ items: menuItems }}
        trigger={["click"]}
        data-testid="privacy-request-actions-dropdown"
      >
        <Button
          tabIndex={0}
          icon={<Icons.CaretDown />}
          data-testid="header-menu-button"
          iconPosition="end"
          type="primary"
          disabled={!menuItems.length}
        >
          Actions
        </Button>
      </Dropdown>
      <ApprovePrivacyRequestModal
        isOpen={isApproveModalOpen}
        isLoading={false}
        onClose={closeApproveModal}
        onApproveRequest={() => approveRequest({ reason: "" })}
        subjectRequest={privacyRequest}
      />
      <DenyPrivacyRequestModal
        isOpen={isDenyModalOpen}
        onClose={closeDenyModal}
        onDenyRequest={(reason) => denyRequest({ reason })}
      />
    </>
  );
};
export default PrivacyRequestActionsDropdown;

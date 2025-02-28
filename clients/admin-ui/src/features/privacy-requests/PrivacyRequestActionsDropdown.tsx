import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMenuProps as MenuProps,
  Icons,
} from "fidesui";
import { ComponentProps, useMemo } from "react";

import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { useFeatures } from "../common/features";
import { getActionTypes } from "../common/RequestType";
import { PrivacyRequestEntity } from "./types";

interface PrivacyRequestActionsDropdownProps {
  privacyRequest: PrivacyRequestEntity;
}

const PrivacyRequestActionsDropdown = ({
  privacyRequest,
}: PrivacyRequestActionsDropdownProps) => {
  const isPendingStatus =
    privacyRequest.status === PrivacyRequestStatus.PENDING;
  const isErrorStatus = privacyRequest.status === PrivacyRequestStatus.ERROR;

  const hasDownloadResultsFlagEnabled =
    useFeatures()?.flags?.downloadAccessRequestResults;
  const isActionRequest = getActionTypes(privacyRequest.policy.rules).includes(
    ActionType.ACCESS,
  );
  const showDownloadResults =
    hasDownloadResultsFlagEnabled &&
    isActionRequest &&
    privacyRequest.status === PrivacyRequestStatus.COMPLETE;

  const menuItems = useMemo(() => {
    const menu = [];
    if (isPendingStatus) {
      menu.push({
        key: "approve",
        label: (
          <span data-testid="privacy-request-action-approve">Approve</span>
        ),
      });
      menu.push({
        key: "deny",
        label: <span data-testid="privacy-request-action-deny">Deny</span>,
      });
    }
    if (showDownloadResults) {
      menu.push({
        key: "download",
        label: (
          <span data-testid="privacy-request-action-download">
            Download request results
            {/* <DownloadAccessResults /> */}
          </span>
        ),
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
  }, [showDownloadResults, isPendingStatus, isErrorStatus]);

  return (
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
  );
};
export default PrivacyRequestActionsDropdown;

import {
  Button,
  Icons,
  Space,
  Tooltip,
  useMessage,
  useNotification,
} from "fidesui";
import { truncate } from "lodash";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features/features.slice";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import ToastLink from "~/features/common/ToastLink";
import { DiffStatus } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

import {
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
} from "../../action-center.slice";
import { ActionCenterTabHash } from "../../hooks/useActionCenterTabs";
import { useConfirmPromotion } from "../../hooks/useConfirmPromotion";
import hasConsentComplianceIssue from "../../utils/hasConsentComplianceIssue";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  showComplianceIssueDetails?: (
    stagedResource: StagedResourceAPIResponse,
  ) => void;
  /** Render Approve/Ignore/Restore as icon-only buttons (datastore-style). */
  iconButtons?: boolean;
  /** Hide the compliance-issue warning button (e.g. in the drawer footer). */
  hideComplianceWarning?: boolean;
  /**
   * Render Approve as a filled primary button (website explorer). The fill
   * draws the eye to the next step once an asset has a system; the button is
   * still disabled until one is assigned.
   */
  primaryApprove?: boolean;
}

export const DiscoveredAssetActionsCell = ({
  asset,
  onTabChange,
  showComplianceIssueDetails,
  iconButtons,
  hideComplianceWarning,
  primaryApprove,
}: DiscoveredAssetActionsCellProps) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels: isConsentStatusFlagEnabled } = flags;
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const { confirmPromotion, isCheckingImpact } = useConfirmPromotion();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  const message = useMessage();
  const notification = useNotification();

  const router = useRouter();

  const anyActionIsLoading =
    isAddingResults ||
    isCheckingImpact ||
    isIgnoringResults ||
    isRestoringResults;

  const {
    urn,
    name,
    resource_type: type,
    diff_status: diffStatus,
    system_key: systemKey,
    user_assigned_system_key: userAssignedSystemKey,
    consent_aggregated: consentAggregated,
  } = asset;

  const truncatedAssetName = truncate(name || "", { length: 50 });

  // Check if the consent status is an error type
  const showConsentComplianceWarning =
    hasConsentComplianceIssue(consentAggregated);

  const handleAdd = async () => {
    const confirmed = await confirmPromotion([urn]);
    if (!confirmed) {
      return;
    }
    const result = await addMonitorResultAssetsMutation({ urnList: [urn] });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      const systemToLink = userAssignedSystemKey || systemKey;
      const href = `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`;
      notification.success({
        message: "Approved",
        description: `${type} "${truncatedAssetName}" has been added to the system inventory.`,
        actions: systemToLink ? (
          <ToastLink onClick={() => router.push(href)}>View</ToastLink>
        ) : undefined,
      });
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      notification.success({
        message: "Asset ignored",
        description: `${type} "${truncatedAssetName}" has been ignored and will not appear in future scans.`,
        actions: (
          <ToastLink
            onClick={async () => {
              await onTabChange(ActionCenterTabHash.IGNORED);
            }}
          >
            View
          </ToastLink>
        ),
      });
    }
  };

  const handleRestore = async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success(
        `${type} "${truncatedAssetName}" is no longer ignored and will appear in future scans.`,
      );
    }
  };

  const handleViewComplianceDetails = () => {
    showComplianceIssueDetails?.(asset);
  };

  // TODO [HJ-369] update disabled and tooltip logic once the categories of consent feature is implemented
  return (
    <Space>
      {diffStatus !== DiffStatus.MUTED && (
        <>
          <Tooltip
            title={
              !asset.system
                ? `This asset requires a system before you can approve it.`
                : "Approve"
            }
          >
            <Button
              data-testid="add-btn"
              size="small"
              type={primaryApprove ? "primary" : undefined}
              onClick={handleAdd}
              disabled={!asset.system || anyActionIsLoading}
              loading={isAddingResults}
              icon={iconButtons ? <Icons.Checkmark /> : undefined}
              aria-label="Approve"
            >
              {iconButtons ? undefined : "Approve"}
            </Button>
          </Tooltip>
          <Tooltip title={iconButtons ? "Ignore" : undefined}>
            <Button
              data-testid="ignore-btn"
              size="small"
              onClick={handleIgnore}
              disabled={anyActionIsLoading}
              loading={isIgnoringResults}
              icon={iconButtons ? <Icons.ViewOff /> : undefined}
              aria-label="Ignore"
            >
              {iconButtons ? undefined : "Ignore"}
            </Button>
          </Tooltip>
          {!hideComplianceWarning &&
            showConsentComplianceWarning &&
            isConsentStatusFlagEnabled && (
              <Button
                data-testid="view-compliance-details-btn"
                size="small"
                onClick={handleViewComplianceDetails}
                disabled={anyActionIsLoading}
                loading={isRestoringResults}
                icon={
                  <Icons.WarningAltFilled
                    style={{ color: "var(--fidesui-color-error)", width: 14 }}
                  />
                }
                title="View compliance issue"
                aria-label="View compliance issue"
              />
            )}
        </>
      )}
      {diffStatus === DiffStatus.MUTED && (
        <Tooltip title={iconButtons ? "Restore" : undefined}>
          <Button
            data-testid="restore-btn"
            size="small"
            onClick={handleRestore}
            disabled={anyActionIsLoading}
            loading={isRestoringResults}
            icon={iconButtons ? <Icons.View /> : undefined}
            aria-label="Restore"
          >
            {iconButtons ? undefined : "Restore"}
          </Button>
        </Tooltip>
      )}
    </Space>
  );
};

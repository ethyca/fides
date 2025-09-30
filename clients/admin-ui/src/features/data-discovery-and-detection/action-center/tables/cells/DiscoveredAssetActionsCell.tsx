import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
  Icons,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features/features.slice";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { DiffStatus } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

import {
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
} from "../../action-center.slice";
import { ActionCenterTabHash } from "../../hooks/useActionCenterTabs";
import { SuccessToastContent } from "../../SuccessToastContent";
import hasConsentComplianceIssue from "../../utils/hasConsentComplianceIssue";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  showComplianceIssueDetails?: (
    stagedResource: StagedResourceAPIResponse,
  ) => void;
}

export const DiscoveredAssetActionsCell = ({
  asset,
  onTabChange,
  showComplianceIssueDetails,
}: DiscoveredAssetActionsCellProps) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels: isConsentStatusFlagEnabled } = flags;
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  const toast = useToast();

  const router = useRouter();

  const anyActionIsLoading =
    isAddingResults || isIgnoringResults || isRestoringResults;

  const {
    urn,
    name,
    resource_type: type,
    diff_status: diffStatus,
    system_key: systemKey,
    user_assigned_system_key: userAssignedSystemKey,
    consent_aggregated: consentAggregated,
  } = asset;

  // Check if the consent status is an error type
  const showConsentComplianceWarning =
    hasConsentComplianceIssue(consentAggregated);

  const handleAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      const systemToLink = userAssignedSystemKey || systemKey;
      const href = `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`;
      toast(
        successToastParams(
          SuccessToastContent(
            `${type} "${name}" has been added to the system inventory.`,
            systemToLink ? () => router.push(href) : undefined,
          ),
        ),
      );
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${type} "${name}" has been ignored and will not appear in future scans.`,
            async () => {
              await onTabChange(ActionCenterTabHash.IGNORED);
            },
          ),
        ),
      );
    }
  };

  const handleRestore = async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `${type} "${name}" is no longer ignored and will appear in future scans.`,
        ),
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
                ? `This asset requires a system before you can add it to the inventory.`
                : undefined
            }
          >
            <Button
              data-testid="add-btn"
              size="small"
              onClick={handleAdd}
              disabled={!asset.system || anyActionIsLoading}
              loading={isAddingResults}
            >
              Add
            </Button>
          </Tooltip>
          <Button
            data-testid="ignore-btn"
            size="small"
            onClick={handleIgnore}
            disabled={anyActionIsLoading}
            loading={isIgnoringResults}
          >
            Ignore
          </Button>
          {showConsentComplianceWarning && isConsentStatusFlagEnabled && (
            <Button
              data-testid="view-compliance-details-btn"
              size="small"
              onClick={handleViewComplianceDetails}
              disabled={anyActionIsLoading}
              loading={isRestoringResults}
              icon={
                <Icons.WarningAltFilled
                  style={{ color: "var(--fidesui-error)", width: 14 }}
                />
              }
              title="View compliance issue"
              aria-label="View compliance issue"
            />
          )}
        </>
      )}
      {diffStatus === DiffStatus.MUTED && (
        <Button
          data-testid="restore-btn"
          size="small"
          onClick={handleRestore}
          disabled={anyActionIsLoading}
          loading={isRestoringResults}
        >
          Restore
        </Button>
      )}
    </Space>
  );
};

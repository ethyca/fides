import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { getIndexFromHash } from "~/features/data-discovery-and-detection/action-center/tables/useActionCenterTabs";
import { successToastContent } from "~/features/data-discovery-and-detection/action-center/utils/successToastContent";
import { DiffStatus } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

import {
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
} from "../../action-center.slice";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
  onTabChange: (index: number) => void;
}

export const DiscoveredAssetActionsCell = ({
  asset,
  onTabChange,
}: DiscoveredAssetActionsCellProps) => {
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
  } = asset;

  const handleAdd = async () => {
    const systemToLink = userAssignedSystemKey || systemKey;
    const href = `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`;
    const result = await addMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          successToastContent(
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
          successToastContent(
            `${type} "${name}" has been ignored and will not appear in future scans.`,
            () => onTabChange(getIndexFromHash("#ignored")!),
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

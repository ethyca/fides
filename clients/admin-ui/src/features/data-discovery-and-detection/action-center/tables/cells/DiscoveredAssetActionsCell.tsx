import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { DiffStatus } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

import {
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
} from "../../action-center.slice";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
}

export const DiscoveredAssetActionsCell = ({
  asset,
}: DiscoveredAssetActionsCellProps) => {
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  const { successAlert, errorAlert } = useAlert();

  const anyActionIsLoading =
    isAddingResults || isIgnoringResults || isRestoringResults;

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { urn, name, resource_type: type, diff_status } = asset;

  const handleAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `${type} "${name}" has been added to the system inventory.`,
        `Confirmed`,
      );
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `${type} "${name}" has been ignored and will not appear in future scans.`,
        `Ignored`,
      );
    }
  };

  const handleRestore = async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `${type} "${name}" is no longer ignored and will appear in future scans.`,
        `Restored`,
      );
    }
  };

  // TODO [HJ-369] update disabled and tooltip logic once the categories of consent feature is implemented
  return (
    <Space>
      {diff_status !== DiffStatus.MUTED && (
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
      {diff_status === DiffStatus.MUTED && (
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

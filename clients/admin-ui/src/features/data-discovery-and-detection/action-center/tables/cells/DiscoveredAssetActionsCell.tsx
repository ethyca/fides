import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { StagedResourceAPIResponse } from "~/types/api";

import {
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
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

  const { successAlert, errorAlert } = useAlert();

  const anyActionIsLoading = isAddingResults || isIgnoringResults;

  const { urn, name, resource_type: type } = asset;

  const handleAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      errorAlert("There was adding the asset to the system inventory");
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
        `${type} "${name}" has been ignored and will not be added to the system inventory.`,
        `Ignored`,
      );
    }
  };

  // TODO [HJ-369] update disabled and tooltip logic once the categories of consent feature is implemented
  return (
    <Space>
      <Tooltip
        title={
          !asset.system_id
            ? `This asset requires a system before you can add it to the inventory.`
            : undefined
        }
      >
        <Button
          data-testid="add-btn"
          size="small"
          onClick={handleAdd}
          disabled={!asset.system_id || anyActionIsLoading}
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
    </Space>
  );
};

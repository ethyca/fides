import { AntButton as Button, AntSpace as Space } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import { StagedResourceAPIResponse } from "~/types/api";

import {
  useAddMonitorResultsMutation,
  useIgnoreMonitorResultsMutation,
} from "../../action-center.slice";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
}

export const DiscoveredAssetActionsCell = ({
  asset,
}: DiscoveredAssetActionsCellProps) => {
  const [addMonitorResultsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultsMutation();
  const [ignoreMonitorResultsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultsMutation();

  const { successAlert } = useAlert();

  const anyActionIsLoading = isAddingResults || isIgnoringResults;

  const { urn, name, resource_type: type } = asset;

  const handleAdd = async () => {
    await addMonitorResultsMutation({
      urnList: [urn],
    });
    successAlert(
      `${type} "${name}" has been added to the system inventory.`,
      `Confirmed`,
    );
  };

  const handleIgnore = async () => {
    await ignoreMonitorResultsMutation({
      urnList: [urn],
    });
    successAlert(
      `${type} "${name}" has been ignored and will not be added to the system inventory.`,
      `Ignored`,
    );
  };

  return (
    <Space>
      <Button
        data-testid="add-btn"
        size="small"
        onClick={handleAdd}
        disabled={anyActionIsLoading}
        loading={isAddingResults}
      >
        Add
      </Button>
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

import { AntButton as Button } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import {
  CatalogResourceStatus,
  getCatalogResourceStatus,
} from "~/features/data-catalog/utils";
import {
  useConfirmResourceMutation,
  usePromoteResourceMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogResourceActionsCell = ({
  resource,
}: {
  resource: StagedResourceAPIResponse;
}) => {
  const { successAlert } = useAlert();
  const status = getCatalogResourceStatus(resource);
  const [confirmResource, { isLoading: classifyIsLoading }] =
    useConfirmResourceMutation();
  const [promoteResource, { isLoading: approveIsLoading }] =
    usePromoteResourceMutation();

  const classifyResource = async () => {
    await confirmResource({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      unmute_children: true,
      classify_monitored_resources: true,
    });
    successAlert(
      `Started classification on ${resource.name ?? "this resource"}`,
    );
  };

  const approveResource = async () => {
    await promoteResource({
      staged_resource_urn: resource.urn,
    });
    successAlert(`Approved ${resource.name ?? "this resource"}`);
  };

  const anyActionIsLoading = classifyIsLoading || approveIsLoading;

  return (
    <>
      {status === CatalogResourceStatus.ATTENTION_REQUIRED && (
        <Button
          size="small"
          onClick={classifyResource}
          loading={classifyIsLoading}
          disabled={anyActionIsLoading}
        >
          Classify
        </Button>
      )}
      {status === CatalogResourceStatus.IN_REVIEW && (
        <Button
          size="small"
          onClick={approveResource}
          loading={approveIsLoading}
          disabled={anyActionIsLoading}
        >
          Approve
        </Button>
      )}
    </>
  );
};

export default CatalogResourceActionsCell;

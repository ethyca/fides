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
import ToastLink from "~/features/common/ToastLink";
import { DiffStatus } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

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

  const toast = useToast();

  const router = useRouter();

  const addSuccessToastContent = (
    type: string,
    name: string,
    systemKey?: string,
  ) => (
    <>
      {`${type} "${name}" has been added to the system inventory.`}
      {systemKey && (
        <ToastLink
          onClick={() => router.push(`${SYSTEM_ROUTE}/configure/${systemKey}`)}
        >
          View
        </ToastLink>
      )}
    </>
  );

  const anyActionIsLoading = isAddingResults || isIgnoringResults;

  // TODO: get system key to navigate
  const { urn, name, resource_type: type, diff_status: diffStatus } = asset;

  const handleAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          addSuccessToastContent(type as string, name as string),
        ),
      );
    }
  };

  // TODO: add toast link to ignored tab
  const handleIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `${type} "${name}" has been ignored and will not appear in future scans.`,
        ),
      );
    }
  };

  // TODO [HJ-369] update disabled and tooltip logic once the categories of consent feature is implemented
  return (
    <Space>
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
      {diffStatus !== DiffStatus.MUTED && (
        <Button
          data-testid="ignore-btn"
          size="small"
          onClick={handleIgnore}
          disabled={anyActionIsLoading}
          loading={isIgnoringResults}
        >
          Ignore
        </Button>
      )}
      <Button
        size="small"
        onClick={() =>
          toast(
            successToastParams(
              addSuccessToastContent(type as string, name as string),
            ),
          )
        }
      >
        Test toast
      </Button>
    </Space>
  );
};

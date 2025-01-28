import { AntButton, EditIcon, Icons } from "fidesui";
import { useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";
import ClassificationCategoryBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import { useUpdateResourceCategoryMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { StagedResourceAPIResponse } from "~/types/api";

interface SystemCellProps {
  aggregateSystem: StagedResourceAPIResponse;
  monitorConfigId: string;
}

export const SystemCell = ({
  aggregateSystem,
  monitorConfigId,
}: SystemCellProps) => {
  const {
    resource_type: assetType,
    name: assetName,
    urn,
    system: systemName,
  } = aggregateSystem;
  const [isEditing, setIsEditing] = useState(false);
  const [updateResourceCategoryMutation, { isLoading }] =
    useUpdateResourceCategoryMutation();

  const { successAlert, errorAlert } = useAlert();

  const handleSelectSystem = async (
    fidesKey: string,
    newSystemName: string,
    isNewSystem?: boolean,
  ) => {
    const result = await updateResourceCategoryMutation({
      staged_resource_urn: urn,
      monitor_config_id: monitorConfigId,
      system_key: fidesKey,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        isNewSystem
          ? `${newSystemName} has been added to your system inventory and the ${assetType} "${assetName}" has been assigned to that system.`
          : `${assetType} "${assetName}" has been assigned to ${newSystemName}.`,
        `Confirmed`,
      );
    }
    setIsEditing(false);
  };

  return (
    <>
      {!isEditing && (
        <div style={getTableTHandTDStyles()}>
          {systemName ? (
            <ClassificationCategoryBadge
              onClick={() => setIsEditing(true)}
              data-testid="system-badge"
            >
              <>
                {systemName}
                <EditIcon />
              </>
            </ClassificationCategoryBadge>
          ) : (
            <AntButton
              size="small"
              type="text"
              aria-label="add"
              icon={<Icons.Add />}
              onClick={() => setIsEditing(true)}
              data-testid="add-system-btn"
            />
          )}
        </div>
      )}
      {!!isEditing && (
        <SystemSelect
          variant="borderless"
          className="w-full"
          autoFocus
          defaultOpen
          onBlur={() => setIsEditing(false)}
          onSelect={(fidesKey: string, option) =>
            handleSelectSystem(fidesKey, option.label as string)
          }
          loading={isLoading}
        />
      )}
    </>
  );
};

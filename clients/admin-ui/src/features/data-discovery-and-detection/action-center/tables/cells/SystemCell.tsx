import { AntButton, EditIcon, Icons } from "fidesui";
import { useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";
import ClassificationCategoryBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import { useUpdateResourceCategoryMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";

interface SystemCellProps {
  urn: string;
  systemName: string | undefined | null;
  monitorConfigId: string;
}

export const SystemCell = ({
  urn,
  systemName,
  monitorConfigId,
}: SystemCellProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [updateResourceCategoryMutation, { isLoading }] =
    useUpdateResourceCategoryMutation();

  const handleSelectSystem = async (fidesKey: string) => {
    await updateResourceCategoryMutation({
      staged_resource_urn: urn,
      monitor_config_id: monitorConfigId,
      system_key: fidesKey,
    });
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
          onSelect={handleSelectSystem}
          loading={isLoading}
        />
      )}
    </>
  );
};

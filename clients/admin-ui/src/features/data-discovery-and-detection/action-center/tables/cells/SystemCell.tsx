import { AntTag as Tag, Icons } from "fidesui";
import { MouseEventHandler, useCallback, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import styles from "~/features/common/table/cells/Cells.module.scss";
import { useUpdateResourceCategoryMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";
import { StagedResourceAPIResponse } from "~/types/api";

interface SystemCellProps {
  aggregateSystem: StagedResourceAPIResponse;
  monitorConfigId: string;
  readonly?: boolean;
}

export const SystemCell = ({
  aggregateSystem,
  monitorConfigId,
  readonly,
}: SystemCellProps) => {
  const {
    resource_type: assetType,
    name: assetName,
    urn,
    system: systemName,
    user_assigned_system_key: userAssignedSystemKey,
    system_key: systemKey,
  } = aggregateSystem;
  const [isEditing, setIsEditing] = useState(false);
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);
  const [updateResourceCategoryMutation, { isLoading }] =
    useUpdateResourceCategoryMutation();
  const { successAlert, errorAlert } = useAlert();

  const onAddSystem: MouseEventHandler<HTMLButtonElement> = useCallback((e) => {
    e.preventDefault();
    setIsNewSystemModalOpen(true);
  }, []);

  const handleCloseNewSystemModal = () => {
    setIsNewSystemModalOpen(false);
  };

  const handleSelectSystem = async (
    fidesKey: string,
    newSystemName: string,
    isNewSystem?: boolean,
  ) => {
    const result = await updateResourceCategoryMutation({
      staged_resource_urn: urn,
      monitor_config_id: monitorConfigId,
      user_assigned_system_key: fidesKey,
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

  const currentSystemKey = userAssignedSystemKey || systemKey;

  if (readonly) {
    return systemName ? (
      <Tag data-testid="system-badge" color="white">
        {systemName}
      </Tag>
    ) : null;
  }

  return (
    <>
      {!isEditing &&
        (systemName ? (
          <Tag onClick={() => setIsEditing(true)} data-testid="system-badge">
            {systemName}
            <Icons.Edit />
          </Tag>
        ) : (
          <Tag
            onClick={() => setIsEditing(true)}
            data-testid="add-system-btn"
            addable
          />
        ))}
      {!!isEditing && (
        <div className={styles.cellBleed}>
          <SystemSelect
            variant="borderless"
            autoFocus
            defaultOpen
            defaultValue={currentSystemKey}
            onBlur={(e) => {
              // Close the dropdown unless the user is clicking the "Add new system" button, otherwise it won't open the modal
              if (e.relatedTarget?.getAttribute("id") !== "add-new-system") {
                setIsEditing(false);
              }
            }}
            onAddSystem={onAddSystem}
            onSelect={(fidesKey: string, option) =>
              handleSelectSystem(fidesKey, option.label as string)
            }
            loading={isLoading}
          />
        </div>
      )}
      {isNewSystemModalOpen && (
        <AddNewSystemModal
          isOpen
          onClose={handleCloseNewSystemModal}
          onSuccessfulSubmit={(fidesKey, name) =>
            handleSelectSystem(fidesKey, name, true)
          }
        />
      )}
    </>
  );
};

import {
  AntTag as Tag,
  ConfirmationModal,
  Icons,
  useDisclosure,
} from "fidesui";
import { MouseEventHandler, useCallback, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";
import { useUpdateSystemAssetsMutation } from "~/features/system/system-assets.slice";
import { Asset } from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface SystemUpdateParams {
  newSystemKey: string;
  newSystemName: string;
  isNewSystem?: boolean;
}

interface AssetSystemCellProps {
  systemKey: string;
  systemName: string;
  asset: Asset;
  readonly?: boolean;
}

const AssetSystemCell = ({
  systemKey,
  systemName,
  asset,
  readonly,
}: AssetSystemCellProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [updateParams, setUpdateParams] = useState<
    SystemUpdateParams | undefined
  >();
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);
  const [updateAsset, { isLoading }] = useUpdateSystemAssetsMutation();
  const { successAlert, errorAlert } = useAlert();

  const confirmationModal = useDisclosure();

  const { asset_type: assetType, name: assetName } = asset;

  const onAddSystem: MouseEventHandler<HTMLButtonElement> = useCallback((e) => {
    e.preventDefault();
    setIsNewSystemModalOpen(true);
  }, []);

  const reassignSystem = async (params?: SystemUpdateParams) => {
    if (!params) {
      return;
    }
    const { newSystemKey, newSystemName, isNewSystem } = params;
    const result = await updateAsset({
      systemKey,
      assets: [{ id: asset.id, system_key: newSystemKey }],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        isNewSystem
          ? `${newSystemName} has been added to your system inventory and the ${assetType} "${assetName}" has been assigned to that system.`
          : `${assetType} ${assetName} has been assigned to ${newSystemName}`,
      );
    }
    setIsEditing(false);
    setUpdateParams(undefined);
  };

  const handleSystemSelected = (params: SystemUpdateParams) => {
    setUpdateParams(params);
    confirmationModal.onOpen();
  };

  if (readonly) {
    return (
      <Tag data-testid="system-badge" color="white">
        {systemName}
      </Tag>
    );
  }

  return (
    <>
      {!isEditing && (
        <Tag
          data-testid="system-badge"
          color="white"
          onClick={() => setIsEditing(true)}
        >
          {systemName} <Icons.Edit />
        </Tag>
      )}
      {!!isEditing && (
        <SystemSelect
          variant="borderless"
          className="w-full"
          autoFocus
          defaultOpen
          defaultValue={systemKey}
          onBlur={(e) => {
            if (e.relatedTarget?.getAttribute("id") !== "add-new-system") {
              setIsEditing(false);
            }
          }}
          onAddSystem={onAddSystem}
          onSelect={(fidesKey, option) =>
            handleSystemSelected({
              newSystemKey: fidesKey,
              newSystemName: option.label as string,
            })
          }
          loading={isLoading}
        />
      )}
      {isNewSystemModalOpen && (
        <AddNewSystemModal
          isOpen
          onClose={() => setIsNewSystemModalOpen(false)}
          onSuccessfulSubmit={(fidesKey, name) =>
            handleSystemSelected({
              newSystemKey: fidesKey,
              newSystemName: name,
              isNewSystem: true,
            })
          }
        />
      )}
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        onClose={confirmationModal.onClose}
        onConfirm={() => {
          reassignSystem(updateParams);
        }}
        title="Reassign asset"
        message={`Are you sure you want to reassign this asset to ${updateParams?.newSystemName}?`}
        isCentered
      />
    </>
  );
};

export default AssetSystemCell;

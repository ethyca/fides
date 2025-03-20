import {
  AntButton,
  AntFlex,
  ConfirmationModal,
  useDisclosure,
  useToast,
} from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useDeleteSystemAssetsMutation } from "~/features/system/system-assets.slice";
import { Asset } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const SystemAssetActionsCell = ({
  asset,
  systemKey,
  onEditClick,
}: {
  asset: Asset;
  systemKey: string;
  onEditClick: () => void;
}) => {
  const [deleteAsset, { isLoading: isDeleting }] =
    useDeleteSystemAssetsMutation();

  const toast = useToast();
  const { isOpen, onClose, onOpen } = useDisclosure();

  const handleDelete = async () => {
    const result = await deleteAsset({
      systemKey,
      asset_ids: [asset.id],
    });
    if (isErrorResult(result)) {
      toast(
        errorToastParams(
          getErrorMessage(
            result.error,
            "A problem occurred removing this asset.  Please try again",
          ),
        ),
      );
    } else {
      toast(successToastParams("Asset removed successfully"));
    }
  };

  return (
    <AntFlex className="gap-1">
      <AntButton size="small" onClick={onEditClick} data-testid="edit-btn">
        Edit
      </AntButton>
      <AntButton
        size="small"
        onClick={onOpen}
        loading={isDeleting}
        data-testid="remove-btn"
      >
        Remove
      </AntButton>
      <ConfirmationModal
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={handleDelete}
        title="Remove asset"
        message="Are you sure you want to ignore the selected assets? This action cannot be undone and may impact consent automation."
        isCentered
      />
    </AntFlex>
  );
};

export default SystemAssetActionsCell;

import { useMessage, useModal } from "fidesui";
import React from "react";

import { getErrorMessage } from "~/features/common/helpers";
import Restrict from "~/features/common/Restrict";
import {
  DataPurpose,
  useDeleteDataPurposeMutation,
} from "~/features/data-purposes/data-purpose.slice";
import { ScopeRegistryEnum } from "~/types/api";
import { RTKErrorResult } from "~/types/errors/api";

interface Props {
  purpose: DataPurpose;
  triggerComponent: React.ReactElement<{
    onClick?: (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
  }>;
}

const DeleteDataPurposeModal = ({ purpose, triggerComponent }: Props) => {
  const message = useMessage();
  const modal = useModal();
  const [deleteDataPurpose] = useDeleteDataPurposeMutation();

  const handleModalOpen = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.stopPropagation();
    modal.confirm({
      title: `Delete ${purpose.name}`,
      content: (
        <span className="text-gray-500">
          You are about to delete data purpose &quot;{purpose.name}&quot;. This
          action is not reversible. Are you sure you want to proceed?
        </span>
      ),
      okText: "Delete",
      centered: true,
      onOk: async () => {
        try {
          await deleteDataPurpose({
            fidesKey: purpose.fides_key,
            force: true,
          }).unwrap();
          message.success(
            `Data purpose "${purpose.name}" deleted successfully`,
          );
        } catch (error) {
          message.error(getErrorMessage(error as RTKErrorResult["error"]));
        }
      },
    });
  };

  return (
    <Restrict scopes={[ScopeRegistryEnum.DATA_PURPOSE_DELETE]}>
      <span>
        {React.cloneElement(triggerComponent, {
          onClick: handleModalOpen,
        })}
      </span>
    </Restrict>
  );
};

export default DeleteDataPurposeModal;

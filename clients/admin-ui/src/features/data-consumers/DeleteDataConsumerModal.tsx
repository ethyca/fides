import { Button, useMessage, useModal } from "fidesui";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";

import {
  DataConsumer,
  useDeleteDataConsumerMutation,
} from "./data-consumer.slice";

interface Props {
  consumer: DataConsumer;
}

const DeleteDataConsumerModal = ({ consumer }: Props) => {
  const message = useMessage();
  const modal = useModal();
  const router = useRouter();
  const [deleteDataConsumer] = useDeleteDataConsumerMutation();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    modal.confirm({
      title: `Delete ${consumer.name}`,
      content: `You are about to delete data consumer "${consumer.name}". This action is not reversible. Are you sure you want to proceed?`,
      okText: "Delete",
      okType: "danger",
      centered: true,
      onOk: async () => {
        try {
          await deleteDataConsumer(consumer.id).unwrap();
          message.success(
            `Data consumer "${consumer.name}" deleted successfully`,
          );
          router.push(DATA_CONSUMERS_ROUTE);
        } catch (error) {
          message.error(getErrorMessage(error as any));
        }
      },
    });
  };

  return (
    <Button
      aria-label="Delete data consumer"
      data-testid="delete-data-consumer-button"
      size="small"
      icon={<TrashCanOutlineIcon />}
      onClick={handleDelete}
    />
  );
};

export default DeleteDataConsumerModal;

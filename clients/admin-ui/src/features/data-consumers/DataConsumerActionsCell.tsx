import { Button, Flex, Icons } from "fidesui";
import { useRouter } from "next/router";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { DataConsumer } from "./data-consumer.slice";
import DeleteDataConsumerModal from "./DeleteDataConsumerModal";

interface Props {
  consumer: DataConsumer;
}

const DataConsumerActionsCell = ({ consumer }: Props) => {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`${DATA_CONSUMERS_ROUTE}/${consumer.id}`);
  };

  return (
    <Flex gap="small">
      <Restrict scopes={[ScopeRegistryEnum.DATA_CONSUMER_UPDATE]}>
        <Button
          aria-label="Edit data consumer"
          data-testid="edit-data-consumer-button"
          size="small"
          icon={<Icons.Edit />}
          onClick={handleEdit}
        />
      </Restrict>
      <Restrict scopes={[ScopeRegistryEnum.DATA_CONSUMER_DELETE]}>
        <DeleteDataConsumerModal consumer={consumer} />
      </Restrict>
    </Flex>
  );
};

export default DataConsumerActionsCell;

import { Button, Flex, Icons } from "fidesui";
import { useRouter } from "next/router";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { DataPurpose } from "~/features/data-purposes/data-purpose.slice";
import DeleteDataPurposeModal from "~/features/data-purposes/DeleteDataPurposeModal";
import { ScopeRegistryEnum } from "~/types/api";

interface Props {
  purpose: DataPurpose;
}

const DataPurposeActionsCell = ({ purpose }: Props) => {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`${DATA_PURPOSES_ROUTE}/${purpose.fides_key}`);
  };

  return (
    <Flex gap="small">
      <Restrict scopes={[ScopeRegistryEnum.DATA_PURPOSE_UPDATE]}>
        <Button
          aria-label="Edit purpose"
          data-testid="edit-data-purpose-button"
          size="small"
          icon={<Icons.Edit />}
          onClick={handleEdit}
        />
      </Restrict>
      <DeleteDataPurposeModal
        purpose={purpose}
        triggerComponent={
          <Button
            aria-label="Delete purpose"
            data-testid="delete-data-purpose-button"
            size="small"
            icon={<Icons.TrashCan />}
          />
        }
      />
    </Flex>
  );
};

export default DataPurposeActionsCell;

import { Button, Drawer } from "fidesui";

import { InfoHeading, InfoText } from "~/features/common/copy/components";
import EditDataUseCell from "~/features/data-catalog/systems/EditDataUseCell";
import { SystemResponse, SystemWithMonitorKeys } from "~/types/api";

const CatalogSystemDetailDrawer = ({
  system,
  onEdit,
  onClose,
}: {
  system?: SystemWithMonitorKeys;
  onEdit: () => void;
  onClose: () => void;
}) => {
  return (
    <Drawer
      open={!!system}
      onClose={onClose}
      title={system?.name || system?.fides_key}
      footer={
        <Button onClick={onEdit} data-testid="edit-system-btn">
          Edit system
        </Button>
      }
    >
      <div data-testid="system-details">
        <InfoHeading text="Title" mt={0} />
        <InfoText>{system?.name ?? system?.fides_key}</InfoText>
        {system?.description && (
          <>
            <InfoHeading text="Description" />
            <InfoText>{system?.description}</InfoText>
          </>
        )}
        <InfoHeading text="Data uses" />
        <EditDataUseCell system={system as SystemResponse} />
      </div>
    </Drawer>
  );
};

export default CatalogSystemDetailDrawer;

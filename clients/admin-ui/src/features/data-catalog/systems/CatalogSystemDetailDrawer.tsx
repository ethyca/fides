import {
  AntButton as Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
} from "fidesui";

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
    <Drawer isOpen={!!system} onClose={onClose} size="md">
      <DrawerOverlay />
      <DrawerContent data-testid="system-details">
        <DrawerHeader>{system?.name || system?.fides_key}</DrawerHeader>
        <DrawerCloseButton />
        <DrawerBody>
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
        </DrawerBody>
        <DrawerFooter>
          <Button onClick={onEdit} data-testid="edit-system-btn">
            Edit system
          </Button>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
};

export default CatalogSystemDetailDrawer;

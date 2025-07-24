import {
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
} from "fidesui";

import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogDatasetDetailDrawer = ({
  dataset,
  onClose,
}: {
  dataset?: StagedResourceAPIResponse;
  onClose: () => void;
}) => (
  <Drawer isOpen={!!dataset} onClose={onClose} size="md">
    <DrawerOverlay />
    <DrawerContent>
      <DrawerHeader>{dataset?.name || dataset?.urn}</DrawerHeader>
      <DrawerCloseButton />
      <DrawerBody>
        <InfoHeading text="Title" mt={0} />
        <InfoText>{dataset?.name ?? dataset?.urn}</InfoText>
        {dataset?.description && (
          <>
            <InfoHeading text="Description" />
            <InfoText>{dataset?.description}</InfoText>
          </>
        )}
      </DrawerBody>
    </DrawerContent>
  </Drawer>
);

export default CatalogDatasetDetailDrawer;

import {
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
} from "fidesui";

import { InfoHeading, InfoText } from "~/features/common/copy/components";
import {
  CatalogResourceStatus,
  getCatalogResourceStatus,
} from "~/features/data-catalog/utils";
import EditCategoryCell from "~/features/data-discovery-and-detection/tables/cells/EditCategoryCell";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogResourceDetailDrawer = ({
  resource,
  onClose,
}: {
  resource?: StagedResourceAPIResponse;
  onClose: () => void;
}) => {
  const resourceType = findResourceType(resource);
  const status = getCatalogResourceStatus(resource);

  const showDataCategories =
    (resourceType === StagedResourceType.FIELD ||
      resourceType === StagedResourceType.TABLE) &&
    status === CatalogResourceStatus.IN_REVIEW;

  return (
    <Drawer isOpen={!!resource} onClose={onClose} size="md">
      <DrawerOverlay />
      <DrawerContent data-testid="resource-details">
        <DrawerHeader>{resource?.name || resource?.urn}</DrawerHeader>
        <DrawerCloseButton />
        <DrawerBody>
          <InfoHeading text="Title" mt={0} />
          <InfoText>{resource?.name ?? resource?.urn}</InfoText>
          {resource?.description && (
            <>
              <InfoHeading text="Description" />
              <InfoText>{resource?.description}</InfoText>
            </>
          )}
          {showDataCategories && (
            <>
              <InfoHeading text="Data categories" />
              <EditCategoryCell resource={resource!} />
            </>
          )}
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
};

export default CatalogResourceDetailDrawer;

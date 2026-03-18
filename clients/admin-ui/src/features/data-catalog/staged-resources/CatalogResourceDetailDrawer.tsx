import { Drawer } from "fidesui";

import { InfoHeading, InfoText } from "~/features/common/copy/components";
import {
  CatalogResourceStatus,
  getCatalogResourceStatus,
} from "~/features/data-catalog/utils";
import EditCategoryCell from "~/features/data-discovery-and-detection/tables/cells/EditCategoryCell";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import {
  StagedResourceAPIResponse,
  StagedResourceTypeValue,
} from "~/types/api";

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
    (resourceType === StagedResourceTypeValue.FIELD ||
      resourceType === StagedResourceTypeValue.TABLE) &&
    status === CatalogResourceStatus.CLASSIFIED;

  return (
    <Drawer
      open={!!resource}
      onClose={onClose}
      title={resource?.name || resource?.urn}
    >
      <section data-testid="resource-details">
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
      </section>
    </Drawer>
  );
};

export default CatalogResourceDetailDrawer;

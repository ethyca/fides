import { Drawer } from "fidesui";

import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogDatasetDetailDrawer = ({
  dataset,
  onClose,
}: {
  dataset?: StagedResourceAPIResponse;
  onClose: () => void;
}) => (
  <Drawer
    open={!!dataset}
    onClose={onClose}
    title={dataset?.name || dataset?.urn}
  >
    <InfoHeading text="Title" mt={0} />
    <InfoText>{dataset?.name ?? dataset?.urn}</InfoText>
    {dataset?.description && (
      <>
        <InfoHeading text="Description" />
        <InfoText>{dataset?.description}</InfoText>
      </>
    )}
  </Drawer>
);

export default CatalogDatasetDetailDrawer;

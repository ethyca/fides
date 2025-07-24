import { DefaultCell } from "~/features/common/table/v2";
import getResourceName from "~/features/data-discovery-and-detection/utils/getResourceName";
import resourceHasChildren from "~/features/data-discovery-and-detection/utils/resourceHasChildren";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogResourceNameCell = ({
  resource,
}: {
  resource: StagedResourceAPIResponse;
}) => {
  return (
    <DefaultCell
      value={getResourceName(resource)}
      fontWeight={resourceHasChildren(resource) ? "semibold" : "normal"}
    />
  );
};

export default CatalogResourceNameCell;

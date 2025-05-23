import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { BadgeCellExpandable } from "~/features/common/table/v2/cells";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

const DiscoveredSystemDataUseCell = ({
  system,
}: {
  system: SystemStagedResourcesAggregateRecord;
}) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const consentCategories =
    system.data_uses?.filter((use) => isConsentCategory(use)) ?? [];
  const cellValues = consentCategories.map((use) => ({
    label: getDataUseDisplayName(use),
    key: use,
  }));

  return <BadgeCellExpandable values={cellValues} />;
};

export default DiscoveredSystemDataUseCell;

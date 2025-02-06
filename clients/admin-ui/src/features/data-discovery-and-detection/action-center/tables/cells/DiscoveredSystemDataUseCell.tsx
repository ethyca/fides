import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { BadgeCellExpandable } from "~/features/common/table/v2/cells";
import { MonitorSystemAggregate } from "~/features/data-discovery-and-detection/action-center/types";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";

const DiscoveredSystemDataUseCell = ({
  system,
}: {
  system: MonitorSystemAggregate;
}) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const consentCategories =
    system.data_uses?.filter((use) => isConsentCategory(use)) ?? [];
  const cellValues = consentCategories.map((use) => ({
    label: getDataUseDisplayName(use),
    key: use,
  }));

  return (
    <BadgeCellExpandable
      values={cellValues}
      bgColor="white"
      borderWidth="1px"
      borderColor="gray.200"
    />
  );
};

export default DiscoveredSystemDataUseCell;

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";
import { ColumnState } from "~/features/common/table/cells/types";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

const DiscoveredSystemDataUseCell = ({
  system,
  columnState,
}: {
  system: SystemStagedResourcesAggregateRecord;
  columnState?: ColumnState;
}) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const consentCategories =
    system.data_uses?.filter((use) => isConsentCategory(use)) ?? [];
  const cellValues = consentCategories.map((use) => ({
    label: getDataUseDisplayName(use),
    key: use,
  }));

  return <TagExpandableCell values={cellValues} columnState={columnState} />;
};

export default DiscoveredSystemDataUseCell;

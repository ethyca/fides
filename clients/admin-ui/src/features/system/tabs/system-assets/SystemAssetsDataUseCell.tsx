import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { BadgeCellExpandable } from "~/features/common/table/v2/cells";

const SystemAssetsDataUseCell = ({ values }: { values?: string[] }) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const cellValues =
    values?.map((use) => ({
      label: getDataUseDisplayName(use),
      key: use,
    })) ?? [];

  return (
    <BadgeCellExpandable
      values={cellValues}
      bgColor="white"
      borderWidth="1px"
      borderColor="gray.200"
    />
  );
};

export default SystemAssetsDataUseCell;

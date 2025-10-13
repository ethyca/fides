import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import {
  TagExpandableCell,
  TagExpandableCellProps,
} from "~/features/common/table/cells";
import { PrivacyDeclaration } from "~/types/api";

const SystemDataUseCell = ({
  privacyDeclarations,
  ...props
}: Omit<TagExpandableCellProps, "values"> & {
  privacyDeclarations: PrivacyDeclaration[];
}) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const dataUses = privacyDeclarations.map(
    (declaration) => declaration.data_use,
  );
  const cellValues = dataUses.map((use) => ({
    label: getDataUseDisplayName(use),
    key: use,
  }));
  return <TagExpandableCell values={cellValues} {...props} />;
};

export default SystemDataUseCell;

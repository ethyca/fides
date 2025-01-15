import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const DataUseSelect = ({
  selectedTaxonomies,
  showDisabled = false,
  ...props
}: TaxonomySelectProps) => {
  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();

  const getActiveDataUses = () => getDataUses().filter((du) => du.active);

  const dataUses = showDisabled ? getDataUses() : getActiveDataUses();

  const options: TaxonomySelectOption[] = dataUses
    .filter((dataUse) => !selectedTaxonomies.includes(dataUse.fides_key))
    .map((dataUse) => {
      const { name, primaryName } = getDataUseDisplayNameProps(
        dataUse.fides_key,
      );
      return {
        value: dataUse.fides_key,
        name,
        primaryName,
        description: dataUse.description || "",
      };
    });

  return <TaxonomySelect options={options} {...props} />;
};

export default DataUseSelect;

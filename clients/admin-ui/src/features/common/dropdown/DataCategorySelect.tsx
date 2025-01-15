import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const DataCategorySelect = ({
  selectedTaxonomies,
  showDisabled = false,
  ...props
}: TaxonomySelectProps) => {
  const { getDataCategoryDisplayNameProps, getDataCategories } =
    useTaxonomies();

  const getActiveDataCategories = () =>
    getDataCategories().filter((c) => c.active);

  const dataCategories = showDisabled
    ? getDataCategories()
    : getActiveDataCategories();

  const options: TaxonomySelectOption[] = dataCategories
    .filter((category) => !selectedTaxonomies.includes(category.fides_key))
    .map((category) => {
      const { name, primaryName } = getDataCategoryDisplayNameProps(
        category.fides_key,
      );
      return {
        value: category.fides_key,
        name,
        primaryName,
        description: category.description || "",
      };
    });

  return <TaxonomySelect options={options} {...props} />;
};

export default DataCategorySelect;

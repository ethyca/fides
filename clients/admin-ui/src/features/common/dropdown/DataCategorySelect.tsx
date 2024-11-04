import { OptionProps, Options, Select } from "chakra-react-select";

import TaxonomyDropdownOption, {
  TaxonomySelectOption,
} from "~/features/common/dropdown/TaxonomyDropdownOption";
import { SELECT_STYLES } from "~/features/common/form/inputs";

import useTaxonomies from "../hooks/useTaxonomies";

export const DataCategoryOption = ({
  data,
  setValue,
  ...props
}: OptionProps<TaxonomySelectOption>) => {
  const { getPrimaryKey, getDataCategoryByKey } = useTaxonomies();
  const primaryKey = getPrimaryKey(data.value, 2);
  const primaryCategory = getDataCategoryByKey(primaryKey);
  return (
    <TaxonomyDropdownOption
      data={data}
      setValue={setValue}
      tagValue={primaryCategory?.name || ""}
      {...props}
    />
  );
};

export interface TaxonomySelectDropdownProps {
  onChange: (selectedOption: TaxonomySelectOption) => void;
  menuIsOpen?: boolean;
  showDisabled?: boolean;
}
const DataCategorySelect = ({
  onChange,
  menuIsOpen,
  showDisabled = false,
}: TaxonomySelectDropdownProps) => {
  const { getDataCategoryDisplayName, getDataCategories } = useTaxonomies();

  const getActiveDataCategories = () =>
    getDataCategories().filter((c) => c.active);

  const dataCategories = showDisabled
    ? getDataCategories()
    : getActiveDataCategories();

  const options: Options<TaxonomySelectOption> = dataCategories.map(
    (category) => ({
      value: category.fides_key,
      label: getDataCategoryDisplayName(category.fides_key),
      description: category.description || "",
    }),
  );

  return (
    <Select
      placeholder="Select a category..."
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      autoFocus
      isSearchable
      menuPlacement="auto"
      components={{
        Option: DataCategoryOption,
      }}
      menuIsOpen={menuIsOpen}
      chakraStyles={{
        ...(SELECT_STYLES as Options<TaxonomySelectOption>),
        control: (baseStyles) => ({ ...baseStyles, border: "none" }),
        menuList: (baseStyles) => ({
          ...baseStyles,
          paddingTop: 0,
          paddingBottom: 0,
          mt: 10,
          position: "fixed",
          overflowX: "hidden",
          maxWidth: "lg",
        }),
      }}
    />
  );
};
export default DataCategorySelect;

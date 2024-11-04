import { OptionProps, Options, Select } from "chakra-react-select";

import { TaxonomySelectDropdownProps } from "~/features/common/dropdown/DataCategorySelect";
import TaxonomyDropdownOption, {
  TaxonomySelectOption,
} from "~/features/common/dropdown/TaxonomyDropdownOption";
import { SELECT_STYLES } from "~/features/common/form/inputs";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const DataUseOption = ({
  data,
  setValue,
  ...props
}: OptionProps<TaxonomySelectOption>) => {
  const { getPrimaryKey, getDataUseByKey } = useTaxonomies();
  const primaryKey = getPrimaryKey(data.value, 2);
  const primaryDataUse = getDataUseByKey(primaryKey);
  return (
    <TaxonomyDropdownOption
      data={data}
      setValue={setValue}
      tagValue={primaryDataUse?.name || ""}
      {...props}
    />
  );
};

const DataUseSelect = ({
  onChange,
  menuIsOpen,
  showDisabled = false,
}: TaxonomySelectDropdownProps) => {
  const { getDataUseDisplayName, getDataUses } = useTaxonomies();

  const getActiveDataUses = () => getDataUses().filter((du) => du.active);

  const dataUses = showDisabled ? getDataUses() : getActiveDataUses();

  const options: Options<TaxonomySelectOption> = dataUses.map((dataUse) => ({
    value: dataUse.fides_key,
    label: getDataUseDisplayName(dataUse.fides_key),
    description: dataUse.description || "",
  }));

  return (
    <Select
      placeholder="Select a data use..."
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      autoFocus
      isSearchable
      menuPlacement="auto"
      components={{
        Option: DataUseOption,
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

export default DataUseSelect;

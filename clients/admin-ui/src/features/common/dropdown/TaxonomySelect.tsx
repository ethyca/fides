import {
  AntFlex as Flex,
  AntSelect as Select,
  AntSelectProps as SelectProps,
} from "fidesui";

import useTaxonomies from "../hooks/useTaxonomies";
import styles from "./TaxonomySelect.module.scss";

export interface TaxonomySelectOption {
  value: string;
  name?: string;
  primaryName?: string;
  description: string;
  className?: string;
}

const TaxonomyOption = ({ data }: { data: TaxonomySelectOption }) => {
  return (
    <Flex
      gap={12}
      title={`${data.primaryName || ""}${data.primaryName ? ": " : ""}${data.name} - ${data.description}`}
    >
      <div>
        <strong>{data.primaryName || data.name}</strong>
        {data.primaryName && `: ${data.name}`}
      </div>
      <em>{data.description}</em>
    </Flex>
  );
};

interface TaxonomySelectProps
  extends SelectProps<string, TaxonomySelectOption> {
  selectedTaxonomies: string[];
  showDisabled?: boolean;
}
export const TaxonomySelect = ({
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
        className: styles.option,
      };
    });

  return (
    <Select<string, TaxonomySelectOption>
      autoFocus
      showSearch
      variant="borderless"
      placeholder="Select a category..."
      options={options}
      optionRender={TaxonomyOption}
      dropdownStyle={{ minWidth: "500px" }}
      className="w-full p-0"
      {...props}
    />
  );
};

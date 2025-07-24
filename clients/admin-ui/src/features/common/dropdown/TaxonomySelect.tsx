import {
  AntFlex as Flex,
  AntSelect as Select,
  AntSelectProps as SelectProps,
} from "fidesui";

import styles from "./TaxonomySelect.module.scss";

export interface TaxonomySelectOption {
  value: string;
  name?: string;
  primaryName?: string;
  description: string;
  className?: string;
}

interface ExtendedTaxonomySelectOption extends TaxonomySelectOption {
  // The visual title of the select element
  formattedTitle: string;
}

export const TaxonomyOption = ({
  data: { formattedTitle, description, name, primaryName },
}: {
  data: ExtendedTaxonomySelectOption;
}) => {
  return (
    <Flex gap={12} title={`${formattedTitle} - ${description}`}>
      <div>
        <strong>{primaryName || name}</strong>
        {primaryName && `: ${name}`}
      </div>
      <em>{description}</em>
    </Flex>
  );
};

export interface TaxonomySelectProps
  extends Omit<SelectProps<string, TaxonomySelectOption>, "options"> {
  selectedTaxonomies: string[];
  showDisabled?: boolean;
}

export const TaxonomySelect = ({
  options,
  ...props
}: SelectProps<string, TaxonomySelectOption>) => {
  const selectOptions = options?.map((opt) => ({
    ...opt,
    className: styles.option,
    formattedTitle: [opt.primaryName, opt.name]
      .filter((maybeString) => maybeString)
      .join(": "),
  }));

  /*
   * @description Matches options where the displayed value or the underlying value includes the input text
   */
  const filterOption = (input: string, option?: ExtendedTaxonomySelectOption) =>
    option?.formattedTitle.toLowerCase().includes(input.toLowerCase()) ||
    option?.value.toLowerCase().includes(input.toLowerCase()) ||
    false;

  return (
    <Select<string, ExtendedTaxonomySelectOption>
      options={selectOptions}
      filterOption={filterOption}
      optionFilterProp="label"
      autoFocus
      variant="borderless"
      optionRender={TaxonomyOption}
      dropdownStyle={{ minWidth: "500px" }}
      className="w-full p-0"
      data-testid="taxonomy-select"
      {...props}
    />
  );
};

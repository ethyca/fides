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

export const TaxonomyOption = ({ data }: { data: TaxonomySelectOption }) => {
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
  }));

  return (
    <Select<string, TaxonomySelectOption>
      options={selectOptions}
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

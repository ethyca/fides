import {
  AntFlex as Flex,
  AntSelect as Select,
  ICustomMultiSelectProps,
  ICustomSelectProps,
} from "fidesui";
import { ReactNode } from "react";

import styles from "./TaxonomySelect.module.scss";

export interface TaxonomySelectOption {
  value: string;
  name?: string;
  primaryName?: string;
  description: string;
  className?: string;
  formattedTitle?: string;
}

export interface TaxonomySelectOptionGroup {
  label: ReactNode;
  value?: string;
  options: TaxonomySelectOption[];
}

export type TaxonomySelectOptions = (
  | TaxonomySelectOption
  | TaxonomySelectOptionGroup
)[];

const TaxonomyOption = ({
  data: { formattedTitle, description, name, primaryName },
}: {
  data: TaxonomySelectOption;
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

interface ITaxonomySelectProps
  extends Omit<ICustomSelectProps<string, TaxonomySelectOption>, "options"> {
  options?: TaxonomySelectOptions;
}
interface ITaxonomyMultiSelectProps
  extends Omit<
    ICustomMultiSelectProps<string, TaxonomySelectOption>,
    "options"
  > {
  options?: TaxonomySelectOptions;
}

export type TaxonomySelectProps = (
  | ITaxonomySelectProps
  | ITaxonomyMultiSelectProps
) & {
  showDisabled?: boolean;
  selectedTaxonomies?: string[];
};

// Helper function to check if options are grouped
const isOptionGroup = (
  option: TaxonomySelectOption | TaxonomySelectOptionGroup,
): option is TaxonomySelectOptionGroup => {
  return "options" in option && Array.isArray(option.options);
};

// Helper function to format a single option
const formatTaxonomyOption = (
  opt: TaxonomySelectOption,
): TaxonomySelectOption => ({
  ...opt,
  className: styles.option,
  formattedTitle:
    opt.formattedTitle ||
    [opt.primaryName, opt.name].filter((maybeString) => maybeString).join(": "),
});

export const TaxonomySelect = ({ options, ...props }: TaxonomySelectProps) => {
  const selectOptions: TaxonomySelectOptions | undefined = options?.map(
    (item) => {
      if (isOptionGroup(item)) {
        // Handle option groups
        return {
          ...item,
          options: item.options.map(formatTaxonomyOption),
        };
      }
      // Handle flat options
      return formatTaxonomyOption(item);
    },
  );

  /*
   * @description Matches options where the displayed value or the underlying value includes the input text
   */
  const filterOption = (input: string, option?: TaxonomySelectOption) =>
    option?.formattedTitle?.toLowerCase().includes(input.toLowerCase()) ||
    option?.value.toLowerCase().includes(input.toLowerCase()) ||
    false;

  return (
    <Select<string, TaxonomySelectOption>
      options={selectOptions as never} // Ant seems to want Options and Groups to use the same interface. Since we've added a bunch of fields to the Options that don't make sense for the Group type, it's easiest just to tell Ant to ignore this type for now.
      filterOption={filterOption}
      optionFilterProp="label"
      autoFocus
      variant="borderless"
      optionRender={TaxonomyOption}
      styles={{ popup: { root: { minWidth: "500px" } } }}
      className="w-full p-0"
      data-testid="taxonomy-select"
      {...props}
    />
  );
};

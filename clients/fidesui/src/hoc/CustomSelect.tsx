import { Checkmark, ChevronDown } from "@carbon/icons-react";
import { Flex, Select, SelectProps, Typography } from "antd/lib";
import { BaseOptionType, DefaultOptionType } from "antd/lib/select";
import React from "react";

const optionDescriptionRender = (
  option: DefaultOptionType | BaseOptionType,
) => {
  const { label, description } = option.data;
  if (!description) {
    return option.label;
  }
  return (
    <Flex vertical className="p-1 leading-tight">
      <Typography.Text strong>{label}</Typography.Text>
      {!!description && (
        <Typography.Text
          type="secondary"
          className="text-wrap text-sm leading-tight"
        >
          {description}
        </Typography.Text>
      )}
    </Flex>
  );
};

export interface ICustomSelectProps<
  SelectValue,
  OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
> extends SelectProps<SelectValue, OptionType> {
  mode?: undefined;
  defaultValue?: SelectValue | null;
}

export interface ICustomMultiSelectProps<
  SelectValue,
  OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
> extends SelectProps<SelectValue[], OptionType> {
  mode: "tags" | "multiple";
  defaultValue?: SelectValue[] | null;
}

/**
 * @description using discriminated unions to explicitly handle single vs multi select values
 */
export type CustomSelectProps<
  SelectValue,
  OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
> =
  | ICustomMultiSelectProps<SelectValue, OptionType>
  | ICustomSelectProps<SelectValue, OptionType>;

const withCustomProps = (WrappedComponent: typeof Select) => {
  const WrappedSelect = <
    SelectValue,
    OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
  >(
    props: CustomSelectProps<SelectValue, OptionType>,
  ) => {
    const { loading, suffixIcon, id } = props;
    const customProps = {
      placeholder: "Select...",
      optionRender: optionDescriptionRender,
      showSearch: true,
      menuItemSelectedIcon: <Checkmark />,
      className: "w-full",
      suffixIcon: loading ? undefined : suffixIcon || <ChevronDown />,
      "data-testid": `select${id ? `-${id}` : ""}`,
      ...props,
    };

    return customProps.mode ? (
      <WrappedComponent {...customProps} /> /* multi-select props */
    ) : (
      <WrappedComponent {...customProps} />
    ); /* mono-select props */
  };
  return WrappedSelect;
};

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Select component.
 * Provides default props for common use cases and improves accessibility with consistent test IDs.
 *
 * Default customizations:
 * - Renders option descriptions in a structured layout when present
 * - Full width styling
 * - Search enabled by default
 * - Custom icons for dropdown and loading
 * - Consistent placeholder text
 * - Consistent test IDs
 *
 * @example
 * ```tsx
 * // Basic usage
 * <CustomSelect options={[
 *   { value: '1', label: 'Option 1', description: 'Description text' }
 * ]} />
 *
 * // With custom ID for testing
 * <CustomSelect id="my-select" options={options} />
 *
 * // Override defaults
 * <CustomSelect
 *   showSearch={false}
 *   className="w-48"
 *   placeholder="Choose an option..."
 * />
 * ```
 */

export const CustomSelect = withCustomProps(Select);

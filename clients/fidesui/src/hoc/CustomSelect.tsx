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

const withCustomProps = (WrappedComponent: typeof Select) => {
  const WrappedSelect = <
    ValueType = any,
    OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
  >({
    placeholder = "Select...",
    optionRender = optionDescriptionRender,
    className = "w-full",
    showSearch = true,
    suffixIcon,
    menuItemSelectedIcon = <Checkmark />,
    ...props
  }: SelectProps<ValueType, OptionType>) => {
    const customProps = {
      placeholder,
      optionRender,
      className,
      showSearch,
      suffixIcon: props.loading ? undefined : suffixIcon || <ChevronDown />,
      menuItemSelectedIcon,
      "data-testid": `select${props.id ? `-${props.id}` : ""}`,
      ...props,
    };
    return <WrappedComponent {...customProps} />;
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

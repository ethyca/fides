import { ChevronDown } from "@carbon/icons-react";
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

/**
 * Higher-order component that adds a custom arrow icon to the Select component.
 */
const withCustomProps = (WrappedComponent: typeof Select) => {
  const WrappedSelect = <
    ValueType = any,
    OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
  >({
    placeholder = "Select...",
    optionRender = optionDescriptionRender,
    className = "w-full",
    suffixIcon = <ChevronDown />,
    ...props
  }: SelectProps<ValueType, OptionType>) => {
    const customProps = {
      placeholder,
      optionRender,
      className,
      suffixIcon,
      ...props,
    };
    return <WrappedComponent {...customProps} />;
  };
  return WrappedSelect;
};

export const CustomSelect = withCustomProps(Select);

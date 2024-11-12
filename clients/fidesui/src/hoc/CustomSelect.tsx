import { ChevronDown } from "@carbon/icons-react";
import type { SelectProps } from "antd/lib";
import { Select } from "antd/lib";
import { BaseOptionType, DefaultOptionType } from "antd/lib/select";
import React from "react";

/**
 * Higher-order component that adds a custom arrow icon to the Select component.
 */
const withCustomArrowIcon = (WrappedComponent: typeof Select) => {
  return function SpecifyCustomIcon<
    ValueType = any,
    OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
  >(props: SelectProps<ValueType, OptionType>) {
    return <WrappedComponent suffixIcon={<ChevronDown />} {...props} />;
  };
};

export const CustomSelect = withCustomArrowIcon(Select);

import { ArrowRight, Calendar } from "@carbon/icons-react";
import { RangePickerProps } from "antd/es/date-picker";
import { DatePicker } from "antd/lib";
import React from "react";

const withCustomProps = (WrappedComponent: typeof DatePicker.RangePicker) => {
  const WrappedSelect = ({
    suffixIcon = <Calendar />,
    separator = (
      <ArrowRight style={{ color: "var(--ant-color-text-disabled)" }} />
    ),
    ...props
  }: RangePickerProps) => {
    const customProps = {
      suffixIcon,
      separator,
      ...props,
    };
    return <WrappedComponent {...customProps} />;
  };
  return WrappedSelect;
};
/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's RangePicker component.
 *
 * Default customizations:
 * - Uses Carbon icons for suffix (calendar icon) and separator (right arrow)
 * - Uses the same gray color for the right arrow icon
 *
 */
export const CustomDateRangePicker = withCustomProps(DatePicker.RangePicker);

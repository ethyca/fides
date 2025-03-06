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

export const CustomDateRangePicker = withCustomProps(DatePicker.RangePicker);

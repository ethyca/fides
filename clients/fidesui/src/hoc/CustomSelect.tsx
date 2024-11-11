import { ChevronDown } from "@carbon/icons-react";
import { Select } from "antd/lib";
import { SelectProps } from "antd/lib/select";
import React from "react";

/**
 * Higher-order component that adds a custom arrow icon to the Select component.
 */
export const withCustomArrowIcon = <P extends SelectProps>(
  WrappedComponent: React.ComponentType<P>
) => {
  return function SpecifyCustomIcon(props: P) {
    const customProps = {
      ...props,
      suffixIcon: <ChevronDown />,
    };

    return <WrappedComponent {...customProps} />;
  };
};

export const CustomSelect = withCustomArrowIcon(Select);

import { Menu } from "antd";

/**
 * Higher-order component that adds data-testid to the menu component
 */
const withCustomProps = (WrappedComponent: typeof Select) => {
  const WrappedSelect = <
    ValueType = any,
    OptionType extends DefaultOptionType | BaseOptionType = DefaultOptionType,
  >(
    props: SelectProps<ValueType, OptionType>,
  ) => {
    const customProps = {
      "data-testid": `select${props.id ? `-${props.id}` : ""}`,
      ...props,
    };
    return <WrappedComponent {...customProps} />;
  };
  return WrappedSelect;
};

export const CustomMenu = withCustomProps(Menu);

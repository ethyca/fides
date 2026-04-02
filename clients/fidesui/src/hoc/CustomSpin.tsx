import { Flex, Spin, SpinProps } from "antd/lib";

export interface CustomSpinProps extends SpinProps {
  centered?: boolean;
  wrapperClassName?: string;
}

const withCustomProps = (WrappedComponent: typeof Spin) => {
  const CustomSpinComponent = ({
    centered = true,
    wrapperClassName,
    ...props
  }: CustomSpinProps) => {
    if (!centered) {
      return <WrappedComponent {...props} />;
    }
    return (
      <Flex
        className={`size-full${wrapperClassName ? ` ${wrapperClassName}` : ""}`}
        align="center"
        justify="center"
      >
        <WrappedComponent {...props} />
      </Flex>
    );
  };
  CustomSpinComponent.displayName = "CustomSpin";
  return CustomSpinComponent;
};

export const CustomSpin = withCustomProps(Spin);

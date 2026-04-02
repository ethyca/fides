import { Flex, Spin, SpinProps } from "antd/lib";

export interface CustomSpinProps extends SpinProps {
  centered?: boolean;
}

const withCustomProps = (WrappedComponent: typeof Spin) => {
  const CustomSpinComponent = ({
    centered = true,
    ...props
  }: CustomSpinProps) => {
    if (!centered) return <WrappedComponent {...props} />;
    return (
      <Flex className="size-full" align="center" justify="center">
        <WrappedComponent {...props} />
      </Flex>
    );
  };
  return CustomSpinComponent;
};

export const CustomSpin = withCustomProps(Spin);

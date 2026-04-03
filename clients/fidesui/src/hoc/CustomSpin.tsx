import { Flex, Spin, SpinProps } from "antd/lib";
import classNames from "classnames";

export interface CustomSpinProps extends SpinProps {
  centered?: boolean;
  rootClassName?: string;
}

const withCustomProps = (WrappedComponent: typeof Spin) => {
  const CustomSpinComponent = ({
    centered = true,
    rootClassName,
    ...props
  }: CustomSpinProps) => {
    const containerClassNames = [
      "size-full",
      "items-center",
      "justify-center",
      rootClassName,
    ];
    if (!centered) {
      containerClassNames.push("contents");
    }
    return (
      <Flex
        className={classNames(containerClassNames)}
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

/**
 * A wrapper around Ant Design's `Spin` that centers the spinner in its
 * container by default. Pass `centered={false}` to render inline without a
 * wrapping flex container. Use `rootClassName` to apply additional classes to
 * the outer wrapper.
 */
export const CustomSpin = withCustomProps(Spin);

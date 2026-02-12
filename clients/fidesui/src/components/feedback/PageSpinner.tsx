import type { SpinProps } from "antd";
import { Flex, Spin } from "fidesui";

interface PageSpinnerProps extends SpinProps {
  alignment?: "center" | "start" | "end";
}

export const PageSpinner = ({
  alignment = "center",
  size = "large",
  ...props
}: PageSpinnerProps) => (
  <Flex className="size-full" align="center" justify={alignment}>
    <Spin size={size} {...props} />
  </Flex>
);

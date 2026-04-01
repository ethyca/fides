import type { SpinProps } from "antd";
import { Flex, Spin } from "antd/lib";

interface CenteredSpinnerProps extends SpinProps {
  alignment?: "center" | "start" | "end";
}

export const CenteredSpinner = ({
  alignment = "center",
  size = "large",
  ...props
}: CenteredSpinnerProps) => (
  <Flex className="size-full" align="center" justify={alignment}>
    <Spin size={size} {...props} />
  </Flex>
);

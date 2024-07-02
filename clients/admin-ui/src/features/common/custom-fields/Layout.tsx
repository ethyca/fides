import { StackProps, VStack } from "fidesui";
import * as React from "react";

const Layout = ({ children, ...props }: StackProps) => (
  <VStack
    alignItems="stretch"
    flexShrink={0}
    gap="18px"
    overflow="auto"
    {...props}
  >
    {children}
  </VStack>
);

export { Layout };

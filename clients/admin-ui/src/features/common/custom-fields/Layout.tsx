import { VStack } from "@fidesui/react";
import * as React from "react";
import { ReactNode } from "react";

type LayoutProps = {
  children: ReactNode;
};

const Layout: React.FC<LayoutProps> = ({ children }) => (
  <VStack
    alignItems="stretch"
    flexShrink={0}
    gap="18px"
    h="434px"
    overflow="auto"
  >
    {children}
  </VStack>
);

export { Layout };

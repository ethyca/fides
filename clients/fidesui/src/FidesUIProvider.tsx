import {
  ChakraProvider as BaseChakraProvider,
  ChakraProviderProps,
} from "@chakra-ui/react";
import { ConfigProvider as BaseAntDesignProvider, ThemeConfig } from "antd/lib";
import { ReactNode } from "react";

import { theme as defaultTheme } from "./FidesUITheme";

export interface FidesUIProviderProps {
  children: ReactNode;
  antTheme?: ThemeConfig;
  theme?: ChakraProviderProps["theme"];
}
export const FidesUIProvider = ({
  children,
  theme = defaultTheme,
  antTheme,
}: FidesUIProviderProps) => (
  <BaseAntDesignProvider theme={antTheme}>
    <BaseChakraProvider theme={theme}>{children}</BaseChakraProvider>
  </BaseAntDesignProvider>
);

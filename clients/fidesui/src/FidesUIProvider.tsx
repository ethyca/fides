import {
  ChakraProvider as BaseChakraProvider,
  ChakraProviderProps,
} from "@chakra-ui/provider";
import { theme as defaultTheme } from "./FidesUITheme";

export const FidesUIProvider = ({
  children,
  theme = defaultTheme,
}: ChakraProviderProps) => (
  <BaseChakraProvider theme={theme}>{children}</BaseChakraProvider>
);

export type { ChakraProviderProps as FidesProviderProps } from "@chakra-ui/provider";

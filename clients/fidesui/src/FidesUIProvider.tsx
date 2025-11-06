import {
  ChakraProvider as BaseChakraProvider,
  ChakraProviderProps,
} from "@chakra-ui/react";
import {
  ConfigProvider as BaseAntDesignProvider,
  message,
  ThemeConfig,
} from "antd/lib";
import { createContext, ReactNode, useContext, useMemo } from "react";

import { defaultAntTheme } from "./ant-theme";
import { theme as defaultTheme } from "./FidesUITheme";

interface ComponentAPIExports {
  messageApi: ReturnType<typeof message.useMessage>[0];
}

const MessageContext = createContext<ComponentAPIExports | undefined>(
  undefined,
);

export interface FidesUIProviderProps {
  children: ReactNode;
  antTheme?: ThemeConfig;
  theme?: ChakraProviderProps["theme"];
  wave?: { disabled?: boolean };
}
export const FidesUIProvider = ({
  children,
  theme = defaultTheme,
  antTheme = defaultAntTheme, // Use default theme if none provided
  wave,
}: FidesUIProviderProps) => {
  const [messageApi, messageContextHolder] = message.useMessage();
  const value = useMemo(() => ({ messageApi }), [messageApi]);

  return (
    <BaseAntDesignProvider theme={antTheme} wave={wave}>
      <BaseChakraProvider theme={theme}>
        <MessageContext.Provider value={value}>
          {messageContextHolder}
          {children}
        </MessageContext.Provider>
      </BaseChakraProvider>
    </BaseAntDesignProvider>
  );
};

export const useMessage = () => {
  const context = useContext(MessageContext);
  if (!context) {
    throw new Error("useMessage must be used within a FidesUIProvider");
  }
  return context.messageApi;
};

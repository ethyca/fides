import {
  ChakraProvider as BaseChakraProvider,
  ChakraProviderProps,
} from "@chakra-ui/react";
import {
  ConfigProvider as BaseAntDesignProvider,
  message,
  Modal,
  ThemeConfig,
} from "antd/lib";
import { createContext, ReactNode, useContext, useMemo } from "react";

import { defaultAntTheme } from "./ant-theme";
import { theme as defaultTheme } from "./FidesUITheme";

interface ComponentAPIExports {
  messageApi: ReturnType<typeof message.useMessage>[0];
  modalApi: ReturnType<typeof Modal.useModal>[0];
}

const AntComponentAPIsContext = createContext<ComponentAPIExports | undefined>(
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
  const [modalApi, modalContextHolder] = Modal.useModal();
  const value = useMemo(
    () => ({ messageApi, modalApi }),
    [messageApi, modalApi],
  );

  return (
    <BaseAntDesignProvider theme={antTheme} wave={wave}>
      <BaseChakraProvider theme={theme}>
        <AntComponentAPIsContext.Provider value={value}>
          {messageContextHolder}
          {modalContextHolder}
          {children}
        </AntComponentAPIsContext.Provider>
      </BaseChakraProvider>
    </BaseAntDesignProvider>
  );
};

export const useMessage = () => {
  const context = useContext(AntComponentAPIsContext);
  if (!context) {
    throw new Error("useMessage must be used within a FidesUIProvider");
  }
  return context.messageApi;
};

export const useModal = () => {
  const context = useContext(AntComponentAPIsContext);
  if (!context) {
    throw new Error("useModal must be used within a FidesUIProvider");
  }
  return context.modalApi;
};

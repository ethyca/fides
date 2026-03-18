import {
  ChakraProvider as BaseChakraProvider,
  ChakraProviderProps,
} from "@chakra-ui/react";
import {
  ConfigProvider as BaseAntDesignProvider,
  message,
  Modal,
  notification,
  ThemeConfig,
} from "antd/lib";
import type {
  ArgsProps as MessageArgsProps,
  TypeOpen as MessageTypeOpen,
} from "antd/lib/message/interface";
import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
} from "react";

import { defaultAntTheme } from "./ant-theme";
import { theme as defaultTheme } from "./FidesUITheme";
import {
  type FeedbackType,
  getDefaultMessageIcon,
  getDefaultModalIcon,
  getDefaultNotificationIcon,
} from "./lib/carbon-icon-defaults";
import { setGlobalMessageApi } from "./lib/globalMessageApi";

const isMessageArgsProps = (content: unknown): content is MessageArgsProps =>
  typeof content === "object" && content !== null && "content" in content;

/**
 * Wraps an Ant message method to inject a default Carbon icon.
 *
 * Supports both calling conventions:
 *   message.success("Saved!")                           - simple content
 *   message.success({ content: "Saved!", duration: 5 }) - with options
 *
 * Prefer the simple string form for basic feedback. Use the config
 * object form when you need to set duration, onClose, or override the icon.
 */
const wrapMessageMethod = (
  method: MessageTypeOpen,
  type: FeedbackType,
): MessageTypeOpen => {
  const defaultIcon = getDefaultMessageIcon(type);
  return (content, duration?, onClose?) => {
    if (isMessageArgsProps(content)) {
      // ArgsProps form - inject icon as default, caller can override
      return method({ icon: defaultIcon, ...content });
    }
    // JointContent (string/ReactNode) - convert to ArgsProps to inject icon
    const args: MessageArgsProps = { content, icon: defaultIcon };
    if (typeof duration === "number") {
      args.duration = duration;
    } else if (typeof duration === "function") {
      args.onClose = duration;
    }
    if (onClose) {
      args.onClose = onClose;
    }
    return method(args);
  };
};

interface ComponentAPIExports {
  messageApi: ReturnType<typeof message.useMessage>[0];
  modalApi: ReturnType<typeof Modal.useModal>[0];
  notificationApi: ReturnType<typeof notification.useNotification>[0];
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
  const [notificationApi, notificationContextHolder] =
    notification.useNotification();
  const wrappedModalApi = useMemo(
    () => ({
      info: (props: Parameters<typeof modalApi.info>[0]) =>
        modalApi.info({ icon: getDefaultModalIcon("info"), ...props }),
      success: (props: Parameters<typeof modalApi.success>[0]) =>
        modalApi.success({ icon: getDefaultModalIcon("success"), ...props }),
      error: (props: Parameters<typeof modalApi.error>[0]) =>
        modalApi.error({ icon: getDefaultModalIcon("error"), ...props }),
      warning: (props: Parameters<typeof modalApi.warning>[0]) =>
        modalApi.warning({ icon: getDefaultModalIcon("warning"), ...props }),
      confirm: (props: Parameters<typeof modalApi.confirm>[0]) =>
        modalApi.confirm({ icon: getDefaultModalIcon("confirm"), ...props }),
    }),
    [modalApi],
  );

  const wrappedMessageApi = useMemo(
    () => ({
      ...messageApi,
      // open, destroy, and loading are inherited unchanged from messageApi.
      // open does not inject Carbon icons; use info/success/error/warning instead.
      // loading keeps Ant's default spinner.
      info: wrapMessageMethod(messageApi.info, "info"),
      success: wrapMessageMethod(messageApi.success, "success"),
      error: wrapMessageMethod(messageApi.error, "error"),
      warning: wrapMessageMethod(messageApi.warning, "warning"),
    }),
    [messageApi],
  );

  const wrappedNotificationApi = useMemo(
    () => ({
      ...notificationApi,
      info: (props: Parameters<typeof notificationApi.info>[0]) =>
        notificationApi.info({
          icon: getDefaultNotificationIcon("info"),
          ...props,
        }),
      success: (props: Parameters<typeof notificationApi.success>[0]) =>
        notificationApi.success({
          icon: getDefaultNotificationIcon("success"),
          ...props,
        }),
      error: (props: Parameters<typeof notificationApi.error>[0]) =>
        notificationApi.error({
          icon: getDefaultNotificationIcon("error"),
          ...props,
        }),
      warning: (props: Parameters<typeof notificationApi.warning>[0]) =>
        notificationApi.warning({
          icon: getDefaultNotificationIcon("warning"),
          ...props,
        }),
    }),
    [notificationApi],
  );

  useEffect(() => {
    setGlobalMessageApi(wrappedMessageApi);
    return () => {
      setGlobalMessageApi(null);
    };
  }, [wrappedMessageApi]);

  const value = useMemo(
    () => ({
      messageApi: wrappedMessageApi,
      modalApi: wrappedModalApi,
      notificationApi: wrappedNotificationApi,
    }),
    [wrappedMessageApi, wrappedModalApi, wrappedNotificationApi],
  );

  return (
    <BaseAntDesignProvider theme={antTheme} wave={wave}>
      <BaseChakraProvider theme={theme}>
        <AntComponentAPIsContext.Provider value={value}>
          {messageContextHolder}
          {modalContextHolder}
          {notificationContextHolder}
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

export const useNotification = () => {
  const context = useContext(AntComponentAPIsContext);
  if (!context) {
    throw new Error("useNotification must be used within a FidesUIProvider");
  }
  return context.notificationApi;
};

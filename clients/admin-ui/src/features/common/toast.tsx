import { Text, UseToastOptions } from "@fidesui/react";
import { ReactNode } from "react";

const SuccessMessage = ({ children }: { children: ReactNode }) => (
  <Text data-testid="toast-success-msg">
    <strong>Success:</strong> {children}
  </Text>
);

const ErrorMessage = ({ children }: { children: ReactNode }) => (
  <Text data-testid="toast-error-msg">
    <strong>Error:</strong> {children}
  </Text>
);

export const DEFAULT_TOAST_PARAMS: UseToastOptions = {
  variant: "subtle",
  position: "top",
  description: "",
  duration: 5000,
  status: "success",
  isClosable: true,
};

export const successToastParams = (message: ReactNode): UseToastOptions => {
  const description = <SuccessMessage>{message}</SuccessMessage>;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description } };
};

export const errorToastParams = (message: ReactNode): UseToastOptions => {
  const description = <ErrorMessage>{message}</ErrorMessage>;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description, status: "error" } };
};

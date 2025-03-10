import { Text, UseToastOptions } from "fidesui";
import { ReactNode } from "react";

const SuccessMessage = ({
  children,
  title = "Success",
}: {
  children: ReactNode;
  title?: string;
}) => (
  <Text data-testid="toast-success-msg">
    <strong>{title}:</strong> {children}
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

export const successToastParams = (
  message: ReactNode,
  title?: string,
): UseToastOptions => {
  const description = <SuccessMessage title={title}>{message}</SuccessMessage>;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description } };
};

export const errorToastParams = (message: ReactNode): UseToastOptions => {
  const description = <ErrorMessage>{message}</ErrorMessage>;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description, status: "error" } };
};

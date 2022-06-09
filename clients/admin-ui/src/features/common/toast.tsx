import { Text, UseToastOptions } from "@fidesui/react";

const SuccessMessage = ({ message }: { message: string }) => (
  <Text>
    <strong>Success:</strong> {message}
  </Text>
);

const ErrorMessage = ({ message }: { message: string }) => (
  <Text>
    <strong>Error:</strong> {message}
  </Text>
);

const DEFAULT_TOAST_PARAMS: UseToastOptions = {
  variant: "subtle",
  position: "top",
  description: "",
  duration: 5000,
  status: "success",
  isClosable: true,
};

export const successToastParams = (message: string): UseToastOptions => {
  const description = <SuccessMessage message={message} />;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description } };
};

export const errorToastParams = (message: string): UseToastOptions => {
  const description = <ErrorMessage message={message} />;
  return { ...DEFAULT_TOAST_PARAMS, ...{ description, status: "error" } };
};
